import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

load_dotenv()  # Loads variables from .env into environment
api_key = os.getenv("OPENAI_API_KEY")

# Now pass api_key where needed, or:
os.environ["OPENAI_API_KEY"] = api_key

# 📄 Load your text file
loader = TextLoader("example.txt")
docs = loader.load()

# 🧠 Create vector embeddings and store in ChromaDB
db = Chroma.from_documents(docs, OpenAIEmbeddings())
retriever = db.as_retriever()

# 🧩 Create a RetrievalQA chain (using "stuff" to give GPT full context)
qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(),
    retriever=retriever,
    chain_type="stuff",  # Stuff all content into GPT for small files
    return_source_documents=True
)

# 💬 Ask a question
question = "Summarize the following content:"
result = qa.invoke(question)

# 🖨️ Output the result
print("\n📌 Question:", question)
print("🧠 Answer:", result['result'])

# 🔎 Show the source documents (debug or transparency)
print("\n📚 Source Documents Used:")
for i, doc in enumerate(result["source_documents"], start=1):
    print(f"\n--- Document {i} ---")
    print(doc.page_content)
