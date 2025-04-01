from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import json, os

app = Flask(__name__)

ARQUIVO_CHAVES = "chaves.json"
ARQUIVO_LOGS = "logs.json"
ARQUIVO_ATUALIZACOES = "atualizacoes.json"
ARQUIVO_ALERTAS = "alertas.json"

def carregar(arquivo):
    if not os.path.exists(arquivo):
        with open(arquivo, "w") as f:
            json.dump({}, f)
    with open(arquivo, "r") as f:
        return json.load(f)

def salvar(arquivo, dados):
    with open(arquivo, "w") as f:
        json.dump(dados, f, indent=2)

# Chaves

@app.route("/criar_chave", methods=["POST"])
def criar_chave():
    dados = request.json
    chaves = carregar(ARQUIVO_CHAVES)
    chave = dados["chave"]
    if chave in chaves:
        return jsonify({"erro": "Chave já existe"}), 400
    chaves[chave] = {
        "validade": dados["validade"],
        "contato": dados["contato"],
        "limite": dados["limite"],
        "usos": [],
        "status": "ativa"
    }
    salvar(ARQUIVO_CHAVES, chaves)
    return jsonify({"mensagem": "Chave criada com sucesso"})

@app.route("/listar_chaves")
def listar_chaves():
    return jsonify(carregar(ARQUIVO_CHAVES))

@app.route("/excluir_chave", methods=["POST"])
def excluir_chave():
    dados = request.json
    chaves = carregar(ARQUIVO_CHAVES)
    if dados["chave"] in chaves:
        del chaves[dados["chave"]]
        salvar(ARQUIVO_CHAVES, chaves)
        return jsonify({"mensagem": "Chave excluída"})
    return jsonify({"erro": "Chave não encontrada"}), 404

@app.route("/editar_chave", methods=["POST"])
def editar_chave():
    dados = request.json
    chaves = carregar(ARQUIVO_CHAVES)
    chave = dados["chave"]
    if chave not in chaves:
        return jsonify({"erro": "Chave não encontrada"}), 404
    chaves[chave]["validade"] = dados["validade"]
    chaves[chave]["contato"] = dados["contato"]
    chaves[chave]["limite"] = dados["limite"]
    salvar(ARQUIVO_CHAVES, chaves)
    return jsonify({"mensagem": "Chave atualizada"})

@app.route("/desconectar_dispositivo", methods=["POST"])
def desconectar_dispositivo():
    dados = request.json
    chaves = carregar(ARQUIVO_CHAVES)
    chave = dados["chave"]
    dispositivo = dados["dispositivo"]
    if chave in chaves and dispositivo in chaves[chave]["usos"]:
        chaves[chave]["usos"].remove(dispositivo)
        salvar(ARQUIVO_CHAVES, chaves)
        return jsonify({"mensagem": "Dispositivo removido"})
    return jsonify({"erro": "Dispositivo ou chave não encontrados"}), 404

@app.route("/bloquear_chave", methods=["POST"])
def bloquear_chave():
    dados = request.json
    chaves = carregar(ARQUIVO_CHAVES)
    chave = dados["chave"]
    status = dados["status"]
    if chave in chaves:
        chaves[chave]["status"] = status
        salvar(ARQUIVO_CHAVES, chaves)
        return jsonify({"mensagem": f"Chave {status}"})
    return jsonify({"erro": "Chave não encontrada"}), 404

@app.route("/resetar_chave", methods=["POST"])
def resetar_chave():
    dados = request.json
    chaves = carregar(ARQUIVO_CHAVES)
    chave = dados["chave"]
    if chave in chaves:
        chaves[chave]["usos"] = []
        if dados.get("nova_validade"):
            chaves[chave]["validade"] = dados["nova_validade"]
        salvar(ARQUIVO_CHAVES, chaves)
        return jsonify({"mensagem": "Chave resetada"})
    return jsonify({"erro": "Chave não encontrada"}), 404

# Atualizações

@app.route("/lancar_atualizacao", methods=["POST"])
def lancar_atualizacao():
    atualizacoes = carregar(ARQUIVO_ATUALIZACOES)
    nova = request.json
    nova["data"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    nova["id"] = str(len(atualizacoes) + 1)
    atualizacoes[nova["id"]] = nova
    salvar(ARQUIVO_ATUALIZACOES, atualizacoes)
    return jsonify({"mensagem": "Atualização lançada"})

@app.route("/listar_atualizacoes")
def listar_atualizacoes():
    return jsonify(carregar(ARQUIVO_ATUALIZACOES))

@app.route("/editar_atualizacao", methods=["POST"])
def editar_atualizacao():
    dados = request.json
    atualizacoes = carregar(ARQUIVO_ATUALIZACOES)
    id = dados["id"]
    if id in atualizacoes:
        atualizacoes[id]["descricao"] = dados["descricao"]
        salvar(ARQUIVO_ATUALIZACOES, atualizacoes)
        return jsonify({"mensagem": "Atualização editada"})
    return jsonify({"erro": "ID não encontrado"}), 404

@app.route("/remover_atualizacao", methods=["POST"])
def remover_atualizacao():
    dados = request.json
    atualizacoes = carregar(ARQUIVO_ATUALIZACOES)
    id = dados["id"]
    if id in atualizacoes:
        del atualizacoes[id]
        salvar(ARQUIVO_ATUALIZACOES, atualizacoes)
        return jsonify({"mensagem": "Atualização removida"})
    return jsonify({"erro": "ID não encontrado"}), 404

# Segurança

@app.route("/registrar_log", methods=["POST"])
def registrar_log():
    logs = carregar(ARQUIVO_LOGS)
    novo = request.json
    novo["data"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    logs[str(len(logs)+1)] = novo
    salvar(ARQUIVO_LOGS, logs)
    return jsonify({"mensagem": "Log registrado"})

@app.route("/ver_logs")
def ver_logs():
    return jsonify(carregar(ARQUIVO_LOGS))

# Alertas

@app.route("/enviar_alerta", methods=["POST"])
def enviar_alerta():
    alertas = carregar(ARQUIVO_ALERTAS)
    dados = request.json
    alertas[dados["chave"]] = {
        "mensagem": dados["mensagem"],
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    salvar(ARQUIVO_ALERTAS, alertas)
    return jsonify({"mensagem": "Alerta enviado"})

@app.route("/ver_alerta/<chave>")
def ver_alerta(chave):
    alertas = carregar(ARQUIVO_ALERTAS)
    return jsonify(alertas.get(chave, {}))

# Estatísticas

@app.route("/estatisticas_cliente/<chave>")
def estatisticas_cliente(chave):
    chaves = carregar(ARQUIVO_CHAVES)
    if chave not in chaves:
        return jsonify({"erro": "Chave não encontrada"}), 404
    return jsonify({
        "dispositivos": len(chaves[chave]["usos"]),
        "limite": chaves[chave]["limite"],
        "validade": chaves[chave]["validade"],
        "status": chaves[chave].get("status", "ativa")
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
