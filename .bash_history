pkg update && pkg upgrade -y
cat << 'EOF' > bot.py
import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Configuração da chave e da URL da xAI (Grok)
GROK_API_KEY = "SUA_CHAVE_GROK_AQUI"

client = OpenAI(
    api_key=GROK_API_KEY,
    base_url="https://api.x.ai/v1"
)

# Instruções do Bot (Base de conhecimento)
SYSTEM_PROMPT = """
Você é o assistente virtual do cliente no WhatsApp.
Responda de forma cortês, objetiva e humana.
Utilize o seguinte contexto para responder:
- Horário de atendimento: Segunda a Sexta, das 8h às 18h.
- Serviços: Instalação, suporte técnico e automação.
"""

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # Extrai a mensagem recebida
    user_message = data.get('message', '') if data else ''
    
    if not user_message:
        return jsonify({"status": "error", "reason": "No message provided"}), 400

    # Envia a mensagem do usuário para o Grok processar
    response = client.chat.completions.create(
        model="grok-beta",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )

    bot_reply = response.choices[0].message.content
    print(f"\n[Mensagem do Cliente]: {user_message}")
    print(f"[Resposta do Grok]: {bot_reply}\n")

    return jsonify({"status": "success", "reply": bot_reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

cat << 'EOF' > bot.py
import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Configuração da sua chave da xAI (Grok)
GROK_API_KEY = "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"

client = OpenAI(
    api_key=GROK_API_KEY,
    base_url="https://api.x.ai/v1"
)

# Instruções do Bot (Base de conhecimento)
SYSTEM_PROMPT = """
Você é o assistente virtual do cliente no WhatsApp.
Responda de forma cortês, objetiva e humana.
Utilize o seguinte contexto para responder:
- Horário de atendimento: Segunda a Sexta, das 8h às 18h.
- Serviços: Instalação, suporte técnico e automação.
"""

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # Extrai a mensagem recebida
    user_message = data.get('message', '') if data else ''
    
    if not user_message:
        return jsonify({"status": "error", "reason": "No message provided"}), 400

    # Envia a mensagem do usuário para o Grok processar
    response = client.chat.completions.create(
        model="grok-beta",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )

    bot_reply = response.choices[0].message.content
    print(f"\n[Mensagem do Cliente]: {user_message}")
    print(f"[Resposta do Grok]: {bot_reply}\n")

    return jsonify({"status": "success", "reply": bot_reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

python bot.py
ls
pkg install python -y
python bot.py
pip install flask openai requests
pkg install rust clang make -y
pip install --upgrade pip setuptools wheel
pip install flask requests openai
