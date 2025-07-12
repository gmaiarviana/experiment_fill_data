# Roadmap de Implementação - Data Structuring Agent

## Visão Geral

Sistema conversacional que transforma conversas naturais em dados estruturados. Desenvolvimento incremental focado em entregas funcionais e testáveis a cada etapa.

---

## 🎯 **ETAPA 1: FUNDAÇÃO CONVERSACIONAL - PLANEJADA**

**Objetivo**: API básica de chat funcionando via Docker com resposta estruturada, criando base sólida para evoluções futuras.

### **Funcionalidade 1.1: Setup Docker Completo** ✅ **IMPLEMENTADO**

**Implementação Concluída:**
- ✅ docker-compose.yml com PostgreSQL, FastAPI, PostgREST
- ✅ Dockerfile otimizado para FastAPI com hot reload
- ✅ requirements.txt com dependências principais
- ✅ .env.example para configuração segura
- ✅ .gitignore protegendo credenciais
- ✅ Todos os containers funcionando e comunicando
- ✅ PostgREST API automática respondendo StatusCode 200
- ✅ PostgreSQL persistindo dados via volumes

### **Funcionalidade 1.2: API de Chat Básica**

**Critérios de Aceite:**
- Deve aceitar POST /chat/message com JSON {"message": "texto"}
- Deve retornar resposta estruturada: {"response": "texto", "timestamp": "ISO", "session_id": "uuid"}
- Deve validar entrada rejeitando mensagem vazia com HTTP 422
- Deve funcionar com resposta estática (sem dependência OpenAI inicial)
- Deve configurar headers CORS para requisições locais
- Deve documentar endpoint automaticamente no /docs do FastAPI

**Experiência do Usuário - Funcionalidade 1.2**
**Antes**: Não existe interface para comunicação com sistema
**Depois**: ✅ Usuário pode enviar mensagem via API e receber resposta estruturada, base para interface conversacional

### **Funcionalidade 1.3: Health Check e Logging**

**Critérios de Aceite:**
- Deve fornecer GET /system/health com status de todos os serviços
- Deve validar no health check: PostgreSQL conectado, FastAPI funcionando
- Deve produzir logs estruturados (JSON) visíveis em `docker logs data-agent-api`
- Deve logar cada requisição chat com timestamp, session_id, message_length
- Deve suportar diferentes níveis de log (INFO, ERROR)
- Deve proteger logs de informações sensíveis

**Experiência do Usuário - Funcionalidade 1.3**
**Antes**: Sistema sem observabilidade, impossível debuggar problemas
**Depois**: ✅ Desenvolvedor tem visibilidade completa da saúde do sistema e pode rastrear todas as interações de chat

### **Funcionalidade 1.4: Configuração via Environment**

**Critérios de Aceite:**
- Deve fornecer arquivo .env.example com todas as variáveis necessárias
- Deve funcionar apenas com variáveis obrigatórias definidas
- Deve permitir configuração de Database URL via DATABASE_URL
- Deve permitir configuração de log level via LOG_LEVEL
- Deve carregar configurações corretamente no container
- Deve mostrar erro claro se variável obrigatória estiver ausente

**Experiência do Usuário - Funcionalidade 1.4**
**Antes**: Sistema com configuração hardcoded, impossível adaptar para diferentes ambientes
**Depois**: ✅ Sistema configurável para desenvolvimento, teste e produção via variáveis de ambiente

**Status ETAPA 1:** 🎯 **PLANEJADA** (0/4 funcionalidades implementadas)

**Resultado Esperado**: Base sólida com API de chat funcional, ambiente Docker estável, logging estruturado e configuração flexível.

---

## 🎯 **ETAPA 2: INTERFACE VISUAL N8N - PLANEJADA**

**Objetivo**: Interface visual para conversação via workflows N8N.

**Capacidades Planejadas:**
- Workflow N8N de chat funcionando
- Integração N8N → FastAPI → resposta visual
- Interface para input de mensagens
- Workflows exportáveis e versionáveis
- Demonstração visual do sistema

**Resultado Esperado**: Usuário pode conversar com sistema através de interface visual intuitiva, sem linha de comando.

---

## 🎯 **ETAPA 3: EXTRAÇÃO INTELIGENTE - PLANEJADA**

**Objetivo**: Sistema extrai dados estruturados de conversas naturais usando OpenAI.

**Capacidades Planejadas:**
- Integração OpenAI para extração de entidades
- Processamento de linguagem natural
- Extração de nome, telefone, data, horário
- Confidence scoring automático
- Resposta estruturada com dados extraídos

**Resultado Esperado**: Sistema entende linguagem natural e transforma automaticamente em dados organizados.

---

## 🎯 **ETAPA 4: PERSISTÊNCIA DE DADOS - PLANEJADA**

**Objetivo**: Dados extraídos são salvos e organizados em banco PostgreSQL.

**Capacidades Planejadas:**
- PostgreSQL integrado via Docker
- Modelo de dados para consultas
- PostgREST para API automática
- Persistência de dados extraídos
- Consulta de registros salvos

**Resultado Esperado**: Conversas geram registros organizados que ficam salvos e consultáveis.

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

## 🎯 **ETAPA 6: REASONING BÁSICO - PLANEJADA**

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

### **ETAPA 7: Memory Persistente Cross-Session**
**Objetivo**: Sistema lembra usuário entre conversas diferentes, aprendizado contínuo.

**Capacidades Planejadas:**
- Memory persistente entre sessões
- User profiling e preferências
- Learning de padrões de uso
- Feedback loop para melhorias
- Personalização automática

### **ETAPA 8: Múltiplas Ações e Workflows**
**Objetivo**: Sistema versátil com capacidade de executar diferentes tipos de ação.

**Capacidades Planejadas:**
- Action detection automática (marcar, cancelar, reagendar, consultar)
- Workflows complexos multi-step
- Batch operations em uma conversa
- Validações de negócio avançadas
- Management interface completa

### **ETAPA 9: Extensibilidade Multi-Domínio**
**Objetivo**: Plataforma extensível para outros domínios além de consultas médicas.

**Capacidades Planejadas:**
- Domain registry modular
- Template system para novos domínios
- Plugin architecture
- Configuration UI para novos casos de uso
- API integration framework

---

## 🏁 **Sistema Completo - Visão Final**

Ao final das primeiras 6 etapas, teremos um **Data Structuring Agent** completo:

### **Stack Técnica Consolidada:**
- **Interface**: N8N workflows visuais
- **Backend**: FastAPI + Python com reasoning
- **IA**: OpenAI para extração + conversação
- **Storage**: PostgreSQL + PostgREST
- **Deploy**: Docker Compose completo
- **Memory**: Context management durante sessões

### **Experiência do Usuário Final:**
```
👤 Usuário: "Quero marcar consulta para João amanhã de manhã"
🤖 Sistema: "Entendi! João para amanhã de manhã. Preciso do telefone e horário específico."
👤 Usuário: "11999887766, pode ser 9h"
🤖 Sistema: "✅ Consulta confirmada: João Silva, (11) 99988-7766, 16/01/2025 09:00"
💾 Dados organizados e salvos automaticamente
```

### **Capacidades Principais:**
- Conversação natural como WhatsApp
- Extração inteligente de entidades
- Reasoning para conduzir conversa
- Memory durante sessão
- Dados estruturados persistentes
- Interface visual via N8N
- Base sólida para extensões futuras