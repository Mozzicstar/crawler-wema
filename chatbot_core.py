# chatbot_core.py
import torch
from transformers import pipeline
from langchain_community.llms import HuggingFacePipeline
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

print("🔍 Loading vector store...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.load_local("wema_index_faiss/index.faiss", embeddings, allow_dangerous_deserialization=True)

print("🧠 Loading model...")
model_name = "facebook/blenderbot-400M-distill"
generator = pipeline(
    "text-generation",
    model=model_name,
    dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None,
    max_new_tokens=300,
    temperature=0.6,
)
llm = HuggingFacePipeline(pipeline=generator)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    memory=memory
)

def get_bot_response(query: str) -> str:
    result = qa_chain({"question": query})
    return result["answer"]
