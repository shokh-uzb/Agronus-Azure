import os
import json
from flask import Flask, request, jsonify
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY not found in .env file!")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow all origins
# Embedding model and vector store setup
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vector_store = Chroma(persist_directory="./agronus_vdb", embedding_function=embedding_model)

# Initialize Groq Model
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=GROQ_API_KEY,
    temperature=0.7
)

def retrieve_context(query, top_k=3):
    """Retrieves relevant knowledge from ChromaDB."""
    results = vector_store.similarity_search(query, k=top_k)
    return "\n\n".join([doc.page_content for doc in results]) if results else "No relevant information found."

@app.route("/chat", methods=["POST"])
def chat():
    """Handles chat requests from frontend."""
    print("Chat request received!")
    data = request.json
    
    user_query = data.get("prompt")
    
    if not user_query:
        return jsonify({"error": "User query is required!"}), 400
    
    # Retrieve knowledge
    context = retrieve_context(user_query)
    
    
    # Modify prompt to act as an agriculture expert
    modified_prompt = f"""
    Act like an agriculture expert and AI assistant for me. Give me only suitable information.
    User Query: {user_query}
    
    ### Retrieved Knowledge:  
    {context}
    """
    
    try:
        response = llm.invoke(modified_prompt)
        return jsonify({"rag_response": response.content})
    except Exception as e:
        return jsonify({"error": "AI API Error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True,port=5002)
