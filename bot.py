import os
import requests
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@app.route('/', methods=['GET'])
def home():
    return "Bot WhatsApp Oficial está rodando!", 200

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    # Validação do Webhook exigida pela Meta
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Token inválido", 403
    return "Requisição inválida", 400

@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.get_json() or {}
    
    try:
        # Extrai a mensagem recebida do payload da Meta
        entry = data.get("entry", [])
        if not entry:
            return jsonify({"status": "ignored"}), 200

        changes = entry[0].get("changes", [])
        if not changes:
            return jsonify({"status": "ignored"}), 200

        value = changes[0].get("value", {})
        messages = value.get("messages", [])

        if messages:
            msg = messages[0]
            from_number = msg.get("from") # Número de quem mandou a mensagem
            msg_body = msg.get("text", {}).get("body", "") # Texto da mensagem

            if msg_body:
                # 1. Gera resposta usando a Groq
                completion = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[{"role": "user", "content": msg_body}]
                )
                bot_reply = completion.choices[0].message.content

                # 2. Envia a resposta de volta pelo WhatsApp Cloud API
                headers = {
                    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "to": from_number,
                    "text": {"body": bot_reply}
                }
                requests.post(
                    f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages",
                    json=payload,
                    headers=headers
                )

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
