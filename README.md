# activate the virtual environment (this can be ignored if you are using a global Python installation)
source asr_tts_env/Scripts/activate

# Run the ASR API server
python -m uvicorn asr_api:app --host 0.0.0.0 --port 8000

# Access the API documentation at:
http://127.0.0.1:8000/docs
http://192.168.100.185:8000/docs