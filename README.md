# 🧠 AI-Powered File Q&A Chatbot

A FastAPI app that uses OpenAI + LangChain to answer questions about uploaded files using vector search and GPT.

## 🚀 Features

- Upload any `.txt` file
- Embeds it using OpenAI
- Stores vectors in ChromaDB
- Ask questions via API (powered by GPT-3.5/4)

## 🛠️ Stack

- Python 3.12
- FastAPI
- LangChain
- Chroma
- OpenAI API

## 📦 Setup

1. Clone the repo
2. Create `.env` from `.env.example`
3. Run:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
