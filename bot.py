import os
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

# Pega a chave das variáveis de ambiente
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@app.route('/', methods=['GET'])
def home():
    return "Bot WhatsApp está rodando!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    message = data.get("message", "")
    
    if not message:
        return jsonify({"error": "Mensagem vazia"}), 400

    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": message}]
    )

    reply = completion.choices[0].message.content
    return jsonify({"response": reply}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
