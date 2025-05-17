import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

load_dotenv()

loader = TextLoader("example.txt")
docs = loader.load()

db = Chroma.from_documents(docs, OpenAIEmbeddings())
retriever = db.as_retriever()

qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(),
    retriever=retriever,
    chain_type="stuff",  
    return_source_documents=True
)

question = "Summarize the following content:"
result = qa.invoke(question)

print("\n📌 Question:", question)
print("🧠 Answer:", result['result'])

print("\n📚 Source Documents Used:")
for i, doc in enumerate(result["source_documents"], start=1):
    print(f"\n--- Document {i} ---")
    print(doc.page_content)
