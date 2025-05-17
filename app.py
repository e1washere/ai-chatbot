import streamlit as st
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
import os
from dotenv import load_dotenv

st.set_page_config(page_title="Czatbot AI dla Firm", layout="centered")

load_dotenv()

@st.cache_resource
def load_qa_chain(file_path):
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path)

    docs = loader.load()

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
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.read())
    qa_chain = load_qa_chain(uploaded_file.name)
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