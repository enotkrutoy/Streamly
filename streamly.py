import streamlit as st
from openai import OpenAI, OpenAIError
import logging
from PIL import Image, ImageEnhance
import time
import json
import requests
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)

# Constants
NUMBER_OF_MESSAGES_TO_DISPLAY = 20
API_DOCS_URL = "https://docs.streamlit.io/library/api-reference"

# Page configuration (Перемещено в начало)
st.set_page_config(
    page_title="Streamly - Groq-Powered Streamlit Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Get help": "https://github.com/AdieLaine/Streamly",
        "Report a bug": "https://github.com/AdieLaine/Streamly",
        "About": """
            ## Streamly
            ### Powered by DeepSeek R1 Distill LLaMA 70B (Groq)
            An AI assistant for Streamlit developers with code generation, 
            documentation updates, and real-time chat capabilities.
        """
    }
)

# API Key Input
GROQ_API_KEY = st.text_input("Groq API Key", type="password")
if not GROQ_API_KEY:
    st.info("Please add your Groq API key to continue.", icon="🗝️")
else:
    # Создаем клиента для работы с Groq API
    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )

# Core functionality
def img_to_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        logging.error(f"Image conversion error: {str(e)}")
        return None

@st.cache_data(show_spinner=False)
def load_and_enhance_image(image_path, enhance=False):
    img = Image.open(image_path)
    if enhance:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.8)
    return img

@st.cache_data(show_spinner=False)
def load_streamlit_updates():
    try:
        with open("data/streamlit_updates.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"JSON loading error: {str(e)}")
        return {}

def initialize_conversation():
    return [
        {"role": "system", "content": "You are Streamly, a Streamlit specialist AI"},
        {"role": "assistant", "content": "Hello! How can I assist with Streamlit today?"}
    ]

# Chat processing with Groq
def process_chat_input(chat_input, latest_updates):
    user_input = chat_input.strip()

    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = initialize_conversation()

    st.session_state.conversation_history.append({"role": "user", "content": user_input})

    try:
        response = client.chat.completions.create(
            model="deepseek-r1-distill-llama-70b",
            messages=st.session_state.conversation_history,
            stream=True
        )

        response_text = ""
        with st.chat_message("assistant"):
            placeholder = st.empty()
            for chunk in response:
                delta = chunk.choices[0].delta.get("content", "")
                response_text += delta
                placeholder.markdown(response_text + "▌")
            placeholder.markdown(response_text)
        
        st.session_state.conversation_history.append({"role": "assistant", "content": response_text})

    except OpenAIError as e:
        st.error(f"API Error: {str(e)}")
        logging.error(f"Groq API error: {str(e)}")

# UI components
def main():
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = initialize_conversation()

    # Sidebar setup
    st.sidebar.image("imgs/sidebar_avatar.png", use_column_width=True)
    st.sidebar.markdown("---")
    
    mode = st.sidebar.radio(
        "Select Mode",
        ["Latest Updates", "Chat with Streamly"],
        index=1,
        format_func=lambda x: x.replace("_", " ").title()
    )

    # Chat interface
    if mode == "Chat with Streamly":
        chat_input = st.chat_input("Ask about Streamlit:")
        if chat_input:
            latest_updates = load_streamlit_updates()
            process_chat_input(chat_input, latest_updates)
        
        # Display chat history
        for message in st.session_state.conversation_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Updates section
    else:
        st.header("Latest Streamlit Updates")
        st.write("Check documentation: ", API_DOCS_URL)

if __name__ == "__main__":
    main()
