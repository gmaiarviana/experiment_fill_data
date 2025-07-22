# Technical Debt - Data Structuring Agent

## 📋 Visão Geral

Documento completo catalogando débito técnico identificado em 2025. Organizado por **prioridade de impacto** para execução via Cursor ou Claude Code.

**✅ RESOLVIDO**: 
- #1 - IMPORTS OBSOLETOS E DEPENDÊNCIAS MORTAS (2025-01-21)
- #2 - ARQUIVOS LEGADOS OBSOLETOS (2025-01-21)

---

## 🚨 **CRÍTICO - Quebra Funcionalidade ou Causa Confusão**

### **#1 - REASONING ENGINE WRAPPER DESNECESSÁRIO**
**🎯 Impacto**: 375 linhas de código morto, duplicação de funcionalidade, performance degradada

**Problema**: `src/core/reasoning_engine.py` é apenas wrapper que delega TUDO para `ReasoningCoordinator`

**Análise**:
- 90+ métodos legados que só fazem: `return self.coordinator.method()`
- Toda lógica real está em `src/core/reasoning/reasoning_coordinator.py`
- Mantido "para compatibilidade" mas é código morto

**Ação Necessária**:
```python
# ❌ REMOVER COMPLETAMENTE:
src/core/reasoning_engine.py

# ✅ ATUALIZAR imports diretos em:
src/api/main.py:
# DE: from src.core.reasoning_engine import ReasoningEngine
# PARA: from src.core.reasoning import ReasoningCoordinator

src/core/container.py:
# Atualizar get_reasoning_engine() para get_reasoning_coordinator()

src/services/consultation_service.py:
# Se usar ReasoningEngine, trocar por ReasoningCoordinator
```

**Benefícios**:
- Elimina 375 linhas de delegação desnecessária
- Remove camada extra de abstração
- Melhora performance e clareza do código

---

## 🔥 **CRÍTICO - Context Data Loss (Identificado 2025-07-22)**

### **#2 - CONTEXT MANAGEMENT QUEBRADO EM CONVERSAS SEQUENCIAIS**
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

### **#3 - REASONING INTELLIGENCE LIMITADO**
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

### **#4 - TIME EXTRACTION FALHA CONSISTENTEMENTE**
**🎯 Impacto**: Dados incompletos, agendamentos sem horário

**Problema**: Sistema extrai datas mas ignora horários consistentemente
```
❌ TESTES FALHANDO:
"Ana Lima 11987654321 proxima terca 15:30" → extrai data mas não horário 15:30
"dia 15/08/2025 as 10h" → extrai data mas não horário 10h
```

**Root Causes**:
```python
# src/core/entity_extraction.py - Schema incompleto para horários
# ❌ Extração configurada mas não persistida
```

**Ação Necessária**:
1. **Schema Update**: Verificar mapeamento horario → horário
2. **Extraction Testing**: Validar function calling para horários
3. **Normalization Pipeline**: Debuggar time processing

---

## ⚠️ **ALTO - Impacta Manutenibilidade e Performance**

### **#2 - FUNCIONALIDADES DUPLICADAS/TRIPLICADAS**
**🎯 Impacto**: Confusão sobre qual implementação usar, código duplicado, manutenção fragmentada

**Duplicações Identificadas**:

#### **Question Generation (3 implementações)**:
```python
# src/core/question_generator.py: QuestionGenerator class
# src/core/reasoning/response_composer.py: Templates similares
# src/core/reasoning_engine.py: _get_response_template() [será removido em #3]
```

#### **Data Summarization (3 implementações)**:
```python
# src/core/data_summarizer.py: DataSummarizer class  
# src/core/reasoning/conversation_flow.py: _summarize_extracted_data()
# src/core/reasoning_engine.py: _summarize_extracted_data() [será removido em #3]
```

#### **Context Management (3 implementações)**:
```python
# src/core/conversation_manager.py: ConversationManager
# src/core/reasoning/conversation_flow.py: context management methods
# src/core/reasoning_engine.py: delegation methods [será removido em #3]
```

**Estratégia de Consolidação**:
1. **Manter** implementação mais robusta de cada funcionalidade
2. **Migrar** dependências para implementação escolhida  
3. **Remover** implementações redundantes
4. **Atualizar** imports em arquivos dependentes

**Recomendação de Consolidação**:
- **Question Generation**: Manter `ResponseComposer`, migrar lógica de `QuestionGenerator`
- **Data Summarization**: Manter `DataSummarizer`, remover de `ConversationFlow`  
- **Context Management**: Manter `ConversationFlow`, migrar de `ConversationManager`

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
src/api/main.py                    # 404 linhas - endpoints + lógica
src/core/entity_extraction.py     # 426 linhas - múltiplas responsabilidades
src/core/reasoning_engine.py      # 375 linhas - wrapper desnecessário
src/core/reasoning/response_composer.py # 448 linhas - muito complexo
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

### **#5 - TESTES INCONSISTENTES E INSUFICIENTES**
**🎯 Impacto**: Bugs em produção, refatorações arriscadas, baixa confiabilidade

**Problemas Identificados**:

#### **Sistemas de Teste Conflitantes**:
```python
# src/main.py: Testa sistema ANTIGO
def test_validation():
    normalize_consulta_data()      # ❌ Sistema legado
    validate_brazilian_phone()    # ❌ Sistema legado

# tests/test_unified_validation.py: Testa sistema NOVO  
DataNormalizer().normalize_consultation_data()  # ✅ Sistema atual
```

#### **Cobertura Insuficiente**:
- Apenas 4 arquivos de teste para sistema complexo
- Falta testes de integração entre módulos
- Falta testes de performance e carga
- Falta testes dos módulos reasoning modulares

**Ação Necessária**:
```python
# Estrutura de testes recomendada:
tests/
├── unit/
│   ├── core/
│   │   ├── test_validation/
│   │   ├── test_reasoning/
│   │   └── test_extraction/
│   ├── services/
│   ├── api/
├── integration/
│   ├── test_chat_flow.py
│   ├── test_persistence_flow.py
├── performance/
└── fixtures/
```

---

### **#6 - PERFORMANCE NÃO OTIMIZADA**
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

### **#7 - CONFIGURAÇÃO AINDA ESPALHADA**
**🎯 Impacto**: Deploy arriscado, configuração inconsistente entre ambientes

**Hardcoded Values Remanescentes**:
```python
# src/main.py line 128:
url = "http://localhost:8000/system/health"  # Deveria usar settings.BASE_URL

# Várias configurações ainda não centralizadas:
# - Timeouts específicos
# - URLs de serviços externos
# - Limites de recursos
```

**Centralização Necessária**:
- Mover todos os hardcoded values para `settings.py`
- Criar configurações específicas por ambiente
- Validação automática de configurações críticas

---

## 🔵 **BAIXO - Melhoria de Experiência do Desenvolvedor**

### **#8 - DOCUMENTAÇÃO INSUFICIENTE**
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
IMPACTO vs COMPLEXIDADE:

Alto Impacto    │ #1 Wrapper     │ #3 Arquitetura │
                │                │ #4 Estrutura   │
                │                │                │
                ├────────────────┼────────────────│
Médio Impacto   │ #5 Testes      │ #6 Performance │
                │ #7 Config      │                │
                ├────────────────┼────────────────│
Baixo Impacto   │ #8 Docs        │                │
                │                │                │
   Baixa Complex.│               │ Alta Complex.  │
```

---

## 🎯 **PLANO DE EXECUÇÃO RECOMENDADO**

### **🚨 FASE CRÍTICA - Resolver Primeiro**
```bash
# #1 - Reasoning Wrapper
```
**Objetivo**: Sistema funcional e sem confusão sobre qual código usar

### **⚡ FASE ESTRUTURAL - Melhorias Significativas**
```bash
# #2 - Funcionalidades Duplicadas
# #3 - Arquitetura Fragmentada
# #5 - Testes Inconsistentes
```
**Objetivo**: Arquitetura limpa e confiável

### **🔧 FASE OTIMIZAÇÃO - Qualidade e Performance**
```bash
# #4 - Estrutura de Arquivos
# #6 - Performance
# #7 - Configuração
# #8 - Documentação
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
1. **Mais seguro**: #1, #8 (baixo risco de quebrar)
2. **Médio risco**: #2, #5, #7 (testar bem)
3. **Alto risco**: #3, #4, #6 (mudanças estruturais grandes)

### **Validação Necessária**:
```bash
# Após cada mudança:
docker-compose up --build -d
curl http://localhost:8000/system/health
docker-compose exec api python -m pytest tests/ -v
```

---

*Documento criado em: 2025-01-21*  
*Última atualização: 2025-01-21 - TD1 e TD2 resolvidos*  
*Baseado em análise completa do código atual*  
*Organizado para execução via Cursor/Claude Code*