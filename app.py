import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
# Número permitido para testes (apenas números: DDI + DDD + Número)
NUMERO_PERMITIDO = "559870166848"

# Chave e URL da Evolution API
EVOLUTION_API_URL = "https://evolution-api-ryan-wr3k.onrender.com"
EVOLUTION_API_KEY = "minhasenha123"
INSTANCE_NAME = "bot_whatsapp"

# Chave da API do Groq (configurada nas variáveis de ambiente do Render)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


def enviar_mensagem_whatsapp(numero, texto):
    """Envia uma mensagem de texto de volta via Evolution API."""
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
        print(f"Status do envio para {numero}: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar mensagem via Evolution API: {e}")
        return None


def obter_resposta_groq(mensagem_usuario):
    """Gera uma resposta usando a API do Groq com Llama 3."""
    if not GROQ_API_KEY:
        print("Erro: GROQ_API_KEY não configurada nas variáveis de ambiente.")
        return "Desculpe, meu sistema de inteligência artificial não está configurado corretamente."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "Você é um assistente virtual prestativo, educado e conciso que responde mensagens no WhatsApp."
            },
            {
                "role": "user",
                "content": mensagem_usuario
            }
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            print(f"Erro Groq API ({response.status_code}): {response.text}")
            return "Ocorreu um erro ao processar sua solicitação."
    except Exception as e:
        print(f"Erro na requisição ao Groq: {e}")
        return "Desculpe, tive um problema ao tentar responder agora."


@app.route('/', methods=['GET'])
def home():
    return "Servidor do Bot WhatsApp ativo!", 200


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    if not data:
        return jsonify({"status": "error", "message": "Nenhum dado recebido"}), 400

    try:
        event = data.get('event')

        # Processa apenas o evento de nova mensagem recebida
        if event == 'messages.upsert':
            msg_data = data.get('data', {})
            key = msg_data.get('key', {})

            # 1. Ignora mensagens enviadas pelo próprio bot
            if key.get('fromMe'):
                return jsonify({"status": "ignored_from_me"}), 200

            # 2. Extrai o número do remetente
            remote_jid = key.get('remoteJid', '')
            numero_remetente = remote_jid.split('@')[0]

            # 3. FILTRO DE SEGURANÇA: Permite apenas o número configurado
            if numero_remetente != NUMERO_PERMITIDO:
                print(f"Mensagem de {numero_remetente} ignorada pelo filtro.")
                return jsonify({"status": "ignored_unauthorized_number"}), 200

            # 4. Extrai o texto da mensagem
            message_content = msg_data.get('message', {})
            mensagem_texto = (
                message_content.get('conversation') or
                message_content.get('extendedTextMessage', {}).get('text')
            )

            if not mensagem_texto:
                print("Mensagem recebida sem conteúdo de texto legível.")
                return jsonify({"status": "ignored_non_text_message"}), 200

            print(f"Mensagem AUTORIZADA de {numero_remetente}: {mensagem_texto}")

            # 5. Processa com o Groq e envia a resposta de volta
            resposta_ai = obter_resposta_groq(mensagem_texto)
            enviar_mensagem_whatsapp(numero_remetente, resposta_ai)

    except Exception as e:
        print(f"Erro ao processar dados no webhook: {e}")

    return jsonify({"status": "success"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
