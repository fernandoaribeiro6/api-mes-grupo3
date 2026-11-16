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
        # Equivalente a: SELECT * FROM oee_metrics ORDER BY id DESC LIMIT 1
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
        # Equivalente a: SELECT * FROM production_orders WHERE status = 'ACTIVE'
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
        # O upsert cria a linha se não existir, ou atualiza se o qr_code (chave) já existir
        response = supabase.table('pieces').upsert({
            "qr_code": qr_code,
            "estacao": estacao, 
            "status": status
        }).execute()
        
        return len(response.data) > 0
    except Exception as e:
        print(f"❌ Erro ao atualizar/inserir peça: {e}")
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