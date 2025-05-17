import streamlit as st
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
import os
from dotenv import load_dotenv
from pdf2image import convert_from_path
import pytesseract
import tempfile

st.set_page_config(page_title="Czatbot AI dla Firm", layout="centered")
load_dotenv()

def extract_text_from_scanned_pdf(file_path):
    pages = convert_from_path(file_path)
    all_text = ""
    for page in pages:
        text = pytesseract.image_to_string(page, lang="pol+eng", config="--psm 6")
        all_text += "\n" + text
    return all_text

@st.cache_resource
def load_qa_chain(file_path):
    docs = []
    if file_path.endswith(".txt"):
        loader = TextLoader(file_path)
        docs = loader.load()
    elif file_path.endswith(".pdf"):
        text = extract_text_from_scanned_pdf(file_path)
        if text.strip() == "":
            raise ValueError("Nie udało się odczytać tekstu z dokumentu.")
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
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    qa_chain = load_qa_chain(tmp_path)
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
