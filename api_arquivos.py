import os
from flask import Flask, request, jsonify

app = Flask(__name__)
PASTA_PROJETO = os.getcwd() # Usa a pasta atual do Termux

@app.route('/arquivos', methods=['GET'])
def listar_arquivos():
    try:
        arquivos = os.listdir(PASTA_PROJETO)
        return jsonify({"status": "sucesso", "arquivos": arquivos}), 200
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/ler', methods=['GET'])
def ler_arquivo():
    nome_arquivo = request.args.get('nome')
    caminho = os.path.join(PASTA_PROJETO, nome_arquivo)
    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        return jsonify({"status": "sucesso", "conteudo": conteudo}), 200
    return jsonify({"status": "erro", "mensagem": "Arquivo não encontrado"}), 404

@app.route('/salvar', methods=['POST'])
def salvar_arquivo():
    dados = request.json
    nome_arquivo = dados.get('nome')
    conteudo = dados.get('conteudo')
    
    caminho = os.path.join(PASTA_PROJETO, nome_arquivo)
    try:
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(conteudo)
        return jsonify({"status": "sucesso", "mensagem": f"Arquivo {nome_arquivo} salvo com sucesso!"}), 200
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
