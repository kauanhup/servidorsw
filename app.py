from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os, json

app = Flask(__name__)
ARQUIVO_CHAVES = "chaves.json"
ARQUIVO_LOGS = "logs.json"
ARQUIVO_ATUALIZACOES = "atualizacoes.json"

def carregar(caminho):
    if not os.path.exists(caminho):
        return {}
    with open(caminho, "r") as f:
        return json.load(f)

def salvar(caminho, dados):
    with open(caminho, "w") as f:
        json.dump(dados, f, indent=2)

# Criação automática dos arquivos se não existirem
for arquivo in [ARQUIVO_CHAVES, ARQUIVO_LOGS, ARQUIVO_ATUALIZACOES]:
    if not os.path.exists(arquivo):
        salvar(arquivo, {})

@app.route("/")
def index():
    return "Servidor SW Online"

# ──────────────── 1. CHAVES ────────────────

@app.route("/criar", methods=["POST"])
def criar():
    data = request.json
    chave = data["chave"]
    contato = data["contato"]
    limite = int(data["limite"])
    tipo = data["tipo"]
    duracao = int(data["duracao"])

    chaves = carregar(ARQUIVO_CHAVES)
    if chave in chaves:
        return jsonify({"erro": "Chave já existe!"}), 400

    if tipo == "horas":
        validade = (datetime.now() + timedelta(hours=duracao)).strftime("%Y-%m-%d %H:%M:%S")
    elif tipo == "dias":
        validade = (datetime.now() + timedelta(days=duracao)).strftime("%Y-%m-%d %H:%M:%S")
    else:
        validade = "vitalicio"

    chaves[chave] = {
        "validade": validade,
        "contato": contato,
        "limite": limite,
        "usos": [],
        "bloqueada": False
    }
    salvar(ARQUIVO_CHAVES, chaves)
    return jsonify({"sucesso": True})

@app.route("/listar")
def listar():
    return jsonify(carregar(ARQUIVO_CHAVES))

@app.route("/clientes/estatisticas", methods=["GET"])
def estatisticas_cliente():
    chave = request.args.get("chave")
    chaves = carregar(ARQUIVO_CHAVES)
    if chave in chaves:
        info = chaves[chave]
        return jsonify({
            "dispositivos": info["usos"],
            "limite": info["limite"],
            "validade": info["validade"],
            "contato": info["contato"],
            "bloqueada": info.get("bloqueada", False)
        })
    return jsonify({"erro": "Chave não encontrada"}), 404
    
@app.route("/editar", methods=["POST"])
def editar():
    data = request.json
    chave = data["chave"]
    chaves = carregar(ARQUIVO_CHAVES)
    if chave in chaves:
        chaves[chave]["validade"] = data["validade"]
        chaves[chave]["contato"] = data["contato"]
        chaves[chave]["limite"] = int(data["limite"])
        salvar(ARQUIVO_CHAVES, chaves)
        return jsonify({"sucesso": True})
    return jsonify({"erro": "Chave não encontrada"}), 404

@app.route("/suspeitas")
def suspeitas():
    chaves = carregar(ARQUIVO_CHAVES)
    resultado = {
        c: info for c, info in chaves.items()
        if len(info["usos"]) > info["limite"]
    }
    return jsonify(resultado)

@app.route("/desconectar", methods=["POST"])
def desconectar():
    chave = request.json["chave"]
    dispositivo = request.json["dispositivo"]
    chaves = carregar(ARQUIVO_CHAVES)
    if chave in chaves and dispositivo in chaves[chave]["usos"]:
        chaves[chave]["usos"].remove(dispositivo)
        salvar(ARQUIVO_CHAVES, chaves)
        return jsonify({"sucesso": True})
    return jsonify({"erro": "Dispositivo ou chave não encontrados"}), 404

@app.route("/bloquear", methods=["POST"])
def bloquear():
    chave = request.json["chave"]
    chaves = carregar(ARQUIVO_CHAVES)
    if chave in chaves:
        chaves[chave]["bloqueada"] = True
        salvar(ARQUIVO_CHAVES, chaves)
        return jsonify({"sucesso": True})
    return jsonify({"erro": "Chave não encontrada"}), 404

@app.route("/desbloquear", methods=["POST"])
def desbloquear():
    chave = request.json["chave"]
    chaves = carregar(ARQUIVO_CHAVES)
    if chave in chaves:
        chaves[chave]["bloqueada"] = False
        salvar(ARQUIVO_CHAVES, chaves)
        return jsonify({"sucesso": True})
    return jsonify({"erro": "Chave não encontrada"}), 404

@app.route("/resetar", methods=["POST"])
def resetar():
    chave = request.json["chave"]
    nova_validade = request.json["validade"]
    chaves = carregar(ARQUIVO_CHAVES)
    if chave in chaves:
        chaves[chave]["usos"] = []
        chaves[chave]["validade"] = nova_validade
        salvar(ARQUIVO_CHAVES, chaves)
        return jsonify({"sucesso": True})
    return jsonify({"erro": "Chave não encontrada"}), 404

# ──────────────── 2. ATUALIZAÇÕES ────────────────

@app.route("/atualizacao/lancar", methods=["POST"])
def lancar_atualizacao():
    atualizacoes = carregar(ARQUIVO_ATUALIZACOES)
    nova = {
        "versao": request.json["versao"],
        "descricao": request.json["descricao"],
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    atualizacoes[str(len(atualizacoes) + 1)] = nova
    salvar(ARQUIVO_ATUALIZACOES, atualizacoes)
    return jsonify({"sucesso": True})

@app.route("/atualizacao/historico")
def historico_atualizacoes():
    return jsonify(carregar(ARQUIVO_ATUALIZACOES))

@app.route("/atualizacao/remover", methods=["POST"])
def remover_atualizacao():
    id = request.json["id"]
    atualizacoes = carregar(ARQUIVO_ATUALIZACOES)
    if id in atualizacoes:
        del atualizacoes[id]
        salvar(ARQUIVO_ATUALIZACOES, atualizacoes)
        return jsonify({"sucesso": True})
    return jsonify({"erro": "ID não encontrado"}), 404

# ──────────────── 3. SEGURANÇA ────────────────

@app.route("/log", methods=["POST"])
def registrar_log():
    logs = carregar(ARQUIVO_LOGS)
    entrada = {
        "tipo": request.json["tipo"],
        "mensagem": request.json["mensagem"],
        "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    logs[str(len(logs) + 1)] = entrada
    salvar(ARQUIVO_LOGS, logs)
    return jsonify({"sucesso": True})

@app.route("/logs")
def ver_logs():
    return jsonify(carregar(ARQUIVO_LOGS))

@app.route("/logs/filtrar", methods=["GET"])
def filtrar_logs():
    tipo = request.args.get("tipo")
    logs = carregar(ARQUIVO_LOGS)
    filtrados = {
        k: v for k, v in logs.items() if v["tipo"] == tipo
    }
    return jsonify(filtrados)

# ──────────────── 4. SISTEMA ────────────────

@app.route("/sistema/info")
def sistema_info():
    chaves = carregar(ARQUIVO_CHAVES)
    logs = carregar(ARQUIVO_LOGS)
    total_chaves = len(chaves)
    total_logs = len(logs)
    dispositivos_unicos = len({
        d for c in chaves.values() for d in c["usos"]
    })
    return jsonify({
        "total_chaves": total_chaves,
        "total_logs": total_logs,
        "dispositivos_unicos": dispositivos_unicos
    })

@app.route("/backup")
def backup():
    return jsonify({
        "chaves": carregar(ARQUIVO_CHAVES),
        "logs": carregar(ARQUIVO_LOGS),
        "atualizacoes": carregar(ARQUIVO_ATUALIZACOES)
    })

# ──────────────── 5. CLIENTES ────────────────

@app.route("/clientes/buscar", methods=["GET"])
def buscar_cliente():
    contato = request.args.get("contato")
    chaves = carregar(ARQUIVO_CHAVES)
    resultado = {
        c: v for c, v in chaves.items() if v["contato"] == contato
    }
    return jsonify(resultado)

@app.route("/clientes/estatisticas", methods=["GET"])
def estatisticas_cliente():
    chave = request.args.get("chave")
    chaves = carregar(ARQUIVO_CHAVES)
    if chave in chaves:
        return jsonify({
            "dispositivos": chaves[chave]["usos"],
            "limite": chaves[chave]["limite"],
            "validade": chaves[chave]["validade"],
            "contato": chaves[chave]["contato"]
        })
    return jsonify({"erro": "Chave não encontrada"}), 404

@app.route("/clientes/suspender", methods=["POST"])
def suspender():
    chave = request.json["chave"]
    chaves = carregar(ARQUIVO_CHAVES)
    if chave in chaves:
        chaves[chave]["bloqueada"] = True
        salvar(ARQUIVO_CHAVES, chaves)
        return jsonify({"sucesso": True})
    return jsonify({"erro": "Chave não encontrada"}), 404

@app.route("/clientes/alerta", methods=["POST"])
def alerta():
    chave = request.json["chave"]
    mensagem = request.json["mensagem"]
    return jsonify({"sucesso": True, "mensagem": f"Alerta para {chave}: {mensagem}"})

# ────────────────────────────────────────────

if __name__ == "__main__":
    from os import environ
    app.run(host="0.0.0.0", port=int(environ.get("PORT", 5000)))
