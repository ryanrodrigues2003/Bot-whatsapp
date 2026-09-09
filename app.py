import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

NUMERO_PERMITIDO = "559870166848"
EVOLUTION_API_URL = "https://evolution-api-ryan-wr3k.onrender.com"
EVOLUTION_API_KEY = "minhasenha123"
INSTANCE_NAME = "bot_whatsapp"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

historico_conversas = {}

@app.route('/', methods=['GET'])
def home():
    return "Servidor ativo!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("--- WEBHOOK RECEBIDO ---")
    print(data) # Imprime o JSON bruto no log do Render para sabermos o formato exato

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
            print(f"Número remetente detectado: {numero_remetente}")

            if numero_remetente != NUMERO_PERMITIDO:
                print(f"Número bloqueado pelo filtro: {numero_remetente}")
                return jsonify({"status": "ignored_unauthorized_number"}), 200

            message_content = msg_data.get('message', {})
            mensagem_texto = (
                message_content.get('conversation') or
                message_content.get('extendedTextMessage', {}).get('text')
            )

            if not mensagem_texto:
                print("Mensagem sem texto detectada.")
                return jsonify({"status": "ignored_non_text_message"}), 200

            print(f"Processando mensagem de {numero_remetente}: {mensagem_texto}")
            
            # Resposta direta temporária para teste de webhook
            url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
            headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}
            payload = {"number": numero_remetente, "text": "Recebido com sucesso pelo novo webhook!"}
            requests.post(url, json=payload, headers=headers, timeout=10)

    except Exception as e:
        print(f"Erro crítico no webhook: {e}")

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
