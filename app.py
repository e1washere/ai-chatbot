import streamlit as st
import requests
import tempfile
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
import os

st.set_page_config(page_title="Czatbot AI dla Firm", layout="centered")

OCR_SPACE_API_KEY = st.secrets["OCR_SPACE_API_KEY"]

@st.cache_resource
def load_qa_chain(text):
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

def extract_text_via_ocr(path):
    with open(path, "rb") as f:
        r = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": f},
            data={
                "apikey": OCR_SPACE_API_KEY,
                "language": "pol,eng,ukr,rus",
                "isOverlayRequired": False,
                "scale": True,
                "OCREngine": 2
            }
        )
    result = r.json()
    parsed = result.get("ParsedResults")
    if not parsed or not parsed[0].get("ParsedText"):
        return ""
    return parsed[0]["ParsedText"]

st.title("🤖 Czatbot AI z Twoich Dokumentów")

uploaded_file = st.file_uploader("📎 Prześlij plik PDF lub TXT", type=["pdf","txt"])

if not uploaded_file:
    st.info("⬆️ Prześlij plik, aby rozpocząć.")
    st.stop()

suffix = ".txt" if uploaded_file.type=="text/plain" else ".pdf"
with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
    tmp.write(uploaded_file.read())
    tmp_path = tmp.name

if uploaded_file.type=="text/plain":
    text = open(tmp_path, "r", encoding="utf-8").read()
else:
    text = ""
    try:
        loader = PyPDFLoader(tmp_path)
        docs = loader.load()
        text = "\n".join([d.page_content for d in docs if d.page_content.strip()])
    except:
        text = ""
    if not text:
        text = extract_text_via_ocr(tmp_path)

if not text.strip():
    st.error("❌ Nie udało się odczytać tekstu z pliku.")
    st.stop()

qa_chain = load_qa_chain(text)
st.success("✅ Plik został załadowany. Możesz teraz zadawać pytania!")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.chat_input("Zadaj pytanie dotyczące treści pliku...")

if user_input:
    st.session_state.history.append(("user", user_input))
    result = qa_chain.invoke(user_input)
    st.session_state.history.append(("bot", result["result"]))

for role, message in st.session_state.history:
    with st.chat_message(role):
        st.write(message)

if st.checkbox("📚 Pokaż źródło odpowiedzi") and "result" in locals():
    for i, doc in enumerate(result.get("source_documents", []), start=1):
        st.markdown(f"**Źródło {i}:**\n{doc.page_content}")
