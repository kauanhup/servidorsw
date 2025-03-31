from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/verificar', methods=['GET'])
def verificar():
    chave = request.args.get('chave')
    with open('chaves.json') as f:
        dados = json.load(f)
    if chave in dados:
        return jsonify({"valida": True, "data": dados[chave]["validade"]})
    return jsonify({"valida": False})

if __name__ == '__main__':
    app.run()
