# Install the environment and dependencies
pip3 install -U funasr
pip install fastapi uvicorn

# Activate the virtual environment (this can be ignored if you are using a global Python installation)
source asr_tts_env/Scripts/activate

# Run the ASR API server
python -m uvicorn asr_api_linux:app --host 0.0.0.0 --port 8000
python -m uvicorn asr_api_windows:app --host 0.0.0.0 --port 8000
python asr_api_windows.py

# Access the API documentation at:
http://127.0.0.1:8000/docs
http://192.168.100.185:8000/docs

**Install the UI dependencies:**
pip install gradio requests

# Acess the asr model with UI:
*   **Run the ASR API server first, then run the UI**
*   **Linux version:**
python -m uvicorn asr_api_linux:app --host 0.0.0.0 --port 8000
*  **Windows version:**
python -m uvicorn asr_api_windows:app --host 0.0.0.0 --port 8000

## Finally, run the UI (make sure the API server is running first)
python asr_ui.py

## Access the UI at:
http://127.0.0.1:7860/

