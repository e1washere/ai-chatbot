import streamlit as st
import requests
import tempfile
import os
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
import stripe
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

# Constants
MAX_FREE_PDFS = st.secrets.get("MAX_FREE_PDFS", 1)
SUPPORTED_LANGUAGES = {
    "Polski": "pol",
    "English": "eng",
    "Українська": "ukr",
    "Русский": "rus"
}

# OCR Function
def extract_text_via_ocr(path):
    """Extract text from image using OCR.space API"""
    try:
        with open(path, "rb") as f:
            r = requests.post(
                "https://api.ocr.space/parse/image",
                files={"file": f},
                data={
                    "apikey": st.secrets["OCR_SPACE_API_KEY"],
                    "language": "pol,eng,ukr,rus",
                    "isOverlayRequired": False,
                    "scale": True,
                    "OCREngine": 2
                },
                timeout=30  # Add timeout
            )
        r.raise_for_status()  # Raise exception for bad status codes
        result = r.json()
        parsed = result.get("ParsedResults")
        if not parsed or not parsed[0].get("ParsedText"):
            logger.warning("OCR returned no text")
            return ""
        return parsed[0]["ParsedText"]
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        st.error("❌ Błąd podczas rozpoznawania tekstu. Spróbuj ponownie później.")
        return ""

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
    .main { padding: 2rem; }
    .stButton>button { width: 100%; }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user { background-color: #2b313e; }
    .chat-message.bot { background-color: #475063; }
    .error-message {
        color: #ff4b4b;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ffd7d7;
        margin: 1rem 0;
    }
    .success-message {
        color: #00c853;
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d7ffd7;
        margin: 1rem 0;
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
try:
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
    with st.spinner("Przetwarzanie dokumentów..."):
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
                logger.info(f"Successfully processed PDF: {uploaded_file.name}")
            except Exception as e:
                logger.warning(f"PDF parsing failed, trying OCR: {str(e)}")
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
                    logger.info(f"Successfully processed PDF via OCR: {uploaded_file.name}")
                else:
                    st.error(f"❌ Nie udało się przetworzyć pliku: {uploaded_file.name}")

            os.unlink(tmp_path)

    if not all_docs:
        st.error("❌ Nie udało się odczytać tekstu z plików.")
        st.stop()

    # Initialize QA chain
    @st.cache_resource
    def load_qa_chain(docs):
        try:
            embeddings = OpenAIEmbeddings()
            db = FAISS.from_documents(docs, embeddings)
            retriever = db.as_retriever(
                search_kwargs={"k": 4}  # Retrieve top 4 most relevant chunks
            )
            qa = RetrievalQA.from_chain_type(
                llm=ChatOpenAI(temperature=0),  # More precise answers
                retriever=retriever,
                chain_type="stuff",
                return_source_documents=True
            )
            return qa
        except Exception as e:
            logger.error(f"Error initializing QA chain: {str(e)}")
            st.error("❌ Błąd podczas inicjalizacji asystenta AI. Spróbuj ponownie później.")
            return None

    qa_chain = load_qa_chain(all_docs)
    if not qa_chain:
        st.stop()

    st.success(f"✅ Załadowano {len(uploaded_files)} plików. Możesz teraz zadawać pytania!")

    # Chat interface
    if "history" not in st.session_state:
        st.session_state.history = []

    user_input = st.chat_input("Zadaj pytanie dotyczące treści dokumentów...")

    if user_input:
        try:
            st.session_state.history.append(("user", user_input))
            with st.spinner("Szukam odpowiedzi..."):
                result = qa_chain.invoke(user_input)
            st.session_state.history.append(("bot", result["result"]))
        except Exception as e:
            logger.error(f"Error processing user input: {str(e)}")
            st.error("❌ Błąd podczas przetwarzania pytania. Spróbuj ponownie później.")

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
except Exception as e:
    logger.error(f"Error processing file upload: {str(e)}")
    st.error("❌ Błąd podczas przetwarzania plików. Spróbuj ponownie później.")
