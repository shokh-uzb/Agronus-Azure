# Agronus Backend - Combined API Server for Azure Deployment
import os
import json
import joblib
import numpy as np
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

if not AZURE_OPENAI_API_KEY:
    logger.warning("AZURE_OPENAI_API_KEY not found in environment variables!")
if not AZURE_OPENAI_ENDPOINT:
    logger.warning("AZURE_OPENAI_ENDPOINT not found in environment variables!")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global store for user sessions (In-memory)
user_sessions = {}

# Load the ML model
model = None
try:
    model_path = os.path.join(os.path.dirname(__file__), "crop_recommendation_model_v1.pkl")
    model = joblib.load(model_path)
    logger.info("ML Model Loaded Successfully!")
except Exception as e:
    logger.error(f"Error loading ML model: {e}")

# Initialize embedding model and vector store
try:
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = Chroma(persist_directory="./agronus_vdb", embedding_function=embedding_model)
    logger.info("Vector store loaded successfully!")
except Exception as e:
    logger.error(f"Error loading vector store: {e}")
    vector_store = None

# Initialize Azure OpenAI Model
llm = None
try:
    if AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT:
        llm = AzureChatOpenAI(
            azure_deployment=AZURE_OPENAI_DEPLOYMENT,
            api_version="2025-01-01-preview",
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            temperature=0.7
        )
        logger.info("Azure OpenAI initialized successfully!")
except Exception as e:
    logger.error(f"Error initializing Azure OpenAI: {e}")

def get_session_id():
    return request.remote_addr

def retrieve_context(query, top_k=3):
    """Retrieves relevant knowledge from ChromaDB."""
    if not vector_store:
        return "No knowledge base available."
    results = vector_store.similarity_search(query, k=top_k)
    return "\n\n".join([doc.page_content for doc in results]) if results else "No relevant information found."

# ============ PREDICTION ENDPOINTS ============

@app.route("/predict", methods=["POST"])
def predict():
    try:
        if not model:
            return jsonify({"error": "Model not loaded"}), 500

        data = request.json
        session_id = get_session_id()
        
        features_array = [
            float(data.get("nitrogen", 0)),
            float(data.get("phosphorus", 0)),
            float(data.get("potassium", 0)),
            float(data.get("temperature", 0)),
            float(data.get("humidity", 0)),
            float(data.get("pH_Level", 0)),
            float(data.get("rainfall", 0))
        ]
       
        features = np.array(features_array).reshape(1, -1)
        prediction = model.predict(features).tolist()
        predicted_crop = prediction[0]

        logger.info(f"Prediction for {session_id}: {predicted_crop}")

        user_sessions[session_id] = {
            "features": features_array,
            "prediction": predicted_crop,
            "latest_query": None
        }

        return jsonify({
            "message": "Prediction made successfully", 
            "prediction": prediction,
            "crop": predicted_crop
        })

    except Exception as e:
        logger.error(f"Prediction Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/userQuery", methods=["POST"])
def userQuery():
    try:
        data = request.json
        query = data.get("text", "")
        session_id = get_session_id()
        
        session_data = user_sessions.get(session_id, {})
        features = session_data.get("features", [0]*7)
        predicted_crop = session_data.get("prediction", "Unknown")
        
        n, p, k, temperature, humidity, ph, rainfall = features

        formatted_inputs = (
            f"N: {n}, P: {p}, K: {k}, "
            f"Temperature: {temperature}, Humidity: {humidity}, "
            f"pH: {ph}, Rainfall: {rainfall}"
        )

        prompt = (
            f"Retrieve precise agricultural recommendations from the vector database based on the user inputs: "
            f"{formatted_inputs}. The response should be strictly aligned with the predicted model output: {predicted_crop} "
            f"and should also address the user's additional query: {query}. "
            f"The answer must be clear, well-structured, and formatted for readability. "
            f"Provide insights on the best irrigation practices suitable for the crop, considering soil type, "
            f"climate, and water requirements. Include secondary crop recommendations that improve soil health "
            f"and productivity. Specify the appropriate fertilizers, their dosage, and application frequency "
            f"for optimal growth. Offer detailed care and maintenance tips, including pest control methods, "
            f"pruning techniques, and disease prevention strategies. Additionally, provide any other relevant "
            f"agronomic insights that enhance crop yield and sustainability."
        )

        logger.info(f"Generated prompt for {session_id}")
        
        return jsonify({ "prompt": prompt })

    except Exception as e:
        logger.error(f"UserQuery Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/get-latest-prediction", methods=["GET"])
def get_latest_prediction():
    session_id = get_session_id()
    data = user_sessions.get(session_id)
    
    if data:
        return jsonify({"latest_prediction": data})
    else:
        return jsonify({"error": "No prediction available"}), 404

# ============ CHAT ENDPOINT (RAG) ============

@app.route("/chat", methods=["POST"])
def chat():
    """Handles chat requests from frontend."""
    logger.info("Chat request received!")
    data = request.json
    
    user_query = data.get("prompt")
    
    if not user_query:
        return jsonify({"error": "User query is required!"}), 400
    
    if not llm:
        return jsonify({"error": "AI service not configured"}), 500
    
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
        logger.error(f"AI API Error: {e}")
        return jsonify({"error": "AI API Error", "details": str(e)}), 500

# ============ HEALTH CHECK ============

@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Agronus API",
        "model_loaded": model is not None,
        "vector_store_loaded": vector_store is not None,
        "llm_configured": llm is not None
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
