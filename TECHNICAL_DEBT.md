# Technical Debt - Data Structuring Agent

## 📋 Visão Geral

Documento catalogando débito técnico **pendente**. Organizado por **prioridade de impacto** para execução via Cursor ou Claude Code.

---

## 🚨 **CRÍTICO - Quebra Funcionalidade ou Causa Confusão**

### **#1 - CONTEXT MANAGEMENT INCOMPLETO EM CONVERSAS SEQUENCIAIS**
**🎯 Impacto**: Inconsistência entre old/new session patterns, contexto pode ser perdido

**Problema**: Coexistência de dois sistemas de session management
```python
# ❌ INCONSISTÊNCIA ARQUITETURAL:
# src/api/main.py - Old session pattern ainda existe
sessions[session_id]["extracted_data"] = {}

# ✅ vs ServiceContainer pattern (novo)  
chat_service = get_chat_service()
result = await chat_service.process_message(message, session_id)
```

**Ação Necessária**:
1. **Consolidar Session Management**: Remover padrão antigo de main.py
2. **Padronizar Chat Router**: Usar ServiceContainer consistently  
3. **Testes Multi-turn**: Validar accumulation em conversas longas

**Benefícios**:
- Arquitetura consistente
- Context management robusto e testável
- Eliminação de duplicate logic

---

### **#2 - BUG DESCOBERTO: REASONING COORDINATOR ERROR**
**🎯 Impacto**: ReasoningCoordinator falha com erro `'extracted_data'`

**Problema**: Testes revelaram bug crítico no core reasoning
```bash
❌ ERRO REAL ENCONTRADO:
{"action": "error", "error": "'extracted_data'", "confidence": 0.0}
# Descoberto via tests/core/test_reasoning_coordinator.py
```

**Root Cause**: KeyError no processamento de extracted_data

**Ação Necessária**:
1. **Debug ReasoningCoordinator**: Investigar e corrigir erro 'extracted_data'
2. **Expand Error Handling**: Melhor tratamento de edge cases
3. **Enhanced Intelligence**: Adicionar actions: correction, reschedule, cancel

**Benefícios**:
- Sistema de reasoning funcional
- Conversas mais inteligentes
- Error handling robusto

---

## ⚠️ **ALTO - Impacta Manutenibilidade e Performance**

### **#3 - PERFORMANCE PARCIALMENTE OTIMIZADA**
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

### **#4 - COBERTURA DE TESTES INSUFICIENTE**
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

**Ação Necessária**:
1. **test_entity_extraction.py**: Cobertura do core extraction engine
2. **test_openai_client.py**: Mock-based testing da integração LLM
3. **Individual service tests**: Unit tests para each service
4. **API router tests**: Cobertura dos endpoints

---

## 📚 **MÉDIO - Qualidade e Manutenibilidade**

### **#5 - DOCUMENTAÇÃO INSUFICIENTE**
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

## 📊 **MATRIZ DE PRIORIZAÇÃO ATUALIZADA**

```
IMPACTO vs COMPLEXIDADE:

Alto Impacto    │ #1 Context     │ #2 Bug Fix     │
                │ #4 Test Gaps   │                │
                │                │                │
                ├────────────────┼────────────────│
Médio Impacto   │ #5 Docs        │ #3 Performance │
                │                │                │
                ├────────────────┼────────────────│
Baixo Impacto   │                │                │
                │                │                │
   Baixa Complex.│               │ Alta Complex.  │
```

---

## 🎯 **PLANO DE EXECUÇÃO RECOMENDADO**

### **🚨 FASE CRÍTICA - Resolver Primeiro**
```bash
# #1 - Context Management consolidation
# #2 - Fix ReasoningCoordinator bug
```
**Objetivo**: Sistema estável e funcional

### **⚡ FASE QUALIDADE - Testes e Robustez**  
```bash
# #4 - Critical test coverage (entity_extraction, openai_client)
```
**Objetivo**: Core modules testados e robustos

### **🔧 FASE OTIMIZAÇÃO - Performance e UX**
```bash
# #3 - Performance optimizations  
# #5 - Documentation completion
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
- **fix**: Para correção de bugs (#2)
- **feat**: Para nova funcionalidade ou testes (#4, #5)
- **refactor**: Para melhorias arquiteturais (#1, #3)
- **docs**: Para documentação (#5)

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

*Documento atualizado em: 2025-07-22*  
*Baseado em análise pós-refatoração e cleanup*  
*Focus: Issues pendentes prioritizados por impacto*