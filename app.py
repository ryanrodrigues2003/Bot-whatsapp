import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

NUMERO_PERMITIDO = "559870166848"
EVOLUTION_API_URL = "https://evolution-api-ryan-wr3k.onrender.com"
EVOLUTION_API_KEY = "minhasenha123"
INSTANCE_NAME = "bot_whatsapp"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


def enviar_mensagem_whatsapp(numero, texto):
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "number": numero,
        "text": texto
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status envio WhatsApp: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"Erro envio WhatsApp: {e}")
        return None


def obter_resposta_groq(mensagem_usuario):
    if not GROQ_API_KEY:
        print("ERRO: GROQ_API_KEY não foi configurada nas variáveis de ambiente do Render.")
        return "Erro interno: Chave Groq não configurada."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": "Você é um assistente virtual prestativo e carinhoso no WhatsApp."},
            {"role": "user", "content": mensagem_usuario}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"Status Groq: {response.status_code}")
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"Erro Resposta Groq: {response.text}")
            return "Ocorreu um erro ao processar sua solicitação."
    except Exception as e:
        print(f"Exceção Groq: {e}")
        return "Desculpe, tive um problema ao tentar responder agora."


@app.route('/', methods=['GET'])
def home():
    return "Servidor ativo!", 200


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error"}), 400

    try:
        event = data.get('event')
        if event == 'messages.upsert':
            msg_data = data.get('data', {})
            key = msg_data.get('key', {})

            if key.get('fromMe'):
                return jsonify({"status": "ignored_from_me"}), 200

            remote_jid = key.get('remoteJid', '')
            numero_remetente = remote_jid.split('@')[0]

            if numero_remetente != NUMERO_PERMITIDO:
                return jsonify({"status": "ignored_unauthorized_number"}), 200

            message_content = msg_data.get('message', {})
            mensagem_texto = (
                message_content.get('conversation') or
                message_content.get('extendedTextMessage', {}).get('text')
            )

            if not mensagem_texto:
                return jsonify({"status": "ignored_non_text_message"}), 200

            print(f"Mensagem recebida de {numero_remetente}: {mensagem_texto}")
            resposta_ai = obter_resposta_groq(mensagem_texto)
            enviar_mensagem_whatsapp(numero_remetente, resposta_ai)

    except Exception as e:
        print(f"Erro no webhook: {e}")

    return jsonify({"status": "success"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
