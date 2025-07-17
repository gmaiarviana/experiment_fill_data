#!/usr/bin/env python3
"""
Teste básico para o endpoint de health check
"""
import requests


def test_health_endpoint():
    """Testa se o endpoint /system/health retorna StatusCode 200"""
    try:
        url = "http://localhost:8000/system/health"
        response = requests.get(url, timeout=10)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✅ Health check endpoint OK: {response.status_code}")
        assert True
        
    except requests.exceptions.ConnectionError:
        print("❌ API não está rodando em localhost:8000")
        assert False
    except Exception as e:
        print(f"❌ Erro: {e}")
        assert False


if __name__ == "__main__":
    print("🧪 Teste do Health Check Endpoint")
    print("-" * 40)
    
    try:
        test_health_endpoint()
        print("✅ Teste passou!")
    except AssertionError:
        print("❌ Teste falhou!") 