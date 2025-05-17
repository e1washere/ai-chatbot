import streamlit as st
import tempfile
import requests
from dotenv import load_dotenv
import os

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain.chains import RetrievalQA
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI

load_dotenv()
OCR_SPACE_API_KEY = st.secrets["OCR_SPACE_API_KEY"]

st.set_page_config(page_title="Czatbot AI dla Firm", layout="centered")

@st.cache_resource
def load_qa_chain(text):
    if not text.strip():
        raise ValueError("Brak tekstu do przetworzenia.")
    docs = [Document(page_content=text)]
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

st.title("🤖 Czatbot AI z Twoich Dokumentów")

uploaded_file = st.file_uploader("📎 Prześlij plik PDF (zeskanowany) lub TXT", type=["pdf", "txt"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    if uploaded_file.type == "text/plain":
        text = open(tmp_path, "r", encoding="utf-8").read()
    else:
        with open(tmp_path, "rb") as f:
            r = requests.post(
                "https://api.ocr.space/parse/image",
                files={"file": f},
                data={
                    "apikey": OCR_SPACE_API_KEY,
                    "language": "eng,pol,rus,ukr",
                    "OCREngine": 2,
                    "scale": True
                },
            )
        result = r.json()
        parsed = result.get("ParsedResults")
        if not parsed or not parsed[0].get("ParsedText"):
            st.error("❌ Nie udało się odczytać tekstu z pliku.")
            st.stop()
        text = parsed[0]["ParsedText"]

    try:
        qa_chain = load_qa_chain(text)
        st.success("✅ Plik został załadowany. Możesz teraz zadawać pytania!")
    except Exception as e:
        st.error(str(e))
        st.stop()
else:
    st.info("⬆️ Prześlij plik, aby rozpocząć.")
    st.stop()

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.chat_input("Zadaj pytanie dotyczące treści pliku...")

if user_input:
    st.session_state.history.append(("user", user_input))
    result = qa_chain.invoke(user_input)
    answer = result["result"]
    st.session_state.history.append(("bot", answer))

for role, message in st.session_state.history:
    with st.chat_message(role):
        st.write(message)

if st.checkbox("📚 Pokaż źródło odpowiedzi") and "result" in locals():
    for i, doc in enumerate(result.get("source_documents", []), start=1):
        st.markdown(f"**Źródło {i}:**\n{doc.page_content}")
