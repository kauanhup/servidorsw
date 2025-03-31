from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Base simples de chaves (em memória)
chaves = {}
versao_atual = "1.0"
atualizacoes = {}

@app.route('/')
def home():
    return jsonify({"mensagem": "Servidor SW EXTRATOR ativo!"})

@app.route('/criar-chave', methods=['POST'])
def criar_chave():
    dados = request.get_json()
    chave = dados.get("chave")
    tipo = dados.get("tipo")  # "horas", "dias", "vitalicio"
    valor = int(dados.get("valor", 1))

    if chave in chaves:
        return jsonify({"erro": "Chave já existe!"}), 400

    if tipo == "horas":
        expira = datetime.now() + timedelta(hours=valor)
    elif tipo == "dias":
        expira = datetime.now() + timedelta(days=valor)
    elif tipo == "vitalicio":
        expira = None
    else:
        return jsonify({"erro": "Tipo inválido!"}), 400

    chaves[chave] = {
        "expira": expira.isoformat() if expira else "vitalicio",
        "criado": datetime.now().isoformat()
    }
    return jsonify({"mensagem": "Chave criada com sucesso!"})

@app.route('/verificar-chave', methods=['POST'])
def verificar_chave():
    dados = request.get_json()
    chave = dados.get("chave")

    if chave not in chaves:
        return jsonify({"valida": False, "mensagem": "Chave inválida!"})

    info = chaves[chave]
    if info["expira"] == "vitalicio":
        return jsonify({"valida": True, "mensagem": "Licença vitalícia"})

    expira = datetime.fromisoformat(info["expira"])
    if datetime.now() <= expira:
        return jsonify({"valida": True, "expira": info["expira"]})
    else:
        return jsonify({"valida": False, "mensagem": "Licença expirada!"})

@app.route('/listar-chaves')
def listar_chaves():
    return jsonify(chaves)

@app.route('/excluir-chave', methods=['POST'])
def excluir_chave():
    dados = request.get_json()
    chave = dados.get("chave")

    if chave in chaves:
        del chaves[chave]
        return jsonify({"mensagem": "Chave removida com sucesso!"})
    else:
        return jsonify({"erro": "Chave não encontrada!"}), 404

@app.route('/atualizacao', methods=['GET', 'POST'])
def atualizacao():
    global versao_atual
    if request.method == 'POST':
        dados = request.get_json()
        versao = dados.get("versao")
        link = dados.get("link")

        versao_atual = versao
        atualizacoes[versao] = link
        return jsonify({"mensagem": "Atualização publicada com sucesso!"})
    else:
        return jsonify({"versao": versao_atual, "link": atualizacoes.get(versao_atual)})

if __name__ == '__main__':
    app.run()
