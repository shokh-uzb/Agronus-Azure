from flask import Flask, request, jsonify
import joblib
import numpy as np
from flask_cors import CORS
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global store for user sessions (In-memory)
# Key: User Identifier (e.g., IP), Value: Dict of data
user_sessions = {}

# Load the model
model = None
try:
    model_path = os.path.join(os.path.dirname(__file__), "crop_recommendation_model_v1.pkl")
    model = joblib.load(model_path)
    logger.info("Model Loaded Successfully!")
except Exception as e:
    logger.error(f"Error loading model: {e}")

def get_session_id():
    # Simple session ID based on IP for local usage. 
    # In production, use a proper session cookie or token.
    return request.remote_addr

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
        
        # Predict using the model
        prediction = model.predict(features).tolist()
        predicted_crop = prediction[0]

        logger.info(f"Prediction for {session_id}: {predicted_crop}")

        # Store in session
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
        
        # Retrieve context from session or use defaults
        features = session_data.get("features", [0]*7)
        predicted_crop = session_data.get("prediction", "Unknown")
        
        n, p, k, temperature, humidity, ph, rainfall = features

        # Formatting the inputs with labels
        formatted_inputs = (
            f"N: {n}, P: {p}, K: {k}, "
            f"Temperature: {temperature}, Humidity: {humidity}, "
            f"pH: {ph}, Rainfall: {rainfall}"
        )

        # Creating the final prompt string
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
        # Format explicitly to match what frontend might expect if it relies on index access, 
        # but for now returning the structured dict is cleaner. 
        # If legacy frontend breaks, we can adapt.
        return jsonify({"latest_prediction": data})
    else:
        return jsonify({"error": "No prediction available"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5001)