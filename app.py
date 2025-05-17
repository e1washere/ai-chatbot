import streamlit as st
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.document_loaders.base import Document
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import tempfile
import os
from dotenv import load_dotenv

st.set_page_config(page_title="Czatbot AI dla Firm", layout="centered")

load_dotenv()

def extract_text_from_scanned_pdf(file_path):
    pages = convert_from_path(file_path)
    all_text = ""
    for i, page in enumerate(pages):
        text = pytesseract.image_to_string(page)
        all_text += f"\nPage {i + 1}:\n{text}"
    return all_text

@st.cache_resource
def load_qa_chain(file_path):
    docs = []
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
    except:
        text = extract_text_from_scanned_pdf(file_path)
        docs = [Document(page_content=text)]
    db = FAISS.from_documents(docs, OpenAIEmbeddings())
    retriever = db.as_retriever()
    qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(),
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True
    )
    return qa

st.title("🤖 Czatbot AI z Twoich Dokumentów")

uploaded_file = st.file_uploader("📎 Prześlij plik PDF lub TXT", type=["pdf", "txt"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name[-4:]) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file_path = tmp_file.name
    qa_chain = load_qa_chain(tmp_file_path)
    st.success("✅ Plik został załadowany. Możesz teraz zadawać pytania!")
else:
    st.info("⬆️ Prześlij plik, aby rozpocząć.")
    st.stop()

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.chat_input("Zadaj pytanie dotyczące treści pliku...")

if user_input:
    st.session_state.history.append(("user", user_input))
    result = qa_chain.invoke(user_input)
    answer = result['result']
    st.session_state.history.append(("bot", answer))

for role, message in st.session_state.history:
    with st.chat_message(role):
        st.write(message)

if st.checkbox("📚 Pokaż źródło odpowiedzi") and "result" in locals():
    for i, doc in enumerate(result.get("source_documents", []), start=1):
        st.markdown(f"**Źródło {i}:**\n{doc.page_content}")
