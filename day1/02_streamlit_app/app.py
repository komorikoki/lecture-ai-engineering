# app.py
import streamlit as st
import ui                   # UIモジュール
import llm                  # LLMモジュール
import database             # データベースモジュール
import metrics              # 評価指標モジュール
import data                 # データモジュール
import torch
from transformers import pipeline
from config import MODEL_NAME
from huggingface_hub import HfFolder



# --- アプリケーション設定 ---
st.set_page_config(page_title="Gemma Chatbot", layout="wide")

# --- 初期化処理 ---
# NLTKデータのダウンロード（初回起動時など）
metrics.initialize_nltk()

# データベースの初期化（テーブルが存在しない場合、作成）
database.init_db()

# データベースが空ならサンプルデータを投入
data.ensure_initial_data()
# set background color to black


# LLMモデルのロード（キャッシュを利用）
# モデルをキャッシュして再利用
@st.cache_resource
def load_model():
    """LLMモデルをロードする"""
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        st.info(f"Using device: {device}") # 使用デバイスを表示
        pipe = pipeline(
            "text-generation",
            model=MODEL_NAME,
            model_kwargs={"torch_dtype": torch.bfloat16},
            device=device
        )
        st.success(f"Success loading model '{MODEL_NAME}'")
        return pipe
    except Exception as e:
        st.error(f"Failed to load model '{MODEL_NAME}': {e}")
        st.error("There may be insufficient GPU memory. Please terminate unnecessary processes or consider using a smaller model.")
        return None
pipe = llm.load_model()

# --- Streamlit アプリケーション ---
st.title("llama 3.2-3B Chatbot with Feedback")
st.write("This is Gemma model-based chatbot. You can provide feedback on the responses.")
st.markdown("---")

# --- Sidebar ---
st.sidebar.title("Navigation")
# --- Footer and others (optional) ---
# --- Footer and others (optional) ---

# Use session state to keep track of the selected page
if 'page' not in st.session_state:
    st.session_state.page = "Chat" # Default page

page = st.sidebar.radio(
    "Page Selection",
    ["Chat", "View History", "Manage Sample Data"],
    key="page_selector",
    index=["Chat", "View History", "Manage Sample Data"].index(st.session_state.page), # Default page selection
    on_change=lambda: setattr(st.session_state, 'page', st.session_state.page_selector) # Update state on selection change
)


# --- Main Content ---
if st.session_state.page == "Chat":
    if pipe:
        ui.display_chat_page(pipe)
    else:
        st.error("Chat functionality is unavailable. Failed to load the model.")
elif st.session_state.page == "View History":
    ui.display_history_page()
elif st.session_state.page == "Manage Sample Data":
    ui.display_data_page()


st.sidebar.markdown("---")
st.sidebar.info("Developer: Komori Koki")

