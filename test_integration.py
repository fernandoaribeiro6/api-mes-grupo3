"""
SUITE DE TESTES DE INTEGRAÇÃO DE API E BANCO DE DADOS (PYTEST)
==============================================================
Projeto Integrador: Aplicação Web para Indústria 4.0 (Planta N2 / SMART 4.0)
Foco: Testes automatizados das APIs com o banco de dados PostgreSQL/TimescaleDB.
"""

import pytest
import jwt
import requests
from datetime import datetime, timedelta

# Configurações do ambiente de testes
BASE_URL = "http://localhost:8000"
SECRET_KEY = "chave_secreta_industria_40_super_segura"
ALGORITHM = "HS256"

# Helper para gerar tokens de teste rápidos
def create_test_token(role: str, user_id: str = "usr_test_01") -> str:
    payload = {
        "sub": user_id,
        "name": f"Test {role}",
        "email": f"test.{role.lower()}@industria40.edu.br",
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@pytest.fixture
def auth_headers_operator():
    token = create_test_token("OPERATOR")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

@pytest.fixture
def auth_headers_engineer():
    token = create_test_token("ENGINEER")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

@pytest.fixture
def auth_headers_manager():
    token = create_test_token("MANAGER")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ==============================================================================
# 1. TESTES DE AUTENTICAÇÃO E PERMISSÕES (GRUPO 5 - IAM & RBAC)
# ==============================================================================

def test_unauthorized_access():
    """Garante que requisições sem token JWT retornem HTTP 401 Unauthorized"""
    response = requests.get(f"{BASE_URL}/api/v1/telemetry/status")
    assert response.status_code == 401, f"Esperado 401, recebido {response.status_code}"

def test_forbidden_role_access(auth_headers_operator):
    """Garante que um OPERATOR não consiga disparar rotinas do Robô (403 Forbidden)"""
    payload = {"routine_type": "PALLETIZING", "speed_ratio": 0.8}
    response = requests.post(f"{BASE_URL}/api/v1/cobot/routines", json=payload, headers=auth_headers_operator)
    assert response.status_code == 403, f"Esperado 403, recebido {response.status_code}"


# ==============================================================================
# 2. TESTES DE INTEGRAÇÃO TELEMETRIA E CLP (GRUPO 1 - IOT)
# ==============================================================================

def test_telemetry_status_read(auth_headers_operator):
    """Testa leitura em tempo real do status do CLP Siemens e botoeiras"""
    response = requests.get(f"{BASE_URL}/api/v1/telemetry/status", headers=auth_headers_operator)
    assert response.status_code == 200
    data = response.json()
    assert "start_button" in data
    assert "emergency_button" in data
    assert "conveyor_speed" in data

def test_send_clp_command(auth_headers_operator):
    """Testa envio de comando de acionamento START para o CLP"""
    payload = {"command": "START", "parameter": "CONVEYOR_ON"}
    response = requests.post(f"{BASE_URL}/api/v1/telemetry/commands", json=payload, headers=auth_headers_operator)
    assert response.status_code in [200, 202]


# ==============================================================================
# 3. TESTES DE INTEGRAÇÃO DO ROBÔ COLABORATIVO (GRUPO 2 - COBOT)
# ==============================================================================

def test_cobot_routine_execution(auth_headers_engineer):
    """Testa disparo de rotina de manipulação do braço Universal Robots por um Engenheiro"""
    payload = {
        "order_id": "OP-2026-001",
        "routine_type": "PICK_AND_PLACE",
        "speed_ratio": 0.5,
        "parameters": {"source_tray": 1, "target_conveyor": 2}
    }
    response = requests.post(f"{BASE_URL}/api/v1/cobot/routines", json=payload, headers=auth_headers_engineer)
    assert response.status_code in [200, 202]
    data = response.json()
    assert "task_id" in data
    assert data["status"] in ["EXECUTING", "QUEUED"]


# ==============================================================================
# 4. TESTES DE INTEGRAÇÃO MES, RASTREABILIDADE E OEE (GRUPO 3 - MES & DB)
# ==============================================================================

def test_create_production_order(auth_headers_manager):
    """Testa criação de nova Ordem de Produção pelo Gestor"""
    payload = {
        "order_number": "OP-TEST-999",
        "product_code": "PROD-A4",
        "quantity_requested": 10
    }
    response = requests.post(f"{BASE_URL}/api/v1/mes/orders", json=payload, headers=auth_headers_manager)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["order_number"] == "OP-TEST-999"

def test_get_oee_dashboard_metrics(auth_headers_manager):
    """Testa consulta aos índices calculados de OEE (Disponibilidade, Desempenho e Qualidade)"""
    response = requests.get(f"{BASE_URL}/api/v1/mes/oee/dashboard", headers=auth_headers_manager)
    assert response.status_code == 200
    data = response.json()
    assert "availability" in data
    assert "performance" in data
    assert "quality" in data
    assert "oee" in data
