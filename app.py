import streamlit as st
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
import os
from dotenv import load_dotenv

st.set_page_config(page_title="AI Chatbot Demo", layout="centered")

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

@st.cache_resource

def load_qa_chain():
    loader = TextLoader("example.txt")
    docs = loader.load()
    db = Chroma.from_documents(docs, OpenAIEmbeddings())
    retriever = db.as_retriever()
    print("Loaded docs:", docs)
    qa = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(),
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True
    )
    return qa

qa_chain = load_qa_chain()

st.title("🤖 AI Chatbot from Your Document")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.chat_input("Ask a question about the content...")

if user_input:
    st.session_state.history.append(("user", user_input))
    result = qa_chain.invoke(user_input)
    answer = result['result']
    st.session_state.history.append(("bot", answer))

for role, message in st.session_state.history:
    with st.chat_message(role):
        st.write(message)

if st.checkbox("Show source content") and "result" in locals():
    for i, doc in enumerate(result.get("source_documents", []), start=1):
        st.markdown(f"**Source {i}:**\n{doc.page_content}")
