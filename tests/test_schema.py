#!/usr/bin/env python3
"""
Teste completo do schema PostgreSQL

Este módulo testa a integridade das tabelas, inserção de dados e constraints
do banco de dados PostgreSQL para o Data Structuring Agent.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.models import Consulta, ChatSession, ExtractionLog
from src.core.database import get_engine, get_session_factory


def test_schema_integrity():
    """
    Testa a integridade da estrutura das tabelas PostgreSQL.
    
    Verifica:
    - Existência das tabelas obrigatórias
    - Campos obrigatórios em cada tabela
    - Tipos de dados corretos (JSONB, UUID, DECIMAL)
    - Constraints e índices
    """
    print("🔍 Testando integridade do schema PostgreSQL...")
    
    try:
        engine = get_engine()
        
        # Lista de tabelas obrigatórias
        required_tables = ['consultas', 'chat_sessions', 'extraction_logs']
        
        # Verificar existência das tabelas
        with engine.connect() as connection:
            for table_name in required_tables:
                result = connection.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"
                ), {"table_name": table_name})
                
                if not result.scalar():
                    print(f"❌ Tabela '{table_name}' não encontrada")
                    assert False
                else:
                    print(f"✅ Tabela '{table_name}' existe")
        
        # Verificar estrutura da tabela consultas
        print("\n📋 Verificando estrutura da tabela 'consultas'...")
        consultas_required_fields = {
            'id': 'integer',
            'nome': 'character varying',
            'telefone': 'character varying', 
            'data': 'timestamp without time zone',
            'horario': 'character varying',
            'tipo_consulta': 'character varying'
        }
        
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'consultas'
                ORDER BY ordinal_position
            """))
            
            columns = {row[0]: {'type': row[1], 'nullable': row[2]} for row in result}
            
            for field, expected_type in consultas_required_fields.items():
                if field not in columns:
                    print(f"❌ Campo obrigatório '{field}' não encontrado em 'consultas'")
                    assert False
                
                actual_type = columns[field]['type']
                if expected_type not in actual_type:
                    print(f"❌ Campo '{field}' tem tipo '{actual_type}', esperado '{expected_type}'")
                    assert False
                
                print(f"✅ Campo '{field}' ({actual_type}) - {'NULL' if columns[field]['nullable'] == 'YES' else 'NOT NULL'}")
        
        # Verificar tipos especiais (JSONB, UUID, DECIMAL)
        print("\n🔧 Verificando tipos especiais...")
        
        # Verificar JSONB em chat_sessions.context
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT data_type FROM information_schema.columns 
                WHERE table_name = 'chat_sessions' AND column_name = 'context'
            """))
            
            if result.scalar() != 'jsonb':
                print("❌ Campo 'context' em 'chat_sessions' não é JSONB")
                assert False
            else:
                print("✅ Campo 'context' é JSONB")
        
        # Verificar UUID em session_id
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT data_type FROM information_schema.columns 
                WHERE table_name = 'consultas' AND column_name = 'session_id'
            """))
            
            if 'uuid' not in result.scalar():
                print("❌ Campo 'session_id' em 'consultas' não é UUID")
                assert False
            else:
                print("✅ Campo 'session_id' é UUID")
        
        # Verificar DECIMAL em confidence_score
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT data_type FROM information_schema.columns 
                WHERE table_name = 'consultas' AND column_name = 'confidence_score'
            """))
            
            if 'numeric' not in result.scalar():
                print("❌ Campo 'confidence_score' em 'consultas' não é DECIMAL")
                assert False
            else:
                print("✅ Campo 'confidence_score' é DECIMAL")
        
        print("\n✅ Teste de integridade do schema passou!")
        assert True
        
    except Exception as e:
        print(f"❌ Erro ao testar schema: {e}")
        assert False


def test_data_insertion():
    """
    Testa inserção de dados de teste em todas as tabelas.
    
    Verifica:
    - Inserção em Consulta
    - Inserção em ChatSession  
    - Inserção em ExtractionLog
    - Relacionamentos entre tabelas
    """
    print("\n📝 Testando inserção de dados...")
    
    try:
        session_factory = get_session_factory()
        session = session_factory()
        
        # Criar session_id para relacionamentos
        test_session_id = uuid.uuid4()
        
        # 1. Testar inserção em ChatSession
        print("  📱 Criando ChatSession...")
        chat_session = ChatSession(
            user_id="test_user_123",
            context={
                "conversation_history": ["Olá, preciso marcar uma consulta"],
                "extracted_data": {"nome": "João Silva"}
            },
            status="active"
        )
        
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)
        
        print(f"    ✅ ChatSession criada com ID: {chat_session.id}")
        
        # 2. Testar inserção em Consulta
        print("  🏥 Criando Consulta...")
        consulta = Consulta(
            nome="João Silva",
            telefone="(11) 99999-9999",
            data=datetime.now() + timedelta(days=7),
            horario="14:30",
            tipo_consulta="Consulta de rotina",
            observacoes="Paciente solicita exame de sangue",
            status="pendente",
            confidence_score=Decimal("0.95"),
            session_id=test_session_id
        )
        
        session.add(consulta)
        session.commit()
        session.refresh(consulta)
        
        print(f"    ✅ Consulta criada com ID: {consulta.id}")
        
        # 3. Testar inserção em ExtractionLog
        print("  📊 Criando ExtractionLog...")
        extraction_log = ExtractionLog(
            session_id=test_session_id,
            raw_message="Olá, preciso marcar uma consulta para João Silva amanhã às 14h",
            extracted_data={
                "nome": "João Silva",
                "data": "2024-01-15",
                "horario": "14:00",
                "tipo_consulta": "Consulta de rotina"
            },
            confidence_score=Decimal("0.92"),
            reasoning_steps=[
                {
                    "type": "extract",
                    "description": "Extraído nome 'João Silva'",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"field": "nome", "value": "João Silva"}
                }
            ]
        )
        
        session.add(extraction_log)
        session.commit()
        session.refresh(extraction_log)
        
        print(f"    ✅ ExtractionLog criado com ID: {extraction_log.id}")
        
        # 4. Verificar relacionamentos
        print("  🔗 Verificando relacionamentos...")
        
        # Buscar consulta por session_id
        consulta_by_session = session.query(Consulta).filter(
            Consulta.session_id == test_session_id
        ).first()
        
        if consulta_by_session:
            print(f"    ✅ Consulta encontrada por session_id: {consulta_by_session.nome}")
        else:
            print("    ❌ Consulta não encontrada por session_id")
            assert False
        
        # Buscar logs por session_id
        logs_by_session = session.query(ExtractionLog).filter(
            ExtractionLog.session_id == test_session_id
        ).all()
        
        if logs_by_session:
            print(f"    ✅ {len(logs_by_session)} logs encontrados por session_id")
        else:
            print("    ❌ Logs não encontrados por session_id")
            assert False
        
        session.close()
        print("\n✅ Teste de inserção de dados passou!")
        assert True
        
    except Exception as e:
        print(f"❌ Erro ao testar inserção de dados: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        assert False


def cleanup_test_data() -> bool:
    """
    Limpa dados de teste das tabelas.
    
    Remove:
    - Consultas com session_id de teste
    - ExtractionLogs com session_id de teste
    - ChatSessions de teste
    
    Returns:
        bool: True se limpeza foi bem-sucedida, False caso contrário
    """
    print("\n🧹 Limpando dados de teste...")
    
    try:
        session_factory = get_session_factory()
        session = session_factory()
        
        # Contar registros antes da limpeza
        consultas_count = session.query(Consulta).count()
        logs_count = session.query(ExtractionLog).count()
        sessions_count = session.query(ChatSession).count()
        
        print(f"  📊 Registros antes da limpeza:")
        print(f"    - Consultas: {consultas_count}")
        print(f"    - ExtractionLogs: {logs_count}")
        print(f"    - ChatSessions: {sessions_count}")
        
        # Limpar dados de teste (consultas e logs com session_id específico)
        deleted_consultas = session.query(Consulta).filter(
            Consulta.session_id.isnot(None)
        ).delete()
        
        deleted_logs = session.query(ExtractionLog).filter(
            ExtractionLog.session_id.isnot(None)
        ).delete()
        
        # Limpar chat sessions de teste
        deleted_sessions = session.query(ChatSession).filter(
            ChatSession.user_id.like("test_%")
        ).delete()
        
        session.commit()
        
        print(f"  🗑️  Dados removidos:")
        print(f"    - Consultas: {deleted_consultas}")
        print(f"    - ExtractionLogs: {deleted_logs}")
        print(f"    - ChatSessions: {deleted_sessions}")
        
        # Verificar contagem após limpeza
        consultas_after = session.query(Consulta).count()
        logs_after = session.query(ExtractionLog).count()
        sessions_after = session.query(ChatSession).count()
        
        print(f"  📊 Registros após limpeza:")
        print(f"    - Consultas: {consultas_after}")
        print(f"    - ExtractionLogs: {logs_after}")
        print(f"    - ChatSessions: {sessions_after}")
        
        session.close()
        print("✅ Limpeza de dados de teste concluída!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao limpar dados de teste: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


def run_schema_tests() -> bool:
    """
    Executa todos os testes do schema PostgreSQL.
    
    Returns:
        bool: True se todos os testes passaram, False caso contrário
    """
    print("🧪 Teste Completo do Schema PostgreSQL")
    print("=" * 50)
    
    # Executar testes em sequência
    tests = [
        ("Integridade do Schema", test_schema_integrity),
        ("Inserção de Dados", test_data_insertion),
        ("Limpeza de Dados", cleanup_test_data)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Executando: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSOU")
            else:
                print(f"❌ {test_name}: FALHOU")
                
        except Exception as e:
            print(f"❌ {test_name}: ERRO - {e}")
            results.append((test_name, False))
    
    # Resumo final
    print("\n" + "=" * 50)
    print("📋 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes do schema passaram!")
        return True
    else:
        print("⚠️  Alguns testes falharam. Verifique os logs acima.")
        return False


if __name__ == "__main__":
    success = run_schema_tests()
    exit(0 if success else 1) 