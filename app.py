import streamlit as st
import requests
import tempfile
import os
from datetime import datetime
import httpx
from openai import OpenAI
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

# --- Page Config and Custom CSS ---
st.set_page_config(
    page_title="AI Dokumenty - Inteligentny Asystent Dokumentów",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# --- API Key and Secrets Validation ---
SECRETS_OK = True
REQUIRED_SECRETS = ["STRIPE_SECRET_KEY", "OPENAI_API_KEY", "OCR_SPACE_API_KEY", "STRIPE_PAYMENT_LINK"]
with st.sidebar:
    st.image("https://i.imgur.com/nJgq2hL.png", width=150) # Using a direct link to a hosted image
    st.markdown("---")

    for secret in REQUIRED_SECRETS:
        if secret not in st.secrets:
            st.error(f"❌ Brakuje sekretu: {secret}")
            SECRETS_OK = False
    
    if not SECRETS_OK:
        st.error("Proszę dodać brakujące sekrety w panelu Streamlit Cloud (Manage App -> Secrets).")
        st.stop()

# If all secrets are present, continue with initialization
try:
    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
except Exception as e:
    st.error("Błąd inicjalizacji Stripe. Sprawdź swój klucz API.")
    st.exception(e)
    st.stop()

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
    """Extract text from a file using OCR.space API"""
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
                timeout=60  # Increased timeout for larger files
            )
        r.raise_for_status()
        result = r.json()
        if result.get("IsErroredOnProcessing"):
            logger.error(f"OCR API Error: {result.get('ErrorMessage')}")
            st.error(f"❌ Błąd API OCR: {result.get('ErrorMessage')}")
            return ""
        parsed = result.get("ParsedResults")
        if not parsed or not parsed[0].get("ParsedText"):
            logger.warning("OCR returned no text")
            return ""
        return parsed[0]["ParsedText"]
    except requests.exceptions.RequestException as e:
        logger.error(f"OCR request error: {str(e)}")
        st.error("❌ Błąd połączenia z API OCR. Spróbuj ponownie później.")
        return ""
    except Exception as e:
        logger.error(f"An unexpected OCR error occurred: {str(e)}")
        st.error("❌ Wystąpił nieoczekiwany błąd podczas rozpoznawania tekstu.")
        st.exception(e) # Show full exception for debugging
        return ""

# Page config is now at the top
# Custom CSS is now at the top

# Sidebar
with st.sidebar:
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
            st.markdown(f"[Kup subskrypcję]({st.secrets['STRIPE_PAYMENT_LINK']})", unsafe_allow_html=True)
    else:
        st.success("💎 Wersja premium: Nielimitowana liczba PDF-ów")

# Main content
st.title("🤖 AI Dokumenty - Inteligentny Asystent Dokumentów")
st.markdown("""
    Prześlij swoje dokumenty PDF i zadawaj pytania w naturalnym języku.
    Nasz asystent AI pomoże Ci znaleźć odpowiedzi w Twoich dokumentach.
""")

# Main app logic in a try-except block for better error handling
try:
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
    with st.spinner("Przetwarzanie dokumentów... To może potrwać chwilę."):
        for uploaded_file in uploaded_files:
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                
                # Try direct PDF parsing first
                try:
                    loader = PyPDFLoader(tmp_path)
                    docs = loader.load()
                    # If PDF is scanned, docs can be empty or have no text content.
                    if not docs or not "".join(d.page_content for d in docs).strip():
                        logger.warning(f"PDF '{uploaded_file.name}' seems to be scanned or empty, falling back to OCR.")
                        raise ValueError("Empty PDF") # Force fallback to OCR
                    
                    for doc in docs:
                        doc.metadata["source"] = uploaded_file.name
                        doc.metadata["page"] = doc.metadata.get("page", 0) + 1
                    all_docs.extend(docs)
                    logger.info(f"Successfully processed digital PDF: {uploaded_file.name}")

                except Exception as e:
                    logger.warning(f"Digital PDF parsing failed for '{uploaded_file.name}' ({e}), trying OCR.")
                    text = extract_text_via_ocr(tmp_path)
                    if text:
                        doc = Document(
                            page_content=text,
                            metadata={"source": uploaded_file.name, "page": 1}
                        )
                        all_docs.append(doc)
                        logger.info(f"Successfully processed scanned PDF via OCR: {uploaded_file.name}")
                    else:
                        st.warning(f"⚠️ Nie udało się przetworzyć pliku: {uploaded_file.name}. Może być uszkodzony lub pusty.")

            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    if not all_docs:
        st.error("❌ Nie udało się odczytać tekstu z żadnego z przesłanych plików. Sprawdź, czy pliki nie są uszkodzone lub chronione hasłem.")
        st.stop()

    # Initialize QA chain
    @st.cache_resource
    def load_qa_chain(_docs): # Use _docs to indicate it's for caching
        try:
            # Step 1: Create a fully configured OpenAI client, bypassing langchain's auto-configuration
            # This is the key to solving the proxy issue in Streamlit Cloud
            openai_client = OpenAI(
                api_key=st.secrets["OPENAI_API_KEY"],
                http_client=httpx.Client(proxies=None) # Explicitly disable proxies
            )

            # Step 2: Pass the pre-configured client to LangChain components
            # We still pass the api_key for validation purposes in some langchain versions
            embeddings = OpenAIEmbeddings(
                openai_api_key=st.secrets["OPENAI_API_KEY"],
                client=openai_client
            )
            
            db = FAISS.from_documents(_docs, embeddings)
            retriever = db.as_retriever(search_kwargs={"k": 5})

            llm = ChatOpenAI(
                openai_api_key=st.secrets["OPENAI_API_KEY"],
                client=openai_client,
                temperature=0.1,
                model="gpt-4o"
            )

            # Step 3: Build the QA chain
            qa = RetrievalQA.from_chain_type(
                llm=llm,
                retriever=retriever,
                chain_type="stuff",
                return_source_documents=True
            )
            return qa
        except Exception as e:
            logger.error(f"Error initializing QA chain: {str(e)}")
            st.error("❌ Błąd podczas inicjalizacji asystenta AI. Sprawdź klucz OpenAI API.")
            st.exception(e) # Show full exception for debugging
            return None

    qa_chain = load_qa_chain(all_docs)
    if not qa_chain:
        st.stop()

    st.success(f"✅ Załadowano {len(uploaded_files)} plików. Możesz teraz zadawać pytania!")

    # Chat interface
    if "history" not in st.session_state:
        st.session_state.history = []

    if user_input := st.chat_input("Zadaj pytanie dotyczące treści dokumentów..."):
        try:
            st.session_state.history.append(("user", user_input))
            with st.spinner("Analizuję..."):
                result = qa_chain.invoke({"query": user_input})
            st.session_state.history.append(("bot", result["result"]))
            
            # Display chat history immediately after getting a new response
            for role, message in st.session_state.history:
                with st.chat_message(role):
                    st.write(message)
            
            # Show sources for the last response
            with st.expander("📚 Zobacz źródła odpowiedzi"):
                for i, doc in enumerate(result.get("source_documents", []), start=1):
                    st.markdown(f"""
                    **Źródło {i}:** Plik: `{doc.metadata.get('source', 'N/A')}`, Strona: `{doc.metadata.get('page', 'N/A')}`
                    > {doc.page_content[:300]}...
                    """)

        except Exception as e:
            logger.error(f"Error processing user input: {str(e)}")
            st.error("❌ Błąd podczas przetwarzania pytania.")
            st.exception(e) # Show full exception for debugging
    else:
        # Display chat history on first load as well
        for role, message in st.session_state.history:
            with st.chat_message(role):
                st.write(message)


except Exception as e:
    logger.error(f"An unexpected error occurred in the main app block: {str(e)}")
    st.error("❌ Wystąpił krytyczny błąd aplikacji.")
    st.exception(e) # Show full exception for debugging
