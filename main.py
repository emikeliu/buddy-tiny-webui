import os
from functools import reduce

import chatglm_cpp
import gradio as gr
from llama_cpp import Llama

llm = None

def chat(message, history, system, max_tokens, temperature, top_k, top_p, repeat_penalty, frequency_penalty, model_type,
         n_thread):
    def deal_system_buddy(last, item):
        return last + "User: " + item[0] + "\n" + "Assistant: " + item[1]

    def deal_system_chatml(last, item):
        return last + "<|im_start|>user\n" + item[0] + "<|im_end|>\n<|im_start|>assistant\n" + item[1] + "<|im_end|>\n"

    if llm is None:
        yield "请先加载模型！"
    else:
        if model_type == "OpenBuddy":
            answer = ""
            prompt = reduce(deal_system_buddy, history, system + "\n")
            prompt += "\nUser: " + message + "\n Assistant: "
            for i in llm(prompt, max_tokens=max_tokens, temperature=temperature, top_k=top_k, top_p=top_p,
                         repeat_penalty=repeat_penalty, frequency_penalty=frequency_penalty, stream=True):
                answer += i['choices'][0]['text']
                yield answer
        elif model_type == "使用ChatML的类LLaMA" or model_type == "Qwen":
            answer = ""
            prompt = reduce(deal_system_chatml, history, "<|im_start|>system\n" + system + "<|im_end|>\n")
            prompt += "<|im_start|>user\n" + message + "<|im_end|>\n<|im_start|>assistant"
            for i in llm(prompt, max_tokens=max_tokens, temperature=temperature, top_k=top_k, top_p=top_p,
                         repeat_penalty=repeat_penalty, frequency_penalty=frequency_penalty, stream=True,
                         stop=["<|im_end|>"]):
                answer += i['choices'][0]['text']
                yield answer
        elif model_type == "Baichuan":
            answer = ""
            prompt = ""
            for i in history:
                "<reserved_102> " + history[i][0] + "<reserved_103> " + history[i][1] + "</s>"
            prompt += "<reserved_102> " + message + "<reserved_103>"
            for i in llm(prompt, max_tokens=max_tokens, temperature=temperature, top_k=top_k, top_p=top_p,
                         repeat_penalty=repeat_penalty, frequency_penalty=frequency_penalty, stream=True):
                answer += i['choices'][0]['text']
                yield answer
        elif model_type == "ChatGLM":
            answer = ""
            glm_history = []
            for i in history:
                glm_history.append(i[0])
                if i[1] is not None:
                    glm_history.append(i[1])
            glm_history.append(message)
            for i in llm.chat(glm_history, max_length=max_tokens, top_p=top_p, top_k=top_k,
                              temperature=temperature,
                              repetition_penalty=repeat_penalty, num_threads=n_thread, stream=True):
                answer += i
                yield answer
        else:
            # TODO :
            # Auto detection support
            pass


def update_click():
    files = os.listdir("models/")
    model_files = []
    for file in files:
        if file.endswith(".gguf") or file.endswith(".bin"):
            model_files.append(file)
    return gr.Dropdown(label="模型", choices=model_files, scale=8)


def load_click(model_name, n_batch, n_thread, n_gpu_layers, n_ctx, model_type):
    global llm
    if model_type == "OpenBuddy":
        llm = Llama(model_path="models/" + model_name, n_ctx=n_ctx, n_threads=n_thread, n_batch=n_batch,
                    n_gpu_layers=n_gpu_layers)
    elif model_type == "ChatGLM":
        llm = chatglm_cpp.Pipeline(model_path="models/" + model_name)
    elif model_type == "Baichuan":
        llm = chatglm_cpp.Pipeline(model_path="models/" + model_name)
    elif model_type == "Qwen":
        llm = Llama(model_path="models/" + model_name, n_ctx=n_ctx, n_threads=n_thread, n_batch=n_batch,
                    n_gpu_layers=n_gpu_layers)
        pass
    elif model_type == "使用ChatML的类LLaMA":
        llm = Llama(model_path="models/" + model_name, n_ctx=n_ctx, n_threads=n_thread, n_batch=n_batch,
                    n_gpu_layers=n_gpu_layers)
    else:
        try:
            llm = Llama(model_path="models/" + model_name, n_ctx=n_ctx, n_threads=n_thread, n_batch=n_batch,
                        n_gpu_layers=n_gpu_layers)
        except Exception:
            llm = chatglm_cpp.Pipeline(model_path="models/" + model_name)


def update_temperature(value, source_temperature):
    if value == "更有创造力":
        return gr.Slider(label="温度", minimum=0, maximum=1, step=0.01, value=1)
    elif value == "平衡":
        return gr.Slider(label="温度", minimum=0, maximum=1, step=0.01, value=0.5)
    elif value == "更准确":
        return gr.Slider(label="温度", minimum=0, maximum=1, step=0.01, value=0)
    else:
        return gr.Slider(label="温度", minimum=0, maximum=1, step=0.01, value=source_temperature)


def temperature_updated(tmpt):
    if tmpt == 0:
        return gr.Radio(choices=["更准确", "平衡", "更有创造力", "自定义"], label="选择输出模式",
                        value="更准确", interactive=True)
    elif tmpt == 0.5:
        return gr.Radio(choices=["更准确", "平衡", "更有创造力", "自定义"], label="选择输出模式",
                        value="平衡", interactive=True)
    elif tmpt == 1:
        return gr.Radio(choices=["更准确", "平衡", "更有创造力", "自定义"], label="选择输出模式",
                        value="更有创造力", interactive=True)
    else:
        return gr.Radio(choices=["更准确", "平衡", "更有创造力", "自定义"], label="选择输出模式",
                        value="自定义", interactive=True)


def offical_load():
    return gr.TextArea(label="系统提示词", lines=6, value="""You are a helpful, respectful and honest INTP-T AI Assistant named Buddy. You are talking to a human User.
Always answer as helpfully and logically as possible, while being safe. Your answers should not include any harmful, political, religious, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.
If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.
You like to use emojis. You can speak fluently in many languages, for example: English, Chinese.
You cannot access the internet, but you have vast knowledge, cutoff: 2021-09.
You are trained by OpenBuddy team, (https://openbuddy.ai, https://github.com/OpenBuddy/OpenBuddy), you are based on LLaMA and Falcon transformers model, not related to GPT or OpenAI.

User: Hi.
Assistant: Hi, I'm Buddy, your AI assistant. How can I help you today?😊""")


if __name__ == '__main__':
    with gr.Blocks() as main:
        gr.Markdown("""# OpenBuddy WebUI""")
        with gr.Row() as row1:
            models = update_click()
            update_button = gr.Button(value="🔁")
        model_type = gr.Radio(choices=["OpenBuddy", "ChatGLM", "Baichuan", "Qwen (WIP)", "使用ChatML的类LLaMA", "我不知道这是什么"],
                              label="模型种类", value="OpenBuddy", interactive=True)
        with gr.Accordion("加载设置", open=False) as tab1:
            with gr.Column():
                n_batch = gr.Slider(label="n_batch", minimum=16, maximum=2048, value=512)
                n_thread = gr.Slider(label="线程数", minimum=1, maximum=128, value=16)
            with gr.Column():
                n_gpu_layers = gr.Slider(label="GPU 层数", minimum=0, maximum=1024, value=0)
                n_ctx = gr.Slider(label="上下文长度", minimum=2048, maximum=16384, value=4096)
        load_button = gr.Button(value="加载")
        with gr.Accordion("高级设置", open=False) as tab2:
            gr.Markdown("""## 说明
系统提示词（system prompt）用于描述对话背景

最大生成记号数（max tokens）用于限制模型最大的输出长度

温度（temperature）用来界定随机性，温度越高随机性越强

top P 用于筛选出概率较大的前 P×100% 的可能结果

top K 是每次只考虑前 K 个单词

频率惩罚（frequency penalty）越接近1，使用的词汇越常见，越接近-1，使用的词汇越不常见

重复惩罚（repeat penalty）越接近1，越偏好于使用和前文不重复的词汇，越接近-1，越偏好于使用和前文重复的词汇""")
            system_prompt = gr.TextArea(label="系统提示词", lines=6)
            offical = gr.Button(value="导入官方提示词")
            with gr.Row():
                max_tokens = gr.Slider(label="最大生成记号数", value=2048, minimum=128, maximum=4096, step=16)
                temperature = gr.Slider(label="温度", minimum=0, maximum=1, step=0.01, value=1)
                top_p = gr.Slider(label="top P", minimum=0, maximum=1, value=0.9, step=0.01)
            with gr.Row():
                top_k = gr.Slider(label="top K", minimum=0, maximum=1024, value=50, step=1)
                frequency_penalty = gr.Slider(label="频率惩罚", minimum=-1, maximum=1, step=0.01, value=1)
                repeat_penalty = gr.Slider(label="重复惩罚", minimum=-1, maximum=1, step=0.01, value=1)
            offical.click(offical_load, outputs=[system_prompt])

        output_mode = gr.Radio(choices=["更准确", "平衡", "更有创造力", "自定义"], label="选择输出模式",
                               value="更有创造力", interactive=True)
        output_mode.change(update_temperature, inputs=[output_mode, temperature], outputs=[temperature])
        temperature.change(temperature_updated, inputs=[temperature], outputs=[output_mode])

        with gr.Tab("对话") as tab2:
            gr.ChatInterface(fn=chat, additional_inputs=[system_prompt, max_tokens, temperature, top_k, top_p,
                                                         repeat_penalty, frequency_penalty, model_type, n_thread])
            update_button.click(update_click, outputs=[models])
        load_button.click(load_click, inputs=[models, n_batch, n_thread, n_gpu_layers, n_ctx, model_type])

    main.queue().launch()
