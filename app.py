import os
import requests
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

# Configurações obtidas das Variáveis de Ambiente
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "botwhatsapp123")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)

@app.route("/", methods=["GET"])
def home():
    return "Bot WhatsApp está online!", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # Validação do Webhook (GET - handshake com a Meta)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode and token:
            if mode == "subscribe" and token == VERIFY_TOKEN:
                print("WEBHOOK_VERIFIED")
                return challenge, 200
            else:
                return "Verification failed", 403
        return "Invalid verification request", 400

    # Recebimento de Mensagens (POST)
    elif request.method == "POST":
        data = request.json
        print("Recebido via POST:", data)

        try:
            # Extrai a mensagem enviada pelo usuário
            changes = data["entry"][0]["changes"][0]["value"]
            if "messages" in changes:
                msg_obj = changes["messages"][0]
                from_number = msg_obj["from"] # Número do usuário
                msg_body = msg_obj["text"]["body"] # Texto enviado

                print(f"Mensagem de {from_number}: {msg_body}")

                # Consulta a API da Groq para gerar a resposta da IA
                chat_completion = groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Você é um assistente virtual útil e amigável no WhatsApp."},
                        {"role": "user", "content": msg_body}
                    ],
                    model="llama3-8b-8192",
                )
                ai_response = chat_completion.choices[0].message.content

                # Envia a resposta de volta para o usuário pelo WhatsApp Cloud API
                send_whatsapp_message(from_number, ai_response)

        except Exception as e:
            print("Erro ao processar mensagem:", e)

        return jsonify({"status": "success"}), 200

def send_whatsapp_message(to_number, message_text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Resposta do envio WhatsApp:", response.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
