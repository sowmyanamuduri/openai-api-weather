import os
from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")  # e.g. https://your-resource.openai.azure.com/
DEPLOYMENT_NAME = os.getenv("OPENAI_DEPLOYMENT_NAME")  # e.g. gpt-35-turbo

if not all([OPENAI_API_KEY, OPENAI_ENDPOINT, DEPLOYMENT_NAME]):
    raise Exception("Missing environment variables: OPENAI_API_KEY, OPENAI_ENDPOINT, or OPENAI_DEPLOYMENT_NAME")

HEADERS = {
    "api-key": OPENAI_API_KEY,
    "Content-Type": "application/json"
}

def query_openai(prompt):
    url = f"{OPENAI_ENDPOINT}openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version=2023-05-15"
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful weather assistant specialized in New York weather."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

def contains_new_york(text):
    # Case-insensitive check if user mentions New York or NYC
    return bool(re.search(r"\bnew york\b|\bnyc\b", text, re.IGNORECASE))

@app.route("/api/messages", methods=["POST"])
def messages():
    data = request.json
    user_message = data.get('text') or ""

    if contains_new_york(user_message):
        prompt = (
            f"Answer the user's weather question clearly and conversationally.\n"
            f"User's question about New York weather: {user_message}\n"
            "Provide weather info for current, past, and tomorrow if applicable."
        )
        try:
            answer = query_openai(prompt)
        except Exception as e:
            answer = f"Sorry, I had trouble getting the weather info: {str(e)}"
    else:
        answer = ("Sorry, this bot only provides weather information for New York City (NYC). "
                  "Please ask about New York's weather.")

    return jsonify({
        "type": "message",
        "text": answer
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
