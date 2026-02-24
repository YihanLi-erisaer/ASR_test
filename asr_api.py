from fastapi import FastAPI, File, UploadFile, Form
import torch
from funasr import AutoModel
import os
import uuid
import traceback
import asyncio
from threading import Lock
import gc

app = FastAPI(title="ASR Model Service")

# ==============================
# 全局变量
# ==============================

device = "cuda" if torch.cuda.is_available() else "cpu"
models = {}  # 模型缓存
model_lock = Lock()  # 防止并发重复加载

# ==============================
# 支持的模型
# ==============================

SUPPORTED_MODELS = {
    "funasr": "FunAudioLLM/Fun-ASR-Nano-2512",
    "sensevoice": "iic/SenseVoiceSmall",
    "paraformer": "paraformer-zh",
    "qwenaudio": "Qwen-Audio",
    "whisperturbo": "iic/whisper-large-v3-turbo",
    "whisper": "iic/whisper-large-v3"
}

#unload all models
def unload_all_models():
    print("🔴 Unloading ALL models")

    models.clear()
    gc.collect()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print("🟢 All models unloaded")

# unload specific model
def unload_model(model_name: str):
    model_name = model_name.lower()

    if model_name in models:
        print(f"🔴 Unloading model: {model_name}")

        del models[model_name]
        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        print(f"🟢 Model unloaded: {model_name}")
        return True

    return False


# ==============================
# 懒加载模型（线程安全）
# ==============================

def get_model(model_name: str):
    model_name = model_name.lower()

    if model_name not in SUPPORTED_MODELS:
        raise ValueError(
            f"Unsupported model. Available models: {list(SUPPORTED_MODELS.keys())}"
        )

    # 已加载直接返回
    if model_name in models:
        return models[model_name]

    # 防止多个请求同时加载同一个模型
    with model_lock:
        # unload_all_models()

        print(f"🔵 Loading model: {model_name} ...")

        model = AutoModel(
            model=SUPPORTED_MODELS[model_name],
            device=device,
            disable_update=True
        )

        models[model_name] = model


        print(f"🟢 Model loaded: {model_name}")
        return model

# ==============================
# 健康检查
# ==============================

@app.get("/")
def health_check():
    return {
        "status": "running",
        "device": device,
        "loaded_models": list(models.keys())
    }

# ==============================
# 查看支持模型
# ==============================

@app.get("/models/")
def list_models():
    return {
        "supported_models": list(SUPPORTED_MODELS.keys()),
        "loaded_models": list(models.keys())
    }

# ==============================
# 语音识别接口（核心）
# ==============================

@app.post("/transcribe/")
async def transcribe_audio(
    file: UploadFile = File(...),
    model: str = Form("sensevoice")
):
    temp_filename = None

    try:
        # 获取模型（懒加载）
        model_instance = get_model(model)

        # 生成唯一文件名
        temp_filename = f"temp_{uuid.uuid4().hex}.wav"

        # 保存上传文件
        file_bytes = await file.read()
        with open(temp_filename, "wb") as f:
            f.write(file_bytes)

        loop = asyncio.get_event_loop()

        # ==============================
        # 推理放线程池（防阻塞关键）
        # ==============================

        if model.lower() in ["whisper", "whisperturbo"]:
            print("Using VAD for Whisper models.")

            result = await loop.run_in_executor(
                None,
                lambda: model_instance.generate(
                    input=temp_filename,
                    use_vad=True,
                    language="auto",
                    batch_size_s=60,
                    use_itn=True,
                )
            )
        else:
            print("Not using VAD for this model.")

            result = await loop.run_in_executor(
                None,
                lambda: model_instance.generate(
                    input=temp_filename,
                    use_vad=True,
                    language="auto",
                    cache={},
                    batch_size_s=0,
                    use_itn=True,
                )
            )

        transcription = result[0] #["text"]

        return {
            "model": model,
            "device": device,
            "transcription": transcription
        }

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

    finally:
        gc.collect()
        if temp_filename and os.path.exists(temp_filename):
            os.remove(temp_filename)

@app.post("/unload_all/")
def unload_all():
    unload_all_models()
    gc.collect()
    return {
        "message": "All models released",
        "loaded_models": list(models.keys())
    }