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

### **#2 - COBERTURA DE TESTES INSUFICIENTE**
**🎯 Impacto**: Core modules críticos sem testes, bugs não detectados

**✅ PROGRESSO FEITO**:
- Service layer: 12 testes abrangentes ✅ 
- ReasoningCoordinator: basic coverage ✅
- Validation system: comprehensive ✅

**❌ GAPS CRÍTICOS**:
```python
# SEM TESTES (0% coverage):
src/core/entity_extraction.py     # CRÍTICO - core extraction
src/core/openai_client.py         # CRÍTICO - main integration  
src/services/consultation_service.py  # Unit tests missing
src/services/extraction_service.py    # Unit tests missing
src/services/session_service.py       # Unit tests missing
```

## 📋 **PLANO DETALHADO DE TESTES**

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
**Complexidade**: Alta (mock OpenAI, test data scenarios)  
**Impacto**: CRÍTICO - Core do sistema sem coverage

#### **2. `tests/core/test_openai_client.py`**
```python
# Testes essenciais:
- test_chat_completion_basic()
- test_full_llm_completion_with_context()
- test_api_failure_handling()
- test_rate_limiting_behavior()
- test_response_parsing_edge_cases()
- test_timeout_handling()
```
**Complexidade**: Média (mock responses, async patterns)  
**Impacto**: CRÍTICO - Main integration point

### **🟡 PRIORIDADE ALTA**

#### **3. `tests/services/test_consultation_service.py`**
```python
# Testes essenciais:
- test_process_and_persist_complete_data()
- test_process_with_validation_errors()
- test_process_with_context_merge()
- test_persistence_failure_handling()
- test_business_rules_validation()
```

#### **4. `tests/services/test_extraction_service.py`**
```python
# Testes essenciais:
- test_extract_entities_with_enhancement()
- test_extract_entities_batch()
- test_validation_and_normalization_flow()
- test_quality_metrics_calculation()
- test_context_aware_extraction()
```

#### **5. `tests/services/test_session_service.py`**
```python
# Testes essenciais:
- test_session_lifecycle()
- test_session_data_persistence()
- test_session_isolation()
- test_session_cleanup()
- test_concurrent_session_handling()
```

### **🟢 PRIORIDADE MÉDIA**

#### **6. API Router Tests**
```python
# tests/api/test_routers.py
- test_extract_endpoint_validation()
- test_validate_endpoint_edge_cases()
- test_consultations_crud_operations()
- test_sessions_management_endpoints()
```

#### **7. Integration & Performance Tests**
```python
# tests/performance/test_benchmarks.py
- test_response_time_benchmarks()
- test_memory_usage_patterns()  
- test_concurrent_load_handling()

# tests/integration/test_multi_turn_conversations.py
- test_context_accumulation_across_messages()
- test_session_state_consistency()
```

## **🎯 Cronograma Sugerido**

### **Semana 1: Core Critical**
- `test_entity_extraction.py` (2-3 dias)
- `test_openai_client.py` (1-2 dias)

### **Semana 2: Services**  
- `test_consultation_service.py` (1 dia)
- `test_extraction_service.py` (1 dia)
- `test_session_service.py` (1 dia)

### **Semana 3: API & Integration**
- API router tests (1-2 dias)
- Multi-turn conversation tests (1-2 dias)

## **🛠️ Ferramentas e Patterns**

### **Mock Strategies**:
```python
# Para OpenAI Client:
@patch('src.core.openai_client.OpenAI')
async def test_with_mock_openai(mock_client):
    mock_client.chat.completions.create.return_value = mock_response
    # Test logic here
```

### **Test Data Fixtures**:
```python
# tests/fixtures/extraction_fixtures.py
CONSULTATION_MESSAGES = [
    "Maria Santos, telefone 81999887766, consulta sexta 14h",
    "João Silva quer remarcar para terça às 15h30",
    # ... more test cases
]
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

### **⚡ FASE QUALIDADE - Testes e Robustez**  
```bash
# #2 - Critical test coverage (entity_extraction, openai_client)
```
**Objetivo**: Core modules testados e robustos

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
docker exec api python -m pytest tests/core/ -v
docker exec api python -m pytest tests/test_service_layer_td3.py -v

# Integration tests  
docker exec api python -m pytest tests/integration/test_user_journey_simple.py -v
```

### **Commits Estruturados**:
- **feat**: Para nova funcionalidade ou testes (#3, #4)
- **refactor**: Para melhorias arquiteturais (#1, #2)
- **docs**: Para documentação (#4)

---

## 📈 **PROGRESSO REALIZADO**

### **✅ RESOLVIDOS COMPLETAMENTE**:
- **Service Architecture**: Especialização + DI + singleton patterns
- **Duplicate Code**: ~400+ lines obsoletas removidas
- **Test Infrastructure**: Base sólida estabelecida

### **🔄 EM PROGRESSO**:  
- **Context Management**: Arquitetura nova implementada, falta consolidação
- **Test Coverage**: ReasoningCoordinator iniciado, faltam core modules
- **Performance**: Instancing resolvido, faltam async/cache optimizations

### **📋 DESCOBERTAS VIA TESTES**:
- **Bug real encontrado**: ReasoningCoordinator 'extracted_data' error
- **Architecture quality**: Service layer bem estruturado
- **Test value**: Testes revelam problemas reais

---

## 📊 **TRACKING DE PROGRESSO DOS TESTES**

### **🎯 Test Coverage Status**

| Módulo | Coverage Atual | Target | Status | Prioridade |
|--------|---------------|---------|--------|-----------|
| `service_layer_td3.py` | ✅ 100% | 100% | **DONE** | ✅ |
| `reasoning_coordinator.py` | 🟡 ~60% | 90% | **PARTIAL** | 🔴 |
| `entity_extraction.py` | ❌ 0% | 90% | **TODO** | 🔴 |
| `openai_client.py` | ❌ 0% | 85% | **TODO** | 🔴 |
| `consultation_service.py` | ❌ 0% | 85% | **TODO** | 🟡 |
| `extraction_service.py` | ❌ 0% | 85% | **TODO** | 🟡 |
| `session_service.py` | ❌ 0% | 85% | **TODO** | 🟡 |
| `api_routers.py` | 🟡 ~40% | 80% | **PARTIAL** | 🟢 |

### **📈 Test Implementation Checklist**

#### **Week 1 - Critical Core (🔴)**
- [ ] **`test_entity_extraction.py`**
  - [ ] Basic entity extraction  
  - [ ] Context accumulation
  - [ ] Temporal expressions
  - [ ] Phone normalization
  - [ ] Malformed input handling
  - [ ] Confidence scoring
  - [ ] Schema validation

- [ ] **`test_openai_client.py`** 
  - [ ] Chat completion basic
  - [ ] Full LLM completion with context
  - [ ] API failure handling
  - [ ] Rate limiting behavior
  - [ ] Response parsing edge cases
  - [ ] Timeout handling

#### **Week 2 - Service Layer (🟡)**  
- [ ] **`test_consultation_service.py`**
- [ ] **`test_extraction_service.py`**
- [ ] **`test_session_service.py`**

#### **Week 3 - Integration (🟢)**
- [ ] **API router tests**
- [ ] **Multi-turn conversation tests**
- [ ] **Performance benchmarks**

### **🎯 Success Metrics**
- **Files with 0% coverage**: 5 → 0 
- **Critical modules covered**: 0/2 → 2/2
- **Overall project coverage**: ~45% → 75%+
- **Bugs detected via tests**: 1 → 5+ (target)

---

*Documento atualizado em: 2025-07-22*  
*Baseado em análise pós-refatoração e cleanup*  
*Focus: Issues pendentes prioritizados por impacto*