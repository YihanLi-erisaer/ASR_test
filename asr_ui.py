import gradio as gr
import requests
import os

API_URL = "http://127.0.0.1:8000/transcribe/"

def transcribe(audio_file, model_name):
    if audio_file is None:
        return "请先上传音频或录音"
    
    try:
        with open(audio_file, "rb") as f:
            files = {"file": (os.path.basename(audio_file), f, "audio/wav")}
            data = {"model": model_name}
            
            response = requests.post(API_URL, files=files, data=data)
            
        if response.status_code == 200:
            result = response.json()
            if "error" in result:
                return f"错误: {result['error']}"
            return result.get("transcription", "无识别结果")
        else:
            return f"服务器请求失败: {response.status_code}"
            
    except Exception as e:
        return f"发生异常: {str(e)}"

# Build the Gradio interface
with gr.Blocks(title="语音识别 (ASR) 系统") as demo:
    gr.Markdown("# ASR 语音识别系统")
    gr.Markdown("上传音频文件或直接录音，选择模型后点击“开始识别”。后端会自动释放内存。")
    
    with gr.Row():
        with gr.Column():
            audio_input = gr.Audio(sources=["upload", "microphone"], type="filepath", label="音频输入")
            
            # select dropdown for model selection
            model_dropdown = gr.Dropdown(
                choices=["sensevoice", "paraformer"], 
                value="sensevoice", 
                label="选择识别模型"
            )
            
            submit_btn = gr.Button("开始识别", variant="primary")
            
        with gr.Column():
            # result output box
            text_output = gr.Textbox(label="识别结果", lines=10)

    # click action for the submit button
    submit_btn.click(
        fn=transcribe,
        inputs=[audio_input, model_dropdown],
        outputs=text_output
    )
    
    gr.Markdown("---")
    gr.Markdown("ℹ️ **提示**: 第一次使用某个模型会下载模型文件，请耐心等待。Windows 进程隔离模式确保任务结束后内存自动释放。")

if __name__ == "__main__":
    # activate the Gradio interface
    demo.launch(share=True, server_name="0.0.0.0", server_port=7860)