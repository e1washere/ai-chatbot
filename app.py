import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
from pdf2image import convert_from_path
import pytesseract
import tempfile
import os

st.set_page_config(page_title="Czatbot AI dla Firm", layout="centered")

@st.cache_resource
def load_qa_chain(pdf_path):
    images = convert_from_path(pdf_path)
    docs = []

    for i, img in enumerate(images):
        text = pytesseract.image_to_string(img, lang="pol")
        if text.strip():
            docs.append(Document(page_content=text, metadata={"page": i + 1}))

    if not docs:
        raise ValueError("❌ Nie udało się odczytać tekstu z pliku PDF. Upewnij się, że zawiera on czytelny tekst.")

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

uploaded_file = st.file_uploader("📎 Prześlij plik PDF (zeskanowany dokument)", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        qa_chain = load_qa_chain(tmp_path)
        st.success("✅ Plik został załadowany. Możesz teraz zadawać pytania!")
    except ValueError as e:
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
