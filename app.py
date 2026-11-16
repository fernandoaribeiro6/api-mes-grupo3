from flask import Flask, jsonify, request
from db_connection import (
    get_active_production_orders,
    get_latest_oee_metrics,
    update_piece_status
)

app = Flask(__name__)

# ==========================================
# ROTAS DA API (ENDPOINTS)
# ==========================================

@app.route('/api/oee', methods=['GET'])
def api_get_oee():
    """Retorna os dados do OEE para o Dashboard (Grupo 4)."""
    oee_data = get_latest_oee_metrics()
    
    if oee_data:
        return jsonify(oee_data), 200
    return jsonify({"erro": "Nenhum dado de OEE encontrado ou falha na base de dados."}), 503

@app.route('/api/ordens', methods=['GET'])
def api_get_ordens():
    """Retorna a lista de Ordens de Produção ativas."""
    orders = get_active_production_orders()
    
    # Devolve a lista vazia caso não haja ordens, ou a lista preenchida
    return jsonify({"ordens_ativas": orders, "total": len(orders)}), 200

@app.route('/api/rastreabilidade', methods=['POST'])
def api_atualizar_peca():
    """
    Recebe um sinal do Cobot/Câmera (Grupo 2) para atualizar o status da peça.
    Espera um JSON no corpo do pedido: {"qr_code": "...", "estacao": "...", "status": "..."}
    """
    dados = request.get_json()
    
    # Validação simples de segurança
    if not dados or not all(k in dados for k in ("qr_code", "estacao", "status")):
        return jsonify({"erro": "Dados incompletos. Envie qr_code, estacao e status."}), 400
        
    sucesso = update_piece_status(dados["qr_code"], dados["estacao"], dados["status"])
    
    if sucesso:
        return jsonify({"mensagem": f"Peça {dados['qr_code']} atualizada com sucesso!"}), 200
    return jsonify({"erro": "Falha ao atualizar a peça no banco de dados."}), 500

# ==========================================
# INICIALIZAÇÃO DO SERVIDOR
# ==========================================
if __name__ == '__main__':
    # O debug=True reinicia o servidor automaticamente quando altera o código
    # O port=5000 é a porta padrão para microsserviços Flask
    app.run(host='0.0.0.0', port=5000, debug=True)