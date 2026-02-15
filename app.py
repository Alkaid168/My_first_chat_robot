import streamlit as st
import time
import datetime
import os
import json
from openai import OpenAI

class BaseBot:
    def __init__(self, name, prompt):
        self.name = name
        self.prompt = prompt
        self.history = []
        self.load_memory()
    
    def _get_time(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def chat(self, user_input):
        client = OpenAI(
            api_key = os.environ.get("DEEPSEEK_API_KEY"),
            base_url = "https://api.deepseek.com"
        )

        # --- 1. 构建完整的上下文列表 ---
        # 先放系统人设
        messages_to_send = [{"role": "system", "content": self.prompt}]
        
        # 再把历史记录塞进去
        for log in self.history:
            # 我们的历史记录里有 time 字段，API 不需要 time，只取 role 和 content
            messages_to_send.append({
                "role": log["role"],       # 这里必须是 "user" 或 "assistant"
                "content": log["content"]
            })
            
        # 最后加上当前这一句用户说的话
        messages_to_send.append({"role": "user", "content": user_input})

        # --- 2. 发送请求 ---
        response = client.chat.completions.create(
            model = "deepseek-chat", 
            messages = messages_to_send, # 发送完整列表
            stream = False
        ).choices[0].message.content

        # ... (后面保存历史的代码保持不变，记得把 "bot" 改成 "assistant") ...
        user_message = {
            "role" : "user",
            "content" : user_input,
            "time" : self._get_time()
        }
        self.history.append(user_message)
        bot_message = {
            "role" : "assistant",
            "content" : response,
            "time" : self._get_time()
        }
        self.history.append(bot_message)
        self.save_memory()
        return response
    
    def save_memory(self):
        filename = f"{self.name}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=4)
    
    def load_memory(self):
        filename = f"{self.name}.json"
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
                print(f"【系统】成功加载{len(self.history)}条聊天记录。")
            except Exception as e:
                print(f"【系统】聊天记录文件损坏，已重置记忆！")
                self.history = []
        else:
            print("【系统】暂无聊天记录。")

    def show_memory(self):
        print(f"---{self.name}的回忆录---")
        for message in self.history:
            role = message["role"]
            content = message["content"]
            time = message["time"]
            print(f"[{time}]{role}:\n{content}")

    def clear_memory(self, clear_json = False):
        self.history = []
        print("【系统】成功清除暂存记忆！")
        if clear_json:
            filename = f"{self.name}.json"
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    print("【系统】成功清除记忆文件！")
            except Exception as e:
                print("【系统】暂无记忆文件，无法清除！")

# ... (BaseBot 类保持不变) ...

# --- 1. 页面设置 (必须放第一行！) ---
st.set_page_config(page_title="Alkaid的AI空间", page_icon="🤖")

# --- 2. 初始化机器人 ---
if "bot" not in st.session_state:
    st.session_state.bot = BaseBot("NBbot", "你叫NBbot，是一个非常牛逼的超级机器人！")

# --- 3. 初始化聊天记录 (关键修改！！！) ---
if "messages" not in st.session_state:
    # 不再是空列表 []
    # 而是从机器人的 history 里搬运过来！
    # 这样一打开网页，以前聊过的记录就直接显示在屏幕上了！
    st.session_state.messages = []
    for log in st.session_state.bot.history:
        st.session_state.messages.append({
            "role": log["role"], 
            "content": log["content"]
        })

# --- 4. 侧边栏 ---
with st.sidebar:
    st.header("⚙️ 控制面板")
    if st.button("🗑️ 清空对话"):
        # 调用机器人的清除记忆
        st.session_state.bot.clear_memory(clear_json=True)
        # 清除 UI 的记忆
        st.session_state.messages = [] 
        st.rerun() # 刷新

st.title("🤖 JSONbot - Alkaid的专属助手")
st.caption("🚀 由 DeepSeek 驱动 | Streamlit 强力驱动")

# --- 5. 渲染历史消息 ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): 
        st.markdown(msg["content"])

# --- 6. 处理用户输入 ---
if user_input := st.chat_input("说点什么吧..."):
    
    # 显示用户的话
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # AI 回复
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 调用机器人
        response = st.session_state.bot.chat(user_input)
        
        # 打字机效果
        for chunk in response:
            full_response += chunk
            # 为了体验更好，如果字数太多，延迟可以调小一点，比如 0.02
            time.sleep(0.02) 
            message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
    
    # 存入 UI 记录
    st.session_state.messages.append({"role": "assistant", "content": full_response})