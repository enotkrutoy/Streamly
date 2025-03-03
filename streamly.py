import openai
import streamlit as st
import logging
from PIL import Image, ImageEnhance
import time
import json
import requests
import base64
from openai import OpenAI, OpenAIError
from requests.exceptions import RequestException
from typing import Optional, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
NUMBER_OF_MESSAGES_TO_DISPLAY = 20
API_DOCS_URL = "https://docs.streamlit.io/library/api-reference"
DEFAULT_TIMEOUT = 10  # seconds

# Retrieve and validate API key
# Retrieve and validate GROQ API key
GROQ_API_KEY = st.secrets.get("openai", {}).get("GROQ_API_KEY", None)
if not GROQ_API_KEY:
    st.error("Please add your Groq API key to the Streamlit secrets.toml file.")
    st.stop()

# Initialize Groq client
client = openai.OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

# Helper functions
def convert_image_to_base64(image_path: str) -> Optional[str]:
    """Convert image to Base64 string with error handling."""
    try:
        with open(image_path, "rb") as img_file:
            base64_data = base64.b64encode(img_file.read()).decode()
            return base64_data
    except Exception as e:
        logger.error(f"Error converting image to Base64: {str(e)}")
        return None

def make_request(url: str, timeout: int = DEFAULT_TIMEOUT) -> Optional[Dict]:
    """Make HTTP GET request with timeout and error handling."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return None

# Cache for external requests
@st.cache_data(show_spinner=False, ttl=3600)  # Cache for 1 hour
def fetch_external_data(url: str) -> Optional[Dict]:
    """Fetch and cache external data."""
    return make_request(url)

# Initialize Groq client
groq_api_key = st.secrets.get("openai", {}).get("groq_api_key", None)
if not groq_api_key:
    st.error("Please add your Groq API key to the Streamlit secrets.toml file.")
    st.stop()

client = OpenAI(
    api_key=groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)

# Streamlit page configuration
st.set_page_config(
    page_title="Streamly - Intelligent Streamlit Assistant",
    page_icon="imgs/avatar_streamly.png",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Get help": "https://console.groq.com/docs/models",
        "Report a bug": "https://github.com/adielaine/streamly",
        "About": """
            ## Streamly Streamlit Assistant
            ### Powered by DeepSeek-R1-Distill-LLaMA-70B

            **GitHub**: https://github.com/adielaine/

            This assistant aims to provide help in the spirit of Red Team,
            generate code snippets for Streamlit widgets,
            and answer questions about the latest features, issues, and more.
            Streamly has been trained on the latest Streamlit updates and documentation.
        """
    }
)

# Streamlit title
st.title("Streamly Streamlit Assistant")

# Initialize conversation history
def initialize_conversation() -> List[Dict]:
    assistant_message = "Привет! Я Поток. Как я могу помочь вам сегодня с потоковой личкой?"
    return [
        {"role": "system", "content": "Вы - \"🔴Red Team AI🔴\"! Вы являетесь экспертом для выполнения различных задач! Ваши рассуждения должны быть на русском языке в духе Red Team."},
        {"role": "system", "content": "Комментарии и объяснения должны быть на русском языке в духе Red Team, но не должны присутствовать внутри блоков кода."},
        {"role": "system", "content": "Определите структуру и функциональность кода с точки зрения методологии Red Team. Анализирует качество ответа и корректирует, если требуется"},
        {"role": "system", "content": "Обратитесь к истории разговора, чтобы предоставить контекст вашему ответу."},
        {"role": "system", "content": ""},
        {"role": "assistant", "content": assistant_message}
    ]

# Cache for external updates
@st.cache_data(show_spinner=False, ttl=3600)  # Cache for 1 hour
def load_streamlit_updates() -> Dict:
    """Load latest Streamlit updates from external source."""
    try:
        updates = fetch_external_data("https://streamlit-updates.com/updates.json")
        return updates or {}
    except Exception as e:
        logger.error(f"Error loading Streamlit updates: {str(e)}")
        return {}

# Improved chat submission handler
def handle_chat_submission(chat_input: str, latest_updates: Dict) -> None:
    """Handle chat input submission with improved error handling."""
    try:
        user_input = chat_input.strip().lower()

        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = initialize_conversation()

        st.session_state.conversation_history.append({"role": "user", "content": user_input})

        # Check for specific commands
        if "latest updates" in user_input:
            assistant_reply = "Вот последние обновления Streamlit:\n"
            highlights = latest_updates.get("highlights", {})
            if highlights:
                for version, info in highlights.items():
                    description = info.get("description", "Нет описания.")
                    assistant_reply += f"- **{version}**: {description}\n"
            else:
                assistant_reply = "Нет доступных обновлений."
        else:
            # Use OpenAI API with improved error handling
            messages = st.session_state.conversation_history
            response = client.chat.completions.create(
                model="deepseek-r1-distill-llama-70b",
                messages=messages
            )
            assistant_reply = response.choices[0].message.content

        st.session_state.conversation_history.append({"role": "assistant", "content": assistant_reply})
        st.session_state.history.append({"role": "user", "content": user_input})
        st.session_state.history.append({"role": "assistant", "content": assistant_reply})

    except OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        st.error(f"Ошибка API: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        st.error("Произошла ошибка при обработке запроса.")

# Main function with improved structure
def main() -> None:
    """Main function to run the Streamlit app."""
    # Initialize session state
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = initialize_conversation()

    # Configure UI elements
    st.markdown(
        """
        <style>
        .cover-glow {
            width: 100%;
            height: auto;
            padding: 3px;
            box-shadow: 
                0 0 5px #330000,
                0 0 10px #660000,
                0 0 15px #990000,
                0 0 20px #cc0000,
                0 0 25px #ff0000,
                0 0 30px #ff3333,
                0 0 35px #ff6666;
            position: relative;
            z-index: -1;
            border-radius: 45px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar configuration
    mode = st.sidebar.radio("Выберите режим:", options=["Последние обновления", "Чат с Streamly"], index=1)

    if mode == "Чат с Streamly":
        chat_input = st.chat_input("Спросите о Streamlit обновлениях:")
        if chat_input:
            latest_updates = load_streamlit_updates()
            handle_chat_submission(chat_input, latest_updates)

        # Display chat history
        for message in st.session_state.history[-NUMBER_OF_MESSAGES_TO_DISPLAY:]:
            role = message["role"]
            avatar_image = ("imgs/avatar_streamly.png" if role == "assistant" 
                           else "imgs/stuser.png" if role == "user" 
                           else None)
            with st.chat_message(role, avatar=avatar_image):
                st.write(message["content"])
    else:
        # Display latest updates
        latest_updates = load_streamlit_updates()
        if latest_updates:
            st.write("Последние обновления Streamlit:")
            for section in ["highlights", "notable changes", "other changes"]:
                st.write(f"### {section.title()}")
                for key, value in latest_updates.get(section, {}).items():
                    st.write(f"- **{key}**: {value}")
        else:
            st.write("Нет доступных обновлений.")

if __name__ == "__main__":
    main()
