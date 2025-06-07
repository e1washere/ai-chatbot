import streamlit as st
import requests
import tempfile
import os
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
import stripe

# Initialize Stripe
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

# Constants
MAX_FREE_PDFS = 1
SUPPORTED_LANGUAGES = {
    "Polski": "pol",
    "English": "eng",
    "Українська": "ukr",
    "Русский": "rus"
}

# Page config
st.set_page_config(
    page_title="AI Dokumenty - Inteligentny Asystent Dokumentów",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #2b313e;
    }
    .chat-message.bot {
        background-color: #475063;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=AI+Dokumenty", width=150)
    st.markdown("---")
    
    # Language selection
    selected_language = st.selectbox(
        "🌐 Wybierz język / Select language",
        list(SUPPORTED_LANGUAGES.keys())
    )
    
    # Subscription status
    if "subscription_status" not in st.session_state:
        st.session_state.subscription_status = "free"
    
    if st.session_state.subscription_status == "free":
        st.info("🆓 Wersja darmowa: 1 PDF")
        if st.button("💎 Przejdź na wersję premium"):
            st.markdown(f"[Przejdź na wersję premium]({st.secrets['STRIPE_PAYMENT_LINK']})")
    else:
        st.success("💎 Wersja premium: Nielimitowana liczba PDF-ów")

# Main content
st.title("🤖 AI Dokumenty - Inteligentny Asystent Dokumentów")
st.markdown("""
    Prześlij swoje dokumenty PDF i zadawaj pytania w naturalnym języku.
    Nasz asystent AI pomoże Ci znaleźć odpowiedzi w Twoich dokumentach.
""")

# File uploader
uploaded_files = st.file_uploader(
    "📎 Prześlij pliki PDF",
    type=["pdf"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("⬆️ Prześlij pliki PDF, aby rozpocząć.")
    st.stop()

# Check subscription limits
if st.session_state.subscription_status == "free" and len(uploaded_files) > MAX_FREE_PDFS:
    st.error(f"❌ Wersja darmowa pozwala na przesyłanie maksymalnie {MAX_FREE_PDFS} pliku PDF.")
    st.info("💎 Przejdź na wersję premium, aby przesyłać nieograniczoną liczbę plików.")
    st.stop()

# Process uploaded files
all_docs = []
for uploaded_file in uploaded_files:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    
    try:
        # Try direct PDF parsing first
        loader = PyPDFLoader(tmp_path)
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = uploaded_file.name
            doc.metadata["page"] = doc.metadata.get("page", 0) + 1
        all_docs.extend(docs)
    except:
        # Fallback to OCR
        text = extract_text_via_ocr(tmp_path)
        if text:
            doc = Document(
                page_content=text,
                metadata={
                    "source": uploaded_file.name,
                    "page": 1
                }
            )
            all_docs.append(doc)

    os.unlink(tmp_path)

if not all_docs:
    st.error("❌ Nie udało się odczytać tekstu z plików.")
    st.stop()

# Initialize QA chain
@st.cache_resource
def load_qa_chain(docs):
    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(docs, embeddings)
    retriever = db.as_retriever()
    qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(),
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True
    )
    return qa

qa_chain = load_qa_chain(all_docs)
st.success(f"✅ Załadowano {len(uploaded_files)} plików. Możesz teraz zadawać pytania!")

# Chat interface
if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.chat_input("Zadaj pytanie dotyczące treści dokumentów...")

if user_input:
    st.session_state.history.append(("user", user_input))
    result = qa_chain.invoke(user_input)
    st.session_state.history.append(("bot", result["result"]))

# Display chat history
for role, message in st.session_state.history:
    with st.chat_message(role):
        st.write(message)

# Show sources
if st.checkbox("📚 Pokaż źródła odpowiedzi") and "result" in locals():
    st.markdown("### Źródła:")
    for i, doc in enumerate(result.get("source_documents", []), start=1):
        st.markdown(f"""
        **Źródło {i}:**
        - Plik: {doc.metadata.get('source', 'Nieznany')}
        - Strona: {doc.metadata.get('page', 'Nieznana')}
        - Fragment:
        ```
        {doc.page_content[:200]}...
        ```
        """)
