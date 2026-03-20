# ASR_test

A **Python-based Automatic Speech Recognition (ASR) demo project** that provides both a server API and a simple UI interface.
It allows you to quickly deploy a local speech recognition service and test it through a front-end interface.
Ideal for learning ASR API usage, deployment, and integration.

---

## 🚀 Features

* 🎙️ **ASR API Server**
  Provides a FastAPI-based REST interface for speech-to-text inference.

* 🧑‍💻 **Cross-platform support**
  Includes startup scripts for both Linux and Windows environments.

* 🖼️ **Simple UI Demo**
  Uses Gradio for a lightweight web interface, making testing and debugging easy.

* 📡 **Integration-ready**
  Can be connected to front-end applications or automated workflows to convert audio files to text.

---

## 📂 Project Structure

```text
.
├── asr_api_linux.py        # ASR API server for Linux
├── asr_api_windows.py      # ASR API server for Windows
├── asr_ui.py               # Gradio web UI demo
└── README.md               # This document
```

---

## 🛠️ Environment & Dependencies

Recommended: **Python 3.8+** with a virtual environment:

```bash
python3 -m venv asr_env
source asr_env/bin/activate     # Linux/macOS
asr_env\Scripts\activate        # Windows
```

Install dependencies:

```bash
pip install -U funasr fastapi uvicorn
pip install gradio requests
```

> **funasr** is used for loading and running speech recognition models. You can replace it with other ASR frameworks if needed.

---

## ▶️ Running the ASR API Server

### 🐧 Linux

```bash
python -m uvicorn asr_api_linux:app --host 0.0.0.0 --port 8000
```

### 🪟 Windows

```bash
python -m uvicorn asr_api_windows:app --host 0.0.0.0 --port 8000
```

Once running, open your browser:

```
http://127.0.0.1:8000/docs
```

You can view the auto-generated API docs and test the endpoints.

---

## 🖥️ Running the UI Demo

After starting the API server, run:

```bash
python asr_ui.py
```

Open your browser at:

```
http://127.0.0.1:7860/
```

You can now test speech recognition through the web interface.

---

## 📌 API Usage Example

Assuming the API server is running:

```bash
curl -X POST "http://127.0.0.1:8000/asr" \
     -F "audio=@./sample.wav"
```

Sample response:

```json
{
  "text": "This is the recognition result"
}
```

---

## 🧠 Custom Models

You can replace the ASR model according to your needs, including offline or faster models.
If you change the model, make sure to update the **funasr** loading code in the scripts.

---

## 💡 Use Cases

* ✅ Local deployment of ASR service
* ✅ Speech-to-text integration
* ✅ ASR learning, experimentation, and demonstration
* ✅ Rapid prototyping of voice-enabled applications

---

## ❓ FAQ

**Q: Can this be deployed on a cloud server?**
A: Yes, the API server can be deployed to the cloud, and the front-end can access it via the public IP.

**Q: Does it support Chinese recognition?**
A: Yes, as long as you load a model that supports Chinese.


