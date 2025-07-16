#!/usr/bin/env python3
"""
Teste para o ConsultaRepository
"""
import sys
import os
from datetime import datetime
import uuid

# Adicionar o diretório src ao path para importar os módulos
# Dentro do container, o src está no diretório raiz
sys.path.insert(0, '/app/src')


def test_consulta_repository_import():
    """Testa se o ConsultaRepository pode ser importado corretamente"""
    try:
        from src.repositories.consulta_repository import ConsultaRepository
        print("✅ ConsultaRepository importado com sucesso")
        return True
    except ImportError as e:
        print(f"❌ Erro ao importar ConsultaRepository: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


def test_consulta_repository_creation():
    """Testa se o ConsultaRepository pode ser instanciado"""
    try:
        from src.repositories.consulta_repository import ConsultaRepository
        from src.core.database import get_session_factory
        
        # Criar sessão
        session_factory = get_session_factory()
        session = session_factory()
        
        # Criar repository
        repo = ConsultaRepository(session)
        
        print("✅ ConsultaRepository criado com sucesso")
        print(f"✅ Tipo do repository: {type(repo).__name__}")
        print(f"✅ Modelo associado: {repo.model.__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar ConsultaRepository: {e}")
        return False


def test_consulta_repository_methods():
    """Testa se os métodos do ConsultaRepository estão disponíveis"""
    try:
        from src.repositories.consulta_repository import ConsultaRepository
        from src.core.database import get_session_factory
        
        session_factory = get_session_factory()
        session = session_factory()
        repo = ConsultaRepository(session)
        
        # Lista de métodos esperados
        expected_methods = [
            'create', 'get', 'update', 'delete', 'list', 'count', 'exists',
            'find_by_session', 'find_by_status', 'find_by_date_range', 
            'find_pending', 'find_by_session_and_status', 'update_status',
            'get_recent_consultas'
        ]
        
        # Verificar métodos disponíveis
        available_methods = [m for m in dir(repo) if not m.startswith('_') and callable(getattr(repo, m))]
        
        print(f"✅ Métodos disponíveis: {len(available_methods)}")
        print(f"✅ Métodos esperados: {len(expected_methods)}")
        
        # Verificar se todos os métodos esperados estão presentes
        missing_methods = [m for m in expected_methods if m not in available_methods]
        
        if missing_methods:
            print(f"❌ Métodos faltando: {missing_methods}")
            return False
        else:
            print("✅ Todos os métodos esperados estão presentes")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar métodos: {e}")
        return False


def test_consulta_repository_inheritance():
    """Testa se o ConsultaRepository herda corretamente do BaseRepository"""
    try:
        from src.repositories.consulta_repository import ConsultaRepository
        from src.repositories.base_repository import BaseRepository
        from src.models.consulta import Consulta
        
        # Verificar herança
        assert issubclass(ConsultaRepository, BaseRepository), "ConsultaRepository deve herdar de BaseRepository"
        
        # Verificar tipo genérico
        repo = ConsultaRepository(None)  # None para teste de tipo
        assert repo.model == Consulta, "Repository deve estar tipado para Consulta"
        
        print("✅ Herança do BaseRepository verificada")
        print("✅ Tipagem genérica correta")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar herança: {e}")
        return False


def test_consulta_repository_type_hints():
    """Testa se os type hints estão corretos"""
    try:
        from src.repositories.consulta_repository import ConsultaRepository
        from src.models.consulta import Consulta
        from typing import get_type_hints
        
        # Verificar type hints dos métodos principais
        hints = get_type_hints(ConsultaRepository.find_by_session)
        assert hints['return'] == 'List[Consulta]', "find_by_session deve retornar List[Consulta]"
        
        hints = get_type_hints(ConsultaRepository.find_by_status)
        assert hints['return'] == 'List[Consulta]', "find_by_status deve retornar List[Consulta]"
        
        hints = get_type_hints(ConsultaRepository.find_pending)
        assert hints['return'] == 'List[Consulta]', "find_pending deve retornar List[Consulta]"
        
        print("✅ Type hints verificados")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar type hints: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Teste do ConsultaRepository")
    print("=" * 50)
    
    tests = [
        ("Importação", test_consulta_repository_import),
        ("Criação", test_consulta_repository_creation),
        ("Métodos", test_consulta_repository_methods),
        ("Herança", test_consulta_repository_inheritance),
        ("Type Hints", test_consulta_repository_type_hints),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testando: {test_name}")
        print("-" * 30)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name}: PASS")
        else:
            print(f"❌ {test_name}: FAIL")
    
    print("\n" + "=" * 50)
    print(f"📊 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram!")
    else:
        print("⚠️  Alguns testes falharam!") 