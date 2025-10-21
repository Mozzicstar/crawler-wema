import gradio as gr
import torch
from transformers import pipeline
from langchain_community.llms import HuggingFacePipeline
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

print("🔍 Loading vector store...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

# Load FAISS index
vectorstore = FAISS.load_local(
    "wema_index_faiss", 
    embeddings, 
    allow_dangerous_deserialization=True
)

print("🧠 Loading model...")
model_name = "facebook/blenderbot-400M-distill"
generator = pipeline(
    "text2text-generation",
    model=model_name,
    max_new_tokens=300,
    temperature=0.6,
    device_map="auto" if torch.cuda.is_available() else None,
)
llm = HuggingFacePipeline(pipeline=generator)

# Initialize memory
memory = ConversationBufferMemory(
    memory_key="chat_history", 
    return_messages=True,
    output_key="answer"
)

# Create the conversational retrieval chain
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    memory=memory,
    return_source_documents=True,
    verbose=True
)

def get_bot_response(message: str, history: list) -> str:
    """Generate response using RAG with conversation memory"""
    try:
        # The qa_chain automatically handles memory
        result = qa_chain({"question": message})
        answer = result["answer"]
        
        # Optional: Show source documents
        # sources = result.get("source_documents", [])
        # if sources:
        #     answer += "\n\n📚 Sources: " + ", ".join([doc.metadata.get("source", "N/A") for doc in sources[:2]])
        
        return answer
        
    except Exception as e:
        print(f"Error: {e}")
        return f"I encountered an error: {str(e)}. Please try again."

def respond(message, chat_history):
    """Handle chat interaction"""
    bot_message = get_bot_response(message, chat_history)
    chat_history.append((message, bot_message))
    return "", chat_history

def clear_memory():
    """Clear conversation memory"""
    global memory
    memory.clear()
    return None

# Create Gradio interface
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🏦 Wema Bank AI Assistant
    Ask me anything about Wema Bank services, products, and policies!
    
    💡 **This chatbot remembers your conversation** - feel free to ask follow-up questions!
    """)
    
    chatbot = gr.Chatbot(
        height=500,
        bubble_full_width=False,
        avatar_images=(None, "🤖"),
        show_label=False
    )
    
    with gr.Row():
        msg = gr.Textbox(
            placeholder="Type your question here...",
            show_label=False,
            scale=4,
            container=False
        )
        submit = gr.Button("Send", scale=1, variant="primary")
    
    with gr.Row():
        clear = gr.Button("Clear Chat & Memory", variant="secondary")
    
    gr.Examples(
        examples=[
            "How can I avoid phishing scams?",
            "What are Wema Bank's opening hours?",
            "How do I open a savings account?",
            "What mobile banking services do you offer?",
            "Tell me more about the last topic"  # Tests memory
        ],
        inputs=msg,
        label="Try these questions:"
    )
    
    gr.Markdown("""
    ### Features:
    - 🧠 **Conversational Memory**: Remembers context from previous messages
    - 🔍 **Semantic Search**: Finds relevant information from Wema Bank docs
    - 📚 **RAG Pipeline**: Retrieves context before generating answers
    """)
    
    # Event handlers
    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    submit.click(respond, [msg, chatbot], [msg, chatbot])
    clear.click(clear_memory, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)