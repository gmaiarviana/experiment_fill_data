# Technical Debt - Data Structuring Agent

## 📋 Visão Geral

Documento catalogando débito técnico **pendente**. Organizado por **prioridade de impacto** para execução via Cursor ou Claude Code.

---

## ⚠️ **ALTO - Impacta Manutenibilidade e Performance**

### **#1 - PERFORMANCE PARCIALMENTE OTIMIZADA**
**🎯 Impacto**: Algumas otimizações implementadas, mas gaps remainem

**✅ PROGRESSO FEITO**:
- Singleton patterns eliminaram instâncias duplicadas ✅
- ServiceContainer com dependency injection ✅
- Lazy loading implementado ✅

**❌ GAPS RESTANTES**:
- Falta async operations para LLM calls pesadas
- Sem connection pooling para database
- Sem cache para validation results
- Performance benchmarks ausentes

**Ação Necessária**:
1. **Async LLM Operations**: Implementar await patterns para reasoning
2. **Database Connection Pooling**: Otimizar conexões DB
3. **Validation Caching**: Cache results para dados repetitivos
4. **Performance Benchmarks**: Medir e validar otimizações

---

### **#2 - TESTES REMANESCENTES**
**🎯 Impacto**: Alguns módulos ainda sem cobertura de testes

**✅ TESTES IMPLEMENTADOS**:
- OpenAI Client: 15 testes completos ✅
- Config Management: 25 testes abrangentes ✅  
- Chat Service: 19 testes de orquestração ✅
- Service Layer: 12 testes de arquitetura ✅
- ReasoningCoordinator: cobertura básica ✅
- Validation System: testes completos ✅

**❌ GAPS RESTANTES**:
```python
# SEM TESTES (0% coverage):
src/core/entity_extraction.py         # CRÍTICO - core extraction
src/services/consultation_service.py  # Unit tests missing
src/services/extraction_service.py    # Estrutura criada, precisa correção
src/services/validation_service.py    # Estrutura criada, precisa correção
src/services/session_service.py       # Unit tests missing
```

## 📋 **PLANO TESTES REMANESCENTES**

### **🔴 PRIORIDADE CRÍTICA**

#### **1. `tests/core/test_entity_extraction.py`**
```python
# Testes essenciais:
- test_extract_consulta_entities_basic()
- test_extract_with_context_accumulation()  
- test_extract_complex_temporal_expressions()
- test_extract_phone_normalization()
- test_extract_with_malformed_input()
- test_extract_confidence_scoring()
- test_extract_schema_validation()
```
**Impacto**: CRÍTICO - Core do sistema sem coverage

### **🟡 PRIORIDADE ALTA**

#### **2. `tests/services/test_consultation_service.py`**
```python
# Testes essenciais:
- test_process_and_persist_complete_data()
- test_process_with_validation_errors()
- test_process_with_context_merge()
- test_persistence_failure_handling()
- test_business_rules_validation()
```

#### **3. Correção dos testes existentes**
- `test_extraction_service.py` - Corrigir mocking strategy
- `test_validation_service.py` - Corrigir mocking strategy

#### **4. `tests/services/test_session_service.py`**
```python
# Testes essenciais:
- test_session_lifecycle()
- test_session_data_persistence()
- test_session_isolation()
- test_session_cleanup()
- test_concurrent_session_handling()
```

### **🟢 PRIORIDADE MÉDIA**

#### **5. API Router Tests**
```python
# tests/api/test_routers.py
- test_extract_endpoint_validation()
- test_validate_endpoint_edge_cases()
- test_consultations_crud_operations()
- test_sessions_management_endpoints()
```

### **Coverage Target**:
- **Core modules**: 90%+ coverage
- **Services**: 85%+ coverage  
- **API routes**: 80%+ coverage
- **Overall project**: 75%+ coverage

---

## 📚 **MÉDIO - Qualidade e Manutenibilidade**

### **#3 - DOCUMENTAÇÃO INSUFICIENTE**
**🎯 Impacto**: Onboarding lento, integração difícil

**Lacunas Documentais**:
- OpenAPI specs para todos endpoints
- Architecture decision records (ADRs)
- Service integration patterns e examples
- Developer setup e contribution guides
- Error handling patterns documentation

**Ação Necessária**:
1. **OpenAPI Documentation**: Auto-generate API specs
2. **Architecture Docs**: Service patterns, DI, reasoning flow
3. **Developer Guides**: Setup, debugging, testing patterns
4. **Code Examples**: Integration patterns para new features

---

## 🎯 **PLANO DE EXECUÇÃO RECOMENDADO**

### **⚡ FASE QUALIDADE - Testes Remanescentes**  
```bash
# #2 - Critical test coverage (entity_extraction, consultation_service)
```
**Objetivo**: Completar cobertura dos módulos críticos restantes

### **🔧 FASE OTIMIZAÇÃO - Performance e UX**
```bash
# #1 - Performance optimizations  
# #3 - Documentation completion
```
**Objetivo**: Sistema otimizado e bem documentado

---

## 🛠️ **INSTRUÇÕES PARA EXECUÇÃO**

### **Validação Obrigatória Após Mudanças**:
```bash
# Health check
curl http://localhost:8000/system/health

# Core tests
docker-compose exec api python -m pytest tests/core/ -v
docker-compose exec api python -m pytest tests/services/ -v

# Integration tests  
docker-compose exec api python -m pytest tests/integration/ -v
```

### **Commits Estruturados**:
- **feat**: Para nova funcionalidade ou testes
- **refactor**: Para melhorias arquiteturais
- **docs**: Para documentação

---

## 📈 **PROGRESSO REALIZADO**

### **✅ RESOLVIDOS COMPLETAMENTE**:
- **Test Coverage**: 59 novos testes implementados ✅
- **OpenAI Client**: 15 testes completos + bug fix ✅
- **Config Management**: 25 testes de configuração ✅  
- **Chat Service**: 19 testes de orquestração ✅
- **Service Architecture**: Especialização + DI + singleton patterns ✅
- **Duplicate Code**: ~400+ lines obsoletas removidas ✅

### **🔄 EM PROGRESSO**:  
- **Test Coverage**: Core modules principais cobertos, faltam alguns services
- **Performance**: Instancing resolvido, faltam async/cache optimizations

### **📊 Test Coverage Status Atualizado**

| Módulo | Coverage Atual | Target | Status | Prioridade |
|--------|---------------|---------|--------|-----------|
| `openai_client.py` | ✅ 100% | 85% | **DONE** | ✅ |
| `config.py` | ✅ 100% | 85% | **DONE** | ✅ |
| `chat_service.py` | ✅ 100% | 85% | **DONE** | ✅ |
| `service_layer_td3.py` | ✅ 100% | 100% | **DONE** | ✅ |
| `reasoning_coordinator.py` | 🟡 ~60% | 90% | **PARTIAL** | 🔴 |
| `entity_extraction.py` | ❌ 0% | 90% | **TODO** | 🔴 |
| `consultation_service.py` | ❌ 0% | 85% | **TODO** | 🟡 |
| `extraction_service.py` | 🟡 estrutura | 85% | **PARTIAL** | 🟡 |
| `validation_service.py` | 🟡 estrutura | 85% | **PARTIAL** | 🟡 |
| `session_service.py` | ❌ 0% | 85% | **TODO** | 🟡 |

### **🎯 Success Metrics Atualizados**
- **Novos testes implementados**: 59 testes funcionais
- **Bugs detectados e corrigidos**: 1 (UnboundLocalError no OpenAI client)  
- **Módulos críticos cobertos**: 3/6 principais módulos cobertos
- **Overall project coverage**: Significativo aumento na cobertura

---

*Documento atualizado em: 2025-07-22*  
*Baseado em implementação do débito técnico #2*  
*Focus: Issues remanescentes após progresso significativo*