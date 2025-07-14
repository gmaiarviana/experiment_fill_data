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

## ✅ **ETAPA 2: INTERFACE VISUAL N8N - CONCLUÍDA**

**Objetivo**: Interface visual para conversação via workflows N8N, mantendo FastAPI como backend.

**Funcionalidades Implementadas:**
- ✅ **Setup N8N Completo**: Container + API + Networking funcionando
- ✅ **Interface Visual**: N8N acessível em localhost:5678 com Basic Auth  
- ✅ **Workflow Chat Completo**: 3 nodes (Webhook → FastAPI → Response)
- ✅ **Backend Control**: N8N API Client + Workflow Manager para list/validate
- ✅ **Environment Setup**: Docker-compose + API key + volumes configurados
- ✅ **Versionamento**: Workflows como JSON versionados no git

**Resultado Alcançado**: Interface visual N8N operacional com chat completo via webhook. Backend control implementado via API para list/validate workflows. Environment setup Docker completo com versionamento de workflows.

---

## 🎯 **ETAPA 3: EXTRAÇÃO INTELIGENTE - EM DESENVOLVIMENTO**

**Objetivo**: Sistema extrai dados estruturados de conversas naturais usando abordagem híbrida LLM + código, com persistência automática e framework extensível.

### **Funcionalidade 3.1: LLM Entity Extraction**
**Critérios de Aceite:**
- ✅ OpenAI function calling integrado ao client existente
- ✅ Sistema extrai: nome, telefone, data, horário, tipo_consulta de linguagem natural
- ✅ Response estruturado com confidence score (0.0-1.0)
- ✅ Identificação automática de campos faltantes
- ✅ **Teste CLI**: `python -m src.main extract "texto natural"` → JSON estruturado
- ✅ **Teste N8N**: Workflow mostra entidades extraídas visualmente

### **Funcionalidade 3.2: Smart Validation & Normalization**
**Critérios de Aceite:**
- ✅ Validação de telefones brasileiros (formato correto)
- ✅ Parsing de datas relativas ("amanhã", "próxima sexta") → ISO format
- ✅ Normalização automática (capitalização nomes, formatação telefones)
- ✅ Confidence scoring baseado em qualidade da validação
- ✅ **Teste CLI**: `python -m src.main validate "dados_json"` → dados normalizados
- ✅ **Teste direto**: Comandos PowerShell testam validação individual

### **Funcionalidade 3.3: Intelligent Reasoning Loop**
**Critérios de Aceite:**
- ✅ Loop Think → Extract → Validate → Act implementado
- ✅ Sistema gera perguntas específicas para dados faltantes
- ✅ Context awareness: lembra informações durante sessão
- ✅ Decisão automática: extrair vs perguntar vs confirmar
- ✅ **Teste CLI**: `python -m src.main reason "texto parcial"` → próxima ação
- ✅ **Teste N8N**: Chat conversacional completo funcionando

### **Funcionalidade 3.4: PostgreSQL Schema Setup**
**Critérios de Aceite:**
- ✅ Schema consultas + extraction_logs + chat_sessions criado
- ✅ Database migrations para criação automática de tabelas
- ✅ Models SQLAlchemy para entidades do domínio
- ✅ **Teste CLI**: `python -m src.main setup-db` → tabelas criadas
- ✅ **Teste direto**: Conexão PostgreSQL funcional via Docker

### **Funcionalidade 3.5: Data Persistence**
**Critérios de Aceite:**
- ✅ Repository pattern para CRUD operations
- ✅ Dados extraídos são persistidos automaticamente
- ✅ PostgREST integration para query direta dos dados
- ✅ **Teste CLI**: `python -m src.main persist "dados_json"` → ID do registro
- ✅ **Teste PostgREST**: `Invoke-WebRequest http://localhost:3000/consultas` → lista registros

### **Funcionalidade 3.6: Complete Chat Integration**
**Critérios de Aceite:**
- ✅ Endpoint `/chat/message` evolui para usar extração + persistência
- ✅ Session management com context entre mensagens
- ✅ Response inclui: resposta conversacional + dados estruturados + status
- ✅ Workflow N8N demonstra fluxo completo end-to-end
- ✅ **Teste N8N**: Chat interface + visualização dados estruturados
- ✅ **Teste CLI**: Conversa completa via linha de comando

**Arquitetura Técnica:**
- **Abordagem Híbrida**: LLM para naturalidade + código para validação
- **Framework Extensível**: Estrutura genérica para novos domínios (domains/)
- **Error Handling**: Confidence threshold + fallback conversacional
- **Performance**: Function calling otimizado + validação local
- **Persistência**: PostgreSQL + PostgREST + Repository pattern

**Resultado Esperado**: Sistema converte linguagem natural em dados estruturados automaticamente, persiste registros organizados e mantém conversação natural.

---

## 🎯 **ETAPA 4: MEMORY CONVERSACIONAL - PLANEJADA**

**Objetivo**: Sistema mantém contexto durante sessões de conversa.

**Capacidades Planejadas:**
- Context management durante sessão
- Session ID para identificar conversas
- Memory de informações mencionadas
- Continuidade conversacional natural
- Reutilização de contexto para completar dados

**Resultado Esperado**: Sistema lembra informações durante conversa, criando experiência natural sem repetições.

---

## 🎯 **ETAPA 5: REASONING BÁSICO - PLANEJADA**

**Objetivo**: Sistema decide inteligentemente próximos passos na conversa.

**Capacidades Planejadas:**
- Reasoning loop: Think → Extract → Validate → Act
- Detecção automática de dados incompletos
- Geração de perguntas específicas para esclarecimentos
- Confirmação inteligente antes de salvar
- Function calling básico para decisões

**Resultado Esperado**: Sistema conduz conversa de forma inteligente, fazendo apenas perguntas necessárias e confirmando quando apropriado.

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