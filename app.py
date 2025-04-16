from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os, json, base64, requests

app = Flask(__name__)

# Arquivos locais
ARQUIVO_CHAVES = "chaves.json"
ARQUIVO_LOGS = "logs.json"
ARQUIVO_ATUALIZACOES = "atualizacoes.json"

# GitHub API
GITHUB_REPO = "kauanhup/servidorsw"
CHAVES_PATH = "chaves.json"
LOGS_PATH = "logs.json"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# Funções GitHub
def carregar_arquivo_github(caminho):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{caminho}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        content = r.json()
        return json.loads(requests.get(content['download_url']).text), content['sha']
    return {}, None

def salvar_arquivo_github(caminho, dados, sha, msg="Atualização pela Render"):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{caminho}"
    content = base64.b64encode(json.dumps(dados, indent=2).encode()).decode()
    r = requests.put(url, headers=HEADERS, json={
        "message": msg,
        "content": content,
        "sha": sha
    })
    return r.status_code == 200

# Funções locais
def carregar(caminho):
    if not os.path.exists(caminho):
        return {}
    with open(caminho, "r") as f:
        return json.load(f)

def salvar(caminho, dados):
    with open(caminho, "w") as f:
        json.dump(dados, f, indent=2)

for arquivo in [ARQUIVO_CHAVES, ARQUIVO_LOGS, ARQUIVO_ATUALIZACOES]:
    if not os.path.exists(arquivo):
        salvar(arquivo, {})

@app.route("/")
def index():
    return "Servidor SW Online"

# ─────── CHAVES ───────

@app.route("/criar", methods=["POST"])
def criar():
    data = request.json
    chave = data["chave"]
    contato = data["contato"]
    limite = int(data["limite"])
    tipo = data["tipo"]
    duracao = int(data["duracao"])

    chaves, sha = carregar_arquivo_github(CHAVES_PATH)
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
    salvar_arquivo_github(CHAVES_PATH, chaves, sha)
    return jsonify({"sucesso": True})

@app.route("/listar")
def listar():
    chaves, _ = carregar_arquivo_github(CHAVES_PATH)
    return jsonify(chaves)

@app.route("/editar", methods=["POST"])
def editar():
    data = request.json
    chave = data["chave"]
    chaves, sha = carregar_arquivo_github(CHAVES_PATH)
    if chave in chaves:
        chaves[chave]["validade"] = data["validade"]
        chaves[chave]["contato"] = data["contato"]
        chaves[chave]["limite"] = int(data["limite"])
        salvar_arquivo_github(CHAVES_PATH, chaves, sha)
        return jsonify({"sucesso": True})
    return jsonify({"erro": "Chave não encontrada"}), 404

@app.route("/bloquear", methods=["POST"])
def bloquear():
    chave = request.json["chave"]
    chaves, sha = carregar_arquivo_github(CHAVES_PATH)
    if chave in chaves:
        chaves[chave]["bloqueada"] = True
        salvar_arquivo_github(CHAVES_PATH, chaves, sha)
        return jsonify({"sucesso": True})
    return jsonify({"erro": "Chave não encontrada"}), 404

@app.route("/desbloquear", methods=["POST"])
def desbloquear():
    chave = request.json["chave"]
    chaves, sha = carregar_arquivo_github(CHAVES_PATH)
    if chave in chaves:
        chaves[chave]["bloqueada"] = False
        salvar_arquivo_github(CHAVES_PATH, chaves, sha)
        return jsonify({"sucesso": True})
    return jsonify({"erro": "Chave não encontrada"}), 404

@app.route("/resetar", methods=["POST"])
def resetar():
    chave = request.json["chave"]
    nova_validade = request.json["validade"]
    chaves, sha = carregar_arquivo_github(CHAVES_PATH)
    if chave in chaves:
        chaves[chave]["usos"] = []
        chaves[chave]["validade"] = nova_validade
        salvar_arquivo_github(CHAVES_PATH, chaves, sha)
        return jsonify({"sucesso": True})
    return jsonify({"erro": "Chave não encontrada"}), 404

@app.route("/desconectar", methods=["POST"])
def desconectar():
    chave = request.json["chave"]
    dispositivo = request.json["dispositivo"]
    chaves, sha = carregar_arquivo_github(CHAVES_PATH)
    if chave in chaves and dispositivo in chaves[chave]["usos"]:
        chaves[chave]["usos"].remove(dispositivo)
        salvar_arquivo_github(CHAVES_PATH, chaves, sha)
        return jsonify({"sucesso": True})
    return jsonify({"erro": "Dispositivo ou chave não encontrados"}), 404

# ─────── LOGS ───────

@app.route("/log", methods=["POST"])
def registrar_log():
    logs_local = carregar(ARQUIVO_LOGS)
    logs_github, sha = carregar_arquivo_github(LOGS_PATH)

    nova_entrada = {
        "tipo": request.json["tipo"],
        "mensagem": request.json["mensagem"],
        "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dispositivo": request.json.get("dispositivo", "???")
    }

    # Local
    logs_local[str(len(logs_local) + 1)] = nova_entrada
    salvar(ARQUIVO_LOGS, logs_local)

    # GitHub
    logs_github[str(len(logs_github) + 1)] = nova_entrada
    salvar_arquivo_github(LOGS_PATH, logs_github, sha, "Novo log registrado")

    return jsonify({"sucesso": True})

@app.route("/logs")
def ver_logs():
    return jsonify(carregar(ARQUIVO_LOGS))

# ─────── SISTEMA ───────

@app.route("/sistema/info")
def sistema_info():
    chaves, _ = carregar_arquivo_github(CHAVES_PATH)
    logs = carregar(ARQUIVO_LOGS)
    dispositivos_unicos = len({d for c in chaves.values() for d in c["usos"]})
    return jsonify({
        "total_chaves": len(chaves),
        "total_logs": len(logs),
        "dispositivos_unicos": dispositivos_unicos
    })

# ─────── CLIENTES ───────

@app.route("/clientes/estatisticas", methods=["GET"])
def estatisticas_cliente():
    chave = request.args.get("chave")
    chaves, _ = carregar_arquivo_github(CHAVES_PATH)
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

@app.route("/clientes/suspender", methods=["POST"])
def suspender():
    chave = request.json["chave"]
    chaves, sha = carregar_arquivo_github(CHAVES_PATH)
    if chave in chaves:
        chaves[chave]["bloqueada"] = True
        salvar_arquivo_github(CHAVES_PATH, chaves, sha)
        return jsonify({"sucesso": True})
    return jsonify({"erro": "Chave não encontrada"}), 404

@app.route("/clientes/alerta", methods=["POST"])
def alerta():
    chave = request.json["chave"]
    mensagem = request.json["mensagem"]
    return jsonify({"sucesso": True, "mensagem": f"Alerta para {chave}: {mensagem}"})

# ─────── MAIN ───────

if __name__ == "__main__":
    from os import environ
    app.run(host="0.0.0.0", port=int(environ.get("PORT", 5000)))
