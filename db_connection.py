import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega as variáveis do ficheiro .env
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Inicializa o cliente Supabase (Comunicação via HTTPS / Porta 443 - Imune a bloqueios)
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"❌ Erro ao inicializar o Supabase: {e}")
    supabase = None

def get_latest_oee_metrics():
    """Lê os dados de OEE via pedido web seguro."""
    if not supabase:
        return None
    try:
        response = supabase.table('oee_metrics').select('*').order('id', desc=True).limit(1).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"❌ Erro ao buscar OEE: {e}")
        return None

def get_active_production_orders():
    """Lê as ordens de produção ativas."""
    if not supabase:
        return []
    try:
        response = supabase.table('production_orders').select('*').eq('status', 'ACTIVE').execute()
        return response.data
    except Exception as e:
        print(f"❌ Erro ao buscar ordens: {e}")
        return []

def update_piece_status(qr_code, estacao, status):
    """Atualiza o estado de uma peça. Se a peça não existir, cria uma nova (Upsert)."""
    if not supabase:
        return False
    try:
        response = supabase.table('pieces').upsert({
            "qr_code": qr_code,
            "estacao": estacao, 
            "status": status
        }).execute()
        
        return len(response.data) > 0
    except Exception as e:
        print(f"❌ Erro ao atualizar/inserir peça: {e}")
        return False

def increment_active_order():
    """Procura a ordem de produção ativa e soma +1 à quantidade produzida."""
    if not supabase:
        return False
    try:
        response = supabase.table('production_orders').select('*').eq('status', 'ACTIVE').execute()
        
        if not response.data:
            print("Nenhuma ordem ativa encontrada para atualizar.")
            return False
            
        ordem_ativa = response.data[0]
        id_ordem = ordem_ativa['id']
        
        # Adapte 'quantidade_produzida' para o nome exato da coluna no Supabase se necessário
        qtd_atual = ordem_ativa.get('quantidade_produzida', 0) 
        nova_qtd = qtd_atual + 1

        update_resp = supabase.table('production_orders').update({
            "quantidade_produzida": nova_qtd
        }).eq('id', id_ordem).execute()

        return len(update_resp.data) > 0
    except Exception as e:
        print(f"❌ Erro ao atualizar ordem de produção: {e}")
        return False

# ==========================================
# TESTE DE LIGAÇÃO
# ==========================================
if __name__ == '__main__':
    print("======================================================================")
    print("   TESTE DE CONEXÃO HTTPS SUPABASE - APLICAÇÃO WEB INDÚSTRIA 4.0")
    print("======================================================================")
    
    ordens = get_active_production_orders()
    if ordens is not None:
        print(f"✅ Conexão bem sucedida! Ordens ativas encontradas: {len(ordens)}")
    else:
        print("❌ Falha na conexão ou nenhuma ordem encontrada.")