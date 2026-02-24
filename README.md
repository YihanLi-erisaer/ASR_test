# activate the virtual environment
source asr_tts_env/Scripts/activate

# Run the ASR API server
uvicorn asr_api:app --host 0.0.0.0 --port 8000

# Access the API documentation at:
http://127.0.0.1:8000/docs
http://192.168.100.185:8000/docs