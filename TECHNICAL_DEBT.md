# Technical Debt - Data Structuring Agent

## 📋 Visão Geral

Documento completo catalogando débito técnico identificado em 2025. Organizado por **prioridade de impacto** para execução via Cursor ou Claude Code.

---

## 🚨 **CRÍTICO - Quebra Funcionalidade ou Causa Confusão**

### **#1 - IMPORTS OBSOLETOS E DEPENDÊNCIAS MORTAS**
**🎯 Impacto**: Sistema pode falhar em runtime, confusão sobre qual código usar

**Problemas Identificados**:
```python
# ❌ OBSOLETO em src/main.py (lines 12-13):
from .core.validators import validate_brazilian_phone, parse_relative_date, normalize_name, calculate_validation_confidence
from .core.data_normalizer import normalize_consulta_data

# ❌ INCONSISTENTE - Mistura de sistemas de logging:
from loguru import logger              # conversation_manager.py, reasoning_engine.py
from src.core.logging.logger_factory import get_logger  # outros arquivos

# ❌ IMPORTS INEXISTENTES em entity_extraction.py:
from somewhere import parse_relative_date, parse_relative_time  # Funções não existem
```

**Ação Necessária**:
```python
# ✅ SUBSTITUIR imports em src/main.py:
from src.core.validation.normalizers.data_normalizer import DataNormalizer

# ✅ PADRONIZAR logging em TODOS os arquivos:
from src.core.logging.logger_factory import get_logger
logger = get_logger(__name__)

# ✅ REMOVER imports inexistentes
# ✅ ATUALIZAR test_validation() para usar DataNormalizer
```

**Arquivos Afetados**:
- `src/main.py` (função test_validation)
- `src/core/conversation_manager.py`
- `src/core/reasoning_engine.py`
- `src/core/entity_extraction.py`

---

### **#2 - ARQUIVOS LEGADOS OBSOLETOS**
**🎯 Impacto**: Confusão sobre qual sistema usar, imports podem falhar

**Arquivos para REMOÇÃO COMPLETA**:
```bash
src/core/logging.py              # 35 linhas - Substituído por logger_factory/
```

**Arquivos para VERIFICAR e remover se substituídos**:
```bash
# Verificar se existem versões antigas que foram substituídas:
src/core/validators.py           # Se foi substituído por validation/
src/core/data_normalizer.py     # Se foi substituído por validation/normalizers/
```

**Validação Necessária**:
- Confirmar que nenhum código ativo importa estes arquivos
- Executar testes após remoção para garantir que sistema funciona

---

### **#3 - REASONING ENGINE WRAPPER DESNECESSÁRIO**
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

## ⚠️ **ALTO - Impacta Manutenibilidade e Performance**

### **#4 - FUNCIONALIDADES DUPLICADAS/TRIPLICADAS**
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

### **#5 - ARQUITETURA DE SERVIÇOS FRAGMENTADA**
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

### **#6 - ESTRUTURA DE ARQUIVOS CONFUSA**
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

### **#7 - TESTES INCONSISTENTES E INSUFICIENTES**
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

### **#8 - PERFORMANCE NÃO OTIMIZADA**
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

### **#9 - CONFIGURAÇÃO AINDA ESPALHADA**
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

### **#10 - DOCUMENTAÇÃO INSUFICIENTE**
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

Alto Impacto    │ #1 Imports     │ #5 Arquitetura │
                │ #2 Arquivos    │ #6 Estrutura   │
                │ #3 Wrapper     │                │
                ├────────────────┼────────────────│
Médio Impacto   │ #7 Testes      │ #8 Performance │
                │ #9 Config      │                │
                ├────────────────┼────────────────│
Baixo Impacto   │ #10 Docs       │                │
                │                │                │
   Baixa Complex.│               │ Alta Complex.  │
```

---

## 🎯 **PLANO DE EXECUÇÃO RECOMENDADO**

### **🚨 FASE CRÍTICA - Resolver Primeiro**
```bash
# #1 - Imports Obsoletos
# #2 - Arquivos Legados  
# #3 - Reasoning Wrapper
```
**Objetivo**: Sistema funcional e sem confusão sobre qual código usar

### **⚡ FASE ESTRUTURAL - Melhorias Significativas**
```bash
# #4 - Funcionalidades Duplicadas
# #5 - Arquitetura Fragmentada
# #7 - Testes Inconsistentes
```
**Objetivo**: Arquitetura limpa e confiável

### **🔧 FASE OTIMIZAÇÃO - Qualidade e Performance**
```bash
# #6 - Estrutura de Arquivos
# #8 - Performance
# #9 - Configuração
# #10 - Documentação
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
1. **Mais seguro**: #1, #2, #10 (baixo risco de quebrar)
2. **Médio risco**: #3, #4, #7, #9 (testar bem)
3. **Alto risco**: #5, #6, #8 (mudanças estruturais grandes)

### **Validação Necessária**:
```bash
# Após cada mudança:
docker-compose up --build
curl http://localhost:8000/system/health
python -m pytest tests/ -v
```

---

*Documento criado em: 2025-01-21*  
*Baseado em análise completa do código atual*  
*Organizado para execução via Cursor/Claude Code*