# Technical Debt - Data Structuring Agent

## 📋 Visão Geral

Documento catalogando débito técnico pendente. Organizado por **prioridade de impacto** para execução via Cursor ou Claude Code.

---

## 🚨 **CRÍTICO - Quebra Funcionalidade ou Causa Confusão**


### **#1 - CONTEXT MANAGEMENT QUEBRADO EM CONVERSAS SEQUENCIAIS**
**🎯 Impacto**: Dados extraídos perdidos entre mensagens, persistence inconsistente, UX degradada

**Problema**: Sistema não mantém contexto entre mensagens da mesma sessão
```
❌ TESTE FALHANDO:
Mensagem 1: "Maria Santos" → Extrai nome, persistence OK
Mensagem 2: "Telefone 81999887766" → Extrai telefone mas PERDE nome anterior
Erro: "Nome do paciente é obrigatório" (mas tinha extraído "Maria Santos")
```

**Root Causes**:
```python
# src/api/main.py - Session context não sendo passado corretamente
sessions[session_id]["extracted_data"] = {}  # ❌ Reset completo a cada mensagem

# src/services/consultation_service.py - Validation pipeline inconsistente  
consulta_data = {
    "nome": normalized_data.get("name") or normalized_data.get("nome", ""),  # ❌ Perde contexto anterior
}
```

**Ação Necessária**:
1. **Context Accumulation**: Mesclar dados novos com contexto existente em `main.py`
2. **Persistence Context**: Passar contexto completo para `ConsultationService`
3. **Session State Management**: Implementar state machine para conversas

**Benefícios**:
- Conversas funcionais multi-turn
- Persistence consistente 
- UX natural para coleta de dados

---

### **#2 - REASONING INTELLIGENCE LIMITADO**
**🎯 Impacto**: Sistema não entende correções, reagendamentos, ou context natural

**Problema**: LLM Strategist reconhece apenas "extract" e "ask", não operations complexas
```
❌ TESTES FALHANDO:
"Na verdade, telefone correto é 85111222333" → action="ask", confidence=0.3 (não entende correção)
"Preciso reagendar consulta" → action="ask" (trata como agendamento novo)
"Como cancelo consulta?" → action="ask", confidence=0.3 (scope limitado)
```

**Root Causes**:
```python
# src/core/reasoning/llm_strategist.py - Prompt limitado
system_prompt = """- "extract": Extrair dados
- "ask": Fazer pergunta
# ❌ Falta: correction, reschedule, cancel, confirm
```

**Ação Necessária**:
1. **Expand Action Types**: Adicionar correction, reschedule, cancel ao strategy
2. **Context-Aware Prompts**: Melhorar prompts com awareness de conversações anteriores
3. **Intent Detection**: Pre-processing para detectar intenções complexas

---

## ⚠️ **ALTO - Impacta Manutenibilidade e Performance**

### ✅ **#3 - FUNCIONALIDADES DUPLICADAS/TRIPLICADAS - RESOLVIDO**
**Status**: **IMPLEMENTADO** - 2025-07-22

**Ações Realizadas**:
- ✅ **Question Generation consolidado**: Migrou lógica de `QuestionGenerator` para `ResponseComposer`
- ✅ **Data Summarization consolidado**: Manteve `DataSummarizer`, removeu duplicação de `ConversationFlow`
- ✅ **Context Management consolidado**: Manteve `ConversationFlow`, removeu `ConversationManager` não utilizado
- ✅ **Arquivos removidos**: `src/core/question_generator.py` (140 linhas) e `src/core/conversation_manager.py` (309 linhas)
- ✅ **Código limpo**: 758 linhas de código duplicado removidas, 0 imports órfãos

**Resultado**: Sistema funcional com responsabilidades consolidadas, manutenibilidade melhorada.

---

### **#3 - ARQUITETURA DE SERVIÇOS FRAGMENTADA**
**🎯 Impacto**: Lógica de negócio espalhada, difícil testar e manter

**Problemas Estruturais**:

#### **Responsabilidades Misturadas**:
```python
# src/api/main.py (404 linhas):
# - Endpoints HTTP
# - Lógica de negócio 
# - Gerenciamento de sessão
# - Validação de dados
# - Tratamento de erros

# src/core/entity_extraction.py (426 linhas):
# - Extração de entidades
# - Normalização de dados
# - Validação temporal
# - Context management
```

#### **Services Insuficientes**:
```python
# Atual: Apenas ConsultationService
# Necessário:
# - ChatService: Orquestra conversação
# - ExtractionService: Gerencia extração
# - ValidationService: Orquestra validação
# - SessionService: Gerencia sessões
```

**Ação Necessária**:
- Extrair lógica de negócio de `main.py` para services especializados
- Quebrar `EntityExtractor` em responsabilidades menores
- Criar services especializados para cada domínio
- Implementar injeção de dependência consistente

---

### **#4 - ESTRUTURA DE ARQUIVOS CONFUSA**
**🎯 Impacto**: Difícil encontrar código, merge conflicts, onboarding lento

**Problemas de Organização**:

#### **Arquivos Muito Grandes**:
```python
src/api/main.py                          # 673 linhas - endpoints + lógica (PIOROU)
src/core/entity_extraction.py           # 447 linhas - múltiplas responsabilidades
src/core/reasoning/response_composer.py # 613 linhas - consolidado mas ainda complexo
✅ REMOVIDO: src/core/reasoning_engine.py     # Foi removido em sessões anteriores
```

#### **Estrutura Inconsistente**:
```python
# Mistura de padrões:
src/core/validation/              # Modular ✅
src/core/reasoning/              # Modular ✅  
src/core/logging/                # Modular ✅
src/core/*.py                    # Monolítico ❌
```

**Reorganização Recomendada**:
```python
src/
├── api/
│   ├── endpoints/              # Dividir main.py
│   │   ├── chat.py
│   │   ├── validation.py
│   │   └── sessions.py
│   ├── middleware/
│   └── schemas/
├── services/                   # Expandir services
│   ├── chat/
│   ├── extraction/
│   └── validation/
└── core/                      # Manter apenas utilities
    ├── validation/            # ✅ Já organizado
    ├── reasoning/             # ✅ Já organizado
    └── logging/               # ✅ Já organizado
```

---

## 🔶 **MÉDIO - Melhoria de Qualidade e Performance**

### **#5 - PERFORMANCE NÃO OTIMIZADA**
**🎯 Impacto**: Latência alta, uso excessivo de recursos, experiência degradada

**Problemas de Performance**:

#### **Operações Síncronas Desnecessárias**:
```python
# Múltiplas chamadas LLM sequenciais
# Validações redundantes executadas múltiplas vezes
# Falta de cache para validações repetitivas
```

#### **Instâncias Duplicadas**:
```python
# reasoning_engine.py cria:
self.question_generator = QuestionGenerator()
self.data_summarizer = DataSummarizer()
self.conversation_manager = ConversationManager()

# coordinator cria:
self.llm_strategist = LLMStrategist()
self.conversation_flow = ConversationFlow()  # Funcionalidade similar
self.response_composer = ResponseComposer()  # Funcionalidade similar
```

#### **Queries N+1 e Falta de Connection Pooling**:
```python
# Repository pattern sem otimizações
# Conexões de banco não reutilizadas
# Falta de batch operations
```

**Otimizações Recomendadas**:
- Implementar cache de validações
- Usar async operations onde possível
- Connection pooling para banco
- Singleton pattern para services pesados
- Batch processing para operações LLM

---


## 🔵 **BAIXO - Melhoria de Experiência do Desenvolvedor**

### **#6 - DOCUMENTAÇÃO INSUFICIENTE**
**🎯 Impacto**: Onboarding lento, manutenção custosa, integração difícil

**Lacunas Documentais**:
- APIs não documentadas com OpenAPI
- Arquitetura de reasoning não explicada
- Falta exemplos de uso dos services
- Guias de contribuição ausentes
- Decisões arquiteturais não documentadas

**Documentação Necessária**:
```python
# API Documentation:
# - OpenAPI specs para todos endpoints
# - Exemplos de request/response
# - Error codes e handling

# Architecture Documentation:
# - Diagramas de componentes
# - Fluxo de dados
# - Decisões técnicas e trade-offs

# Developer Guides:
# - Setup environment
# - Debugging guide
# - Contribution guidelines
```

---

## 📊 **MATRIZ DE PRIORIZAÇÃO**

```
IMPACTO vs COMPLEXIDADE (ATUALIZADO):

Alto Impacto    │                │ #1 Context     │
                │                │ #2 Intelligence│
                │                │ #3 Arquitetura │
                ├────────────────┼────────────────│
Médio Impacto   │ ✅ RESOLVIDO  │ #4 Estrutura   │
                │ #3 Duplicadas │ #5 Performance │
                │                │                │
                ├────────────────┼────────────────│
Baixo Impacto   │ #6 Docs        │                │
                │                │                │
   Baixa Complex.│               │ Alta Complex.  │
```

---

## 🎯 **PLANO DE EXECUÇÃO RECOMENDADO**

### **🚨 FASE CRÍTICA - Resolver Primeiro**
```bash
# #1 - Context Management
# #2 - Reasoning Intelligence
```
**Objetivo**: Sistema funcional para conversas sequenciais

### **⚡ FASE ESTRUTURAL - Melhorias Significativas**
```bash
# ✅ #3 - Funcionalidades Duplicadas (RESOLVIDO)
# #3 - Arquitetura Fragmentada (renumerado)
```
**Objetivo**: Arquitetura limpa e confiável

### **🔧 FASE OTIMIZAÇÃO - Qualidade e Performance**
```bash
# #4 - Estrutura de Arquivos (renumerado)
# #5 - Performance (renumerado)
# #6 - Documentação (renumerado)
```
**Objetivo**: Sistema otimizado e bem documentado

---

## 🛠️ **INSTRUÇÕES PARA CURSOR/CLAUDE CODE**

### **Estratégia de Execução**:
1. **Uma issue por vez** - Não misturar problemas diferentes
2. **Testes após cada mudança** - Validar que sistema funciona
3. **Commits específicos** - Facilitar rollback se necessário
4. **Backup de arquivos críticos** - Antes de grandes mudanças

### **Ordem de Segurança**:
1. **Mais seguro**: #7 (baixo risco de quebrar)
2. **Médio risco**: #3 (testar bem)
3. **Alto risco**: #1, #2, #4, #5, #6 (mudanças estruturais grandes)

### **Validação Necessária**:
```bash
# Após cada mudança:
docker-compose up --build -d
curl http://localhost:8000/system/health
docker-compose exec api python -m pytest tests/integration/test_user_journey_simple.py -v -s
docker-compose exec api python -m pytest tests/test_unified_validation.py -v
docker-compose exec api python -m pytest tests/test_health.py -v
```

---

*Documento atualizado em: 2025-07-22*  
*Baseado em análise completa do código atual*  
*Organizado para execução via Cursor/Claude Code*