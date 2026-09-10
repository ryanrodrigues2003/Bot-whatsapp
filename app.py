import os
import logging
import requests
import threading
from datetime import datetime, timedelta
from collections import OrderedDict
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from jsonschema import validate, ValidationError

load_dotenv()

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "https://evolution-api-ryan.onrender.com").strip()
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "171EF9DE-6B4B-4EC1-A3F9-F777669EE6F9").strip()
INSTANCE_NAME = os.getenv("INSTANCE_NAME", "bot_whatsapp").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "Gsk_eC6rJOD2pwU81eBR7ivAWGdyb3FYFJXcpEsylocRLma0zZfW0z90").strip()

class HistoricoConversas:
    def __init__(self, max_usuarios=500, max_mensagens=10, ttl_minutos=30):
        self.dados = OrderedDict()
        self.max_usuarios = max_usuarios
        self.max_mensagens = max_mensagens
        self.ttl = timedelta(minutes=ttl_minutos)
        self.lock = threading.RLock()
    
    def _limpar_expirados(self):
        agora = datetime.now()
        expirados = [k for k, v in self.dados.items() if agora - v['ultima_atividade'] > self.ttl]
        for k in expirados:
            del self.dados[k]
    
    def adicionar_mensagem(self, numero, role, content):
        with self.lock:
            self._limpar_expirados()
            if numero not in self.dados and len(self.dados) >= self.max_usuarios:
                self.dados.popitem(last=False)
            
            if numero not in self.dados:
                self.dados[numero] = {
                    'mensagens': [],
                    'ultima_atividade': datetime.now()
                }
            
            self.dados[numero]['mensagens'].append({"role": role, "content": content})
            self.dados[numero]['ultima_atividade'] = datetime.now()
            
            if len(self.dados[numero]['mensagens']) > self.max_mensagens:
                self.dados[numero]['mensagens'] = self.dados[numero]['mensagens'][-self.max_mensagens:]
    
    def obter_historico(self, numero):
        with self.lock:
            return self.dados.get(numero, {}).get('mensagens', []).copy()

historico = HistoricoConversas()

WEBHOOK_SCHEMA = {
    "type": "object",
    "properties": {
        "event": {"type": "string"},
        "data": {"type": "object"}
    },
    "required": ["event", "data"]
}

def enviar_mensagem_whatsapp(numero, texto):
    if not EVOLUTION_API_URL or not EVOLUTION_API_KEY:
        logger.error("Evolution API não configurada")
        return None
    
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"number": numero, "text": texto}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        return None

def obter_resposta_groq(numero_remetente, mensagem_usuario):
    if not GROQ_API_KEY:
        return "Erro: GROQ_API_KEY não configurada no ambiente."
    
    historico.adicionar_mensagem(numero_remetente, "user", mensagem_usuario)
    messages_historico = historico.obter_historico(numero_remetente)
    
    system_prompt = {
        "role": "system",
        "content": (
            "Você é o Mario, atendente virtual simpático da 'Pizzaria Bella Italia'.\n"
            "CARDÁPIO:\n"
            "- Média (R$ 40), Grande (R$ 50), Gigante (R$ 65).\n"
            "- Sabores: Calabresa, Mussarela, Margherita, Frango c/ Catupiry.\n"
            "- Especiais (+ R$ 5): Quatro Queijos, Bacon c/ Cheddar, Portuguesa.\n"
            "- Bebidas: Coca 2L (R$ 12), Guaraná 2L (R$ 10), Água (R$ 4).\n"
            "- Taxa de entrega: R$ 7,00.\n"
            "Guie o pedido passo a passo até o resumo final."
        )
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [system_prompt] + messages_historico,
        "temperature": 0.6
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            timeout=15
        )
        if response.status_code == 200:
            resposta_ia = response.json()["choices"][0]["message"]["content"]
            historico.adicionar_mensagem(numero_remetente, "assistant", resposta_ia)
            return resposta_ia
        return "Desculpe, tive um problema técnico ao processar a resposta."
    except Exception as e:
        logger.error(f"Erro na Groq: {e}")
        return "Desculpe, tente novamente em instantes."

def processar_background(numero_remetente, mensagem_texto):
    resposta_ai = obter_resposta_groq(numero_remetente, mensagem_texto)
    if resposta_ai:
        enviar_mensagem_whatsapp(numero_remetente, resposta_ai)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "online", "bot": "Pizzaria Bella Italia"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        validate(instance=data, schema=WEBHOOK_SCHEMA)
        
        if data.get('event') != 'messages.upsert':
            return jsonify({"status": "ignored"}), 200
        
        msg_data = data.get('data', {})
        key = msg_data.get('key', {})
        
        if key.get('fromMe'):
            return jsonify({"status": "ignored_from_me"}), 200
        
        remote_jid = key.get('remoteJid', '')
        numero_remetente = ''.join(filter(str.isdigit, remote_jid.split('@')[0]))
        
        message_content = msg_data.get('message', {})
        mensagem_texto = (
            message_content.get('conversation') or
            message_content.get('extendedTextMessage', {}).get('text', '')
        )
        
        if not mensagem_texto or not numero_remetente:
            return jsonify({"status": "ignored_no_text"}), 200
        
        t = threading.Thread(
            target=processar_background,
            args=(numero_remetente, mensagem_texto),
            daemon=True
        )
        t.start()
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Erro webhook: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
