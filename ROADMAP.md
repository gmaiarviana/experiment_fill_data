# Roadmap de Implementação - Data Structuring Agent

## Visão Geral

Sistema conversacional que transforma conversas naturais em dados estruturados. Desenvolvimento incremental focado em entregas funcionais e testáveis a cada etapa.

---

## ✅ **ETAPA 1: FUNDAÇÃO CONVERSACIONAL - CONCLUÍDA**

**Objetivo**: API básica de chat funcionando via Docker com resposta estruturada, criando base sólida para evoluções futuras.

**Funcionalidades Implementadas:**
- ✅ **Setup Docker Completo**: PostgreSQL + FastAPI + PostgREST funcionando
- ✅ **API de Chat Básica**: Endpoint `/chat/message` com validação e resposta estruturada  
- ✅ **Health Check e Logging**: Monitoramento via `/system/health` e logs JSON estruturados
- ✅ **Configuração via Environment**: Sistema centralizado de configuração com validação

**Resultado Alcançado**: Base sólida com API de chat funcional, ambiente Docker estável, logging estruturado e configuração flexível.

---

## ❌ **ETAPA 2: INTERFACE VISUAL N8N - DEPRECADA**

**Objetivo**: Interface visual para conversação via workflows N8N, mantendo FastAPI como backend.

**Status**: DEPRECADA - Substituída pela Etapa 4 (Interface React)

**Funcionalidades Implementadas (mantidas para referência):**
- ✅ **Setup N8N Completo**: Container + API + Networking funcionando
- ✅ **Interface Visual**: N8N acessível em localhost:5678 com Basic Auth  
- ✅ **Workflow Chat Completo**: 3 nodes (Webhook → FastAPI → Response)
- ✅ **Backend Control**: N8N API Client + Workflow Manager para list/validate
- ✅ **Environment Setup**: Docker-compose + API key + volumes configurados
- ✅ **Versionamento**: Workflows como JSON versionados no git

**Resultado Alcançado**: Interface visual N8N operacional com chat completo via webhook. Backend control implementado via API para list/validate workflows. Environment setup Docker completo com versionamento de workflows.

**Motivo da Deprecação**: Decisão arquitetural de focar em interface React nativa para melhor experiência do usuário e controle total sobre a interface conversacional.

---

## 🎯 **ETAPA 3: EXTRAÇÃO INTELIGENTE - EM DESENVOLVIMENTO**

**Objetivo**: Sistema extrai dados estruturados de conversas naturais usando abordagem híbrida LLM + código, com persistência automática e framework extensível.

### **Funcionalidade 3.1: LLM Entity Extraction - ✅ IMPLEMENTADA**

**Critérios de Aceite Atingidos:**
- ✅ **OpenAI function calling integrado**: Cliente OpenAI com function calling implementado
- ✅ **Sistema extrai entidades**: nome, telefone, data, horário, tipo_consulta de linguagem natural  
- ✅ **Response estruturado com confidence score**: Score baseado em completude (0.0-1.0)
- ✅ **Identificação automática de campos faltantes**: Sistema detecta e sugere perguntas
- ✅ **Teste CLI funcionando**: `python -m src.main extract "texto natural"` → JSON estruturado
- ✅ **Teste API funcionando**: Endpoint `/extract/entities` operacional

**Implementação Realizada:**
- **EntityExtractor**: `src/core/entity_extraction.py` - Extração especializada para consultas médicas
- **CLI Command**: `src/main.py` - Sistema de linha de comando para testes
- **HTTP Endpoints**: `/extract/entities` e `/chat/message` com validação completa  
- **Schemas Pydantic**: Validação estruturada em `src/api/schemas/chat.py`

**Resultado**: Sistema converte linguagem natural em dados estruturados com confidence score de até 100%.

### **Funcionalidade 3.2: Smart Validation & Normalization - ✅ IMPLEMENTADA**
**Critérios de Aceite Atingidos:**
- ✅ Validação de telefones brasileiros (formato correto)
- ✅ Parsing de datas relativas ("amanhã", "próxima sexta") → ISO format
- ✅ Normalização automática (capitalização nomes, formatação telefones)
- ✅ Confidence scoring baseado em qualidade da validação
- ✅ **Teste CLI**: `python -m src.main validate "dados_json"` → dados normalizados
- ✅ **Teste direto**: Comandos PowerShell testam validação individual

**Implementação Realizada:**
- **Validators**: `src/core/validators.py` - Validação de dados brasileiros (CPF, telefone, CEP)
- **Data Normalizer**: `src/core/data_normalizer.py` - Normalização e formatação automática
- **HTTP Endpoint**: `POST /validate` - Validação de dados estruturados antes da persistência
- **Date Parsing**: Suporte a datas relativas em português via python-dateutil
- **Phone Validation**: Validação específica para formatos brasileiros
- **Schemas Pydantic**: Validação integrada com normalização automática

**Resultado**: Sistema valida e normaliza dados automaticamente com alta precisão para contexto brasileiro.

### **Funcionalidade 3.3: Intelligent Reasoning Loop - ✅ IMPLEMENTADA**
**Critérios de Aceite:**
Critérios de Aceite:

✅ Loop Think → Extract → Validate → Act implementado
✅ Sistema gera perguntas específicas para dados faltantes
✅ Context awareness: lembra informações durante sessão
✅ Decisão automática: extrair vs perguntar vs confirmar
✅ Teste CLI: python -m src.main reason "texto parcial" → próxima ação
✅ Teste API: Chat conversacional completo funcionando

Implementação Realizada:

ReasoningEngine: Loop Think → Extract → Validate → Act com OpenAI function calling
Context Management: Session management em memória com merge inteligente de dados
Smart Decisions: Analisa contexto e histórico para decidir próxima ação automaticamente
API Integration: Endpoint /chat/message expandido com ReasoningEngine
CLI Command: python -m src.main reason para debugging do reasoning loop

### **Funcionalidade 3.4: PostgreSQL Schema Setup - ✅ IMPLEMENTADA**

**Critérios de Aceite Atingidos:**
- ✅ **Schema consultas + extraction_logs + chat_sessions criado**: Tabelas criadas com campos completos conforme README
- ✅ **Database migrations para criação automática**: SQLAlchemy Base.metadata.create_all() funcionando  
- ✅ **Models SQLAlchemy para entidades do domínio**: Consulta, ChatSession, ExtractionLog implementados
- ✅ **Teste CLI funcionando**: `python -m src.main setup-db` → tabelas criadas (3/3)
- ✅ **Conexão PostgreSQL funcional**: Via Docker container postgres:5432 testada e validada

**Implementação Realizada:**
- **Database Connection**: `src/core/database.py` - Engine SQLAlchemy + session factory + connection management
- **SQLAlchemy Models**: `src/models/` - Consulta, ChatSession, ExtractionLog com campos completos
- **Schema Creation**: Script `setup-db` com verificação de integridade e validação pós-criação
- **Schema Testing**: `tests/test_schema.py` - Testes completos de integridade, inserção e relacionamentos
- **CLI Integration**: Comando `python -m src.main setup-db` para criação e validação automática

**Resultado**: Schema PostgreSQL 100% funcional com 3 tabelas criadas, testadas e validadas conforme especificação do README.

### **Funcionalidade 3.5: Data Persistence**
**Critérios de Aceite:**
- Repository pattern para CRUD operations
- Dados extraídos são persistidos automaticamente
- PostgREST integration para query direta dos dados
- **Teste CLI**: `python -m src.main persist "dados_json"` → ID do registro
- **Teste PostgREST**: `Invoke-WebRequest http://localhost:3000/consultas` → lista registros

### **Funcionalidade 3.6: Complete Chat Integration**
**Critérios de Aceite:**
- Endpoint `/chat/message` evolui para usar extração + persistência
- Session management com context entre mensagens
- Response inclui: resposta conversacional + dados estruturados + status
- Visualização será implementada na interface React da Etapa 4
- **Teste API**: Chat interface + visualização dados estruturados
- **Teste CLI**: Conversa completa via linha de comando

**Arquitetura Técnica:**
- **Abordagem Híbrida**: LLM para naturalidade + código para validação
- **Framework Extensível**: Estrutura genérica para novos domínios (domains/)
- **Error Handling**: Confidence threshold + fallback conversacional
- **Performance**: Function calling otimizado + validação local
- **Persistência**: PostgreSQL + PostgREST + Repository pattern

**Resultado Esperado**: Sistema converte linguagem natural em dados estruturados automaticamente, persiste registros organizados e mantém conversação natural.

---

## 🎯 **ETAPA 4: INTERFACE CONVERSACIONAL - PLANEJADA**

**Objetivo**: Interface visual limpa para conversação fluida com feedback em tempo real dos dados extraídos.

**Capacidades Planejadas:**
- Chat interface responsiva e mobile-friendly
- Visualização em tempo real dos dados sendo extraídos
- Progress feedback com % de completude e campos faltantes
- Cards visuais mostrando dados estruturados lado a lado com conversa
- Confidence score visual e status da extração
- Single-page application focada apenas na conversação

**Resultado Esperado**: Interface conversacional fluida onde usuários normais conseguem conversar naturalmente e ver dados sendo extraídos em tempo real, criando experiência demonstrável e profissional.

---

## 🎯 **ETAPA 5: MEMORY CONVERSACIONAL - PLANEJADA**

**Objetivo**: Sistema mantém contexto durante sessões de conversa.

**Capacidades Planejadas:**
- Context management durante sessão
- Session ID para identificar conversas
- Memory de informações mencionadas
- Continuidade conversacional natural
- Reutilização de contexto para completar dados

**Resultado Esperado**: Sistema lembra informações durante conversa, criando experiência natural sem repetições.

---

## 🔮 **PRÓXIMAS ETAPAS FUTURAS**

### **ETAPA 6: Memory Persistente Cross-Session**
**Objetivo**: Sistema lembra usuário entre conversas diferentes, aprendizado contínuo.

**Capacidades Planejadas:**
- Memory persistente entre sessões
- User profiling e preferências
- Learning de padrões de uso
- Feedback loop para melhorias
- Personalização automática

### **ETAPA 7: Múltiplas Ações e Workflows**
**Objetivo**: Sistema versátil com capacidade de executar diferentes tipos de ação.

**Capacidades Planejadas:**
- Action detection automática (marcar, cancelar, reagendar, consultar)
- Workflows complexos multi-step
- Batch operations em uma conversa
- Validações de negócio avançadas
- Management interface completa

### **ETAPA 8: Extensibilidade Multi-Domínio**
**Objetivo**: Plataforma extensível para outros domínios além de consultas médicas.

**Capacidades Planejadas:**
- Domain registry modular
- Template system para novos domínios
- Plugin architecture
- Configuration UI para novos casos de uso
- API integration framework

---