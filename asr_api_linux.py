from fastapi import FastAPI, File, UploadFile, Form
import torch
from funasr import AutoModel
import os
import uuid
import traceback
import asyncio
from threading import Lock
import gc
import ctypes

app = FastAPI(title="ASR Model Service on Linux (Memory Optimized)")

# ==============================
# Linux memory management utilities
# ==============================
def force_release_memory():
    """强制将内存归还给操作系统"""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    
    # 在 Linux 系统下，通过 libc 强制执行 malloc_trim
    # 这是释放 CPU 内存的关键
    try:
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
        print("🧹 Memory trimmed via malloc_trim")
    except Exception as e:
        print(f"⚠️ malloc_trim not available: {e}")


device = "cuda" if torch.cuda.is_available() else "cpu"
models = {}  # 模型缓存
model_lock = Lock()

SUPPORTED_MODELS = {
    "funasr": "FunAudioLLM/Fun-ASR-Nano-2512",
    "sensevoice": "iic/SenseVoiceSmall",
    "paraformer": "paraformer-zh",
    "qwenaudio": "Qwen-Audio",
    "whisperturbo": "iic/whisper-large-v3-turbo",
    "whisper": "iic/whisper-large-v3"
}

# ==============================
# model unloading utilities
# ==============================

def unload_all_models():
    print("🔴 Unloading ALL models")
    global models
    # delete dicts
    model_names = list(models.keys())
    for name in model_names:
        model = models.pop(name)
        del model
    
    force_release_memory()
    print("🟢 All models unloaded and RAM released")

def unload_specific_model(model_name: str):
    model_name = model_name.lower()
    if model_name in models:
        print(f"🔴 Unloading model: {model_name}")
        model = models.pop(model_name)
        del model
        force_release_memory()
        return True
    return False

# ==============================
# load model utility (with locking)
# ==============================

def get_model(model_name: str):
    model_name = model_name.lower()
    if model_name not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_name}")

    if model_name in models:
        return models[model_name]

    with model_lock:
        # if the memory is too tight, we can choose to unload all other models before loading a new one
        # unload_all_models() 

        print(f"🔵 Loading model: {model_name} onto {device}...")
        try:
            model = AutoModel(
                model=SUPPORTED_MODELS[model_name],
                device=device,
                disable_update=True
            )
            models[model_name] = model
            print(f"🟢 Model loaded: {model_name}")
            return model
        except Exception as e:
            print(f"❌ Failed to load model: {str(e)}")
            raise e

# ==============================
# api endpoints
# ==============================

@app.get("/")
def health_check():
    return {"status": "running", "device": device, "loaded_models": list(models.keys())}

@app.post("/transcribe/")
async def transcribe_audio(
    file: UploadFile = File(...),
    model: str = Form("sensevoice")
):
    temp_filename = f"temp_{uuid.uuid4().hex}.wav"
    
    try:
        model_instance = get_model(model)

        
        file_bytes = await file.read()
        with open(temp_filename, "wb") as f:
            f.write(file_bytes)
        del file_bytes # 显式删除大字节数组引用
        
        loop = asyncio.get_event_loop()

        
        common_args = {
            "input": temp_filename,
            "use_vad": True,
            "language": "auto",
            "use_itn": True,
        }

        if model.lower() in ["whisper", "whisperturbo"]:
            inference_args = {**common_args, "batch_size_s": 60}
        else:
            inference_args = {**common_args, "cache": {}, "batch_size_s": 0}

        print(f"🚀 Starting inference with {model}...")
        result = await loop.run_in_executor(
            None, 
            lambda: model_instance.generate(**inference_args)
        )

        
        transcription = result[0] if result else ""

        return {
            "model": model,
            "transcription": transcription
        }

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        gc.collect()

@app.post("/unload/")
def unload(model_name: str = Form(None)):
    """支持卸载全部或指定模型"""
    if model_name:
        success = unload_specific_model(model_name)
        msg = f"Model {model_name} released" if success else "Model not found"
    else:
        unload_all_models()
        msg = "All models released"
    
    return {"message": msg, "loaded_models": list(models.keys())}

# if __name__ == "__main__":
    # import uvicorn
    # 使用 uvicorn 运行: python asr_api.py
    # uvicorn.run(app, host="0.0.0.0", port=8000)