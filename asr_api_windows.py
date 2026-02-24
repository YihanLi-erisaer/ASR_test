import os
import uuid
import traceback
import gc
import ctypes
import multiprocessing
from fastapi import FastAPI, File, UploadFile, Form
import torch
from funasr import AutoModel
import re

app = FastAPI(title="ASR on Windows with complete process isolation")

SUPPORTED_MODELS = {
    "funasr": "FunAudioLLM/Fun-ASR-Nano-2512",
    "sensevoice": "iic/SenseVoiceSmall",
    "paraformer": "paraformer-zh",
    "qwenaudio": "Qwen-Audio",
    "whisperturbo": "iic/whisper-large-v3-turbo",
    "whisper": "iic/whisper-large-v3"
}

# ==============================
# 核心：在独立进程中运行推理
# ==============================
def inference_worker(model_key, audio_path, return_dict):
    """
    这个函数会在一个全新的子进程中运行。
    运行结束后，该进程占用的所有内存/显存会被 Windows 强制回收。
    """
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🧬 Subprocess: Loading {model_key} on {device}...")
        
        # 1. 加载模型
        model = AutoModel(
            model=SUPPORTED_MODELS[model_key],
            device=device,
            disable_update=True
        )

        # 2. 准备推理参数
        is_whisper = model_key.lower() in ["whisper", "whisperturbo"]
        batch_size = 60 if is_whisper else 0
        
        # 3. 执行推理
        result = model.generate(
            input=audio_path,
            use_vad=True,
            language="auto",
            batch_size_s=batch_size,
            use_itn=True,
        )
        
        # 4. 传回结果
        if result and isinstance(result, list) and len(result) > 0:
            first_item = result[0]
            if isinstance(first_item, dict) and "text" in first_item:
                raw_text = first_item["text"]
                
                # --- 新增：使用正则去除 <|...|> 格式的标签 ---
                # 这个正则会匹配所有以 <| 开头，以 |> 结尾的内容并将其替换为空
                clean_text = re.sub(r"<\|.*?\|>", "", raw_text)
                
                return_dict["result"] = clean_text.strip() # .strip() 去掉首尾多余空格
            else:
                return_dict["result"] = str(first_item)
        else:
            return_dict["result"] = ""
        print(f"🧬 Subprocess: Inference complete.")

    except Exception as e:
        return_dict["error"] = str(e)
        traceback.print_exc()
    finally:
        # 清理显存（尽量文明退出）
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

# ==============================
# 接口
# ==============================

@app.post("/transcribe/")
async def transcribe_audio(
    file: UploadFile = File(...),
    model: str = Form("sensevoice")
):
    if model not in SUPPORTED_MODELS:
        return {"error": "Unsupported model"}

    temp_filename = f"temp_{uuid.uuid4().hex}.wav"
    
    try:
        # 1. 保存音频
        content = await file.read()
        with open(temp_filename, "wb") as f:
            f.write(content)
        del content

        # 2. 使用 multiprocessing 启动子进程
        # 这是 Windows 释放内存的终极武器：完事后 Process 就没了，资源必释放
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        
        p = multiprocessing.Process(
            target=inference_worker, 
            args=(model, temp_filename, return_dict)
        )
        p.start()
        p.join()  # 等待子进程结束

        # 3. 检查结果
        if "error" in return_dict:
            return {"error": return_dict["error"]}
        
        return {
            "model": model,
            "transcription": return_dict.get("result", "")
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        # 强制主进程回收一下管理器的碎片
        gc.collect()
        # 强制 Windows 清理工作集
        try:
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.kernel32.SetProcessWorkingSetSize(handle, -1, -1)
        except:
            pass

@app.get("/")
def health_check():
    return {"status": "Process Isolation Mode"}

 # if __name__ == "__main__":
    # import uvicorn
    # Windows 下使用 multiprocessing 必须在 if __name__ == "__main__" 下
    # 并且建议设置启动方法
    # vmultiprocessing.set_start_method('spawn', force=True)
    # uvicorn.run(app, host="0.0.0.0", port=8000)