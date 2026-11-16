#!/usr/bin/env python3
"""
Script de Geração e Teste de Tokens JWT - Projeto Integrador Indústria 4.0
-----------------------------------------------------------------------
Este script gera tokens JWT assinados para diferentes perfis de usuário (RBAC)
e executa simulações de teste de permissões de acesso às APIs do projeto.

Perfis suportados:
- OPERATOR  : Operador da máquina (HMI, acionamento simples, telemetria)
- ENGINEER  : Engenheiro de Manutenção (calibração, rotinas do robô, CLP)
- MANAGER   : Gestor de Produção (criação de OPs, relatórios de OEE)
- ADMIN     : Administrador Geral do Sistema (acesso irrestrito)

Uso:
    python3 generate-test-tokens.py
"""

import time
import datetime
import jwt
from typing import Dict, Any, List

# Configuração de Segurança Padrão (Grupo 5 - Cloud & IAM)
SECRET_KEY = "chave_secreta_industria_40_super_segura_2026_v1"
ALGORITHM = "HS256"

# Usuários de Teste Pré-cadastrados
TEST_USERS = [
    {
        "id": "usr_op_01",
        "name": "João Operador",
        "email": "joao.operador@ficticio.edu.br",
        "role": "OPERATOR"
    },
    {
        "id": "usr_eng_01",
        "name": "Carlos Engenheiro",
        "email": "carlos.eng@ficticio.edu.br",
        "role": "ENGINEER"
    },
    {
        "id": "usr_mngr_01",
        "name": "Ana Gestora",
        "email": "ana.gestora@ficticio.edu.br",
        "role": "MANAGER"
    },
    {
        "id": "usr_admin_01",
        "name": "Admin Sistema",
        "email": "admin@ficticio.edu.br",
        "role": "ADMIN"
    }
]

def generate_token(user_id: str, name: str, email: str, role: str, expires_in_hours: int = 24) -> str:
    """Gera um token JWT válido com expiração configurada."""
    now = datetime.datetime.now(datetime.timezone.utc)
    expiration = now + datetime.timedelta(hours=expires_in_hours)
    
    payload = {
        "sub": user_id,
        "name": name,
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expiration.timestamp())
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def generate_expired_token(user_id: str = "usr_expired", role: str = "OPERATOR") -> str:
    """Gera um token propositalmente expirado para testes de erro 401."""
    now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
    expiration = now - datetime.timedelta(hours=1)
    
    payload = {
        "sub": user_id,
        "name": "Usuário Expirado",
        "email": "expirado@ficticio.edu.br",
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expiration.timestamp())
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def generate_invalid_token() -> str:
    """Gera um token assinado com chave incorreta para teste de fraude/tampering."""
    payload = {
        "sub": "usr_hacker",
        "name": "Ataque Simulado",
        "role": "ADMIN",
        "exp": int(time.time()) + 3600
    }
    # Chave falsa com tamanho suficiente para evitar warning
    INVALID_KEY = "chave_falsa_super_segura_para_testes_123456"
    return jwt.encode(payload, INVALID_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Dict[str, Any]:
    """Valida o token JWT e devolve o payload ou gera exceção."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return {"error": "401 Unauthorized - Token expirado"}
    except jwt.PyJWTError:
        return {"error": "403 Forbidden - Assinatura ou token inválido"}

def simulate_rbac_check(token: str, endpoint: str, allowed_roles: List[str]) -> str:
    """Simula a validação que o API Gateway fará em cada requisição."""
    decoded = verify_token(token)
    if "error" in decoded:
        return f"❌ NEGADO: {decoded['error']}"
    
    user_role = decoded.get("role")
    if user_role in allowed_roles or user_role == "ADMIN":
        return f"✅ PERMITIDO: [{user_role}] acessou {endpoint}"
    else:
        return f"🚫 NEGADO: 403 Forbidden - Perfil [{user_role}] não tem acesso a {endpoint}"

def main():
    print("================================================================================")
    print("      GERADOR E SIMULADOR DE TOKENS JWT - INDÚSTRIA 4.0 (GRUPO 5 / IAM)         ")
    print("================================================================================")
    print()
    
    generated_tokens = {}
    
    # 1. Geração dos Tokens para cada perfil
    print("🔑 1. TOKENS VÁLIDOS GERADOS (Validade: 24h):\n")
    for user in TEST_USERS:
        token = generate_token(user["id"], user["name"], user["email"], user["role"])
        generated_tokens[user["role"]] = token
        print(f"📌 Perfil: {user['role']} ({user['name']})")
        print(f"   Token JWT: Bearer {token}\n")
    
    # Tokens especiais para testes de borda
    expired_token = generate_expired_token()
    invalid_token = generate_invalid_token()
    
    print("--------------------------------------------------------------------------------")
    print("⚠️ 2. TOKENS PARA TESTES DE EXCEÇÃO (401 / 403):\n")
    print(f"📌 Token Expirado (Deve retornar 401):")
    print(f"   Bearer {expired_token}\n")
    print(f"📌 Token com Assinatura Falsa (Deve retornar 403):")
    print(f"   Bearer {invalid_token}\n")
    
    # 2. Simulação de Testes de Permissão (RBAC)
    print("--------------------------------------------------------------------------------")
    print("🧪 3. SIMULAÇÃO DE CONTROLE DE ACESSO (RBAC) NAS APIS:\n")
    
    routes = [
        {"endpoint": "GET /api/v1/telemetry/status", "allowed": ["OPERATOR", "ENGINEER", "MANAGER"]},
        {"endpoint": "POST /api/v1/telemetry/commands", "allowed": ["OPERATOR", "ENGINEER"]},
        {"endpoint": "POST /api/v1/cobot/routines", "allowed": ["ENGINEER"]},
        {"endpoint": "POST /api/v1/mes/orders", "allowed": ["MANAGER"]},
        {"endpoint": "GET /api/v1/mes/oee/dashboard", "allowed": ["OPERATOR", "ENGINEER", "MANAGER"]}
    ]
    
    for r in routes:
        print(f"🎯 Testando Rota: {r['endpoint']} (Permitido para: {', '.join(r['allowed'])})")
        for role, token in generated_tokens.items():
            result = simulate_rbac_check(token, r["endpoint"], r["allowed"])
            print(f"   - {result}")
        print()
    
    print("--------------------------------------------------------------------------------")
    print("📋 4. EXEMPLOS DE COMANDO CURL PARA OS ALUNOS TESTAREM:\n")
    op_token = generated_tokens["OPERATOR"]
    eng_token = generated_tokens["ENGINEER"]
    
    print("# Leitura de Telemetria (Perfil OPERATOR):")
    print(f'curl -X GET "http://localhost:8000/api/v1/telemetry/status" \\\n     -H "Authorization: Bearer {op_token}"\n')
    
    print("# Disparo do Robô (Perfil ENGINEER):")
    print(f'curl -X POST "http://localhost:8000/api/v1/cobot/routines" \\\n     -H "Authorization: Bearer {eng_token}" \\\n     -H "Content-Type: application/json" \\\n     -d \'{{"routine_type": "PICK_AND_PLACE"}}\'\n')

if __name__ == "__main__":
    main()
