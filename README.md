# Data Structuring Agent - Sistema de Extração Conversacional

## Visão Geral

Sistema conversacional que transforma **conversas naturais** em **dados estruturados**. O usuário conversa naturalmente (como WhatsApp), e o sistema automaticamente extrai, organiza e armazena informações em registros estruturados.

### Conceito Central
- **Input**: Conversa natural e fluida
- **Processamento**: Extração inteligente de entidades e intenções via LLM
- **Output**: Dados estruturados (cards/tickets/registros)
- **Interface**: N8N para visualização e orchestração

---

## Stack Tecnológica

### **Core Services**
- **Python 3.11**: Linguagem principal para backend
- **FastAPI**: API REST para endpoints + WebSocket/SSE para chat
- **SQLAlchemy**: ORM para persistência de dados
- **PostgreSQL**: Banco de dados principal (via Docker)
- **OpenAI API**: LLM para extração de entidades e conversação
- **Docker Compose**: Containerização completa

### **Interface e Orchestração**
- **N8N**: Interface visual principal para workflows e demonstrações
- **PostgREST**: API REST automática para acesso direto aos dados
- **React (opcional)**: Interface web complementar se necessário

### **Bibliotecas Especializadas**
- **Pydantic**: Validação e serialização de dados estruturados
- **Loguru**: Logging estruturado e debugging
- **python-multipart**: Upload de arquivos e dados multipart
- **asyncio**: Processamento assíncrono para chat streaming

---

## Decisões Arquiteturais

### **1. Arquitetura Modular com Context Engineering**

**Princípio**: Sistema modular onde cada componente tem responsabilidade específica, seguindo princípios de Context Engineering para LLMs.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   N8N Interface │    │  Chat Service   │    │ Data Service    │
│   (Workflows)   │───▶│ (Conversation)  │───▶│ (Structured)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │ Context Service │
                    │  (Memory/RAG)   │
                    └─────────────────┘
```

### **2. Context Engineering Strategy**

**Write Context** (Persistir aprendizado):
- Sessões de conversa com histórico
- Padrões de extração bem-sucedidos
- Preferências do usuário e correções

**Select Context** (Buscar contexto relevante):
- Últimas interações da sessão
- Padrões similares de extração
- Templates de entidades por domínio

**Compress Context** (Otimizar tokens):
- Resumo de conversas longas
- Entidades já extraídas como contexto
- Apenas informações relevantes para próxima extração

**Isolate Context** (Separar responsabilidades):
- Chat conversacional isolado da extração de dados
- Validação separada da coleta
- Diferentes agentes para diferentes domínios

### **3. Function Calling Architecture**

**Decisão**: LLM decide dinamicamente quais funções executar baseado na conversa.

```python
# Funções disponíveis para o agente
functions = [
    "extract_entities",      # Extrair entidades da conversa
    "validate_data",         # Validar dados estruturados
    "search_existing",       # Buscar registros existentes
    "create_record",         # Criar novo registro
    "clarify_missing"        # Pedir esclarecimentos
]
```

**Vantagem**: Sistema se adapta automaticamente a diferentes tipos de conversa sem regras fixas.

### **4. Reasoning Loop Simplificado**

**Decisão**: Ciclo Think → Extract → Validate → Act para cada interação.

```
Think:    "O usuário quer marcar consulta?"
Extract:  "Nome: João, Telefone: 11999887766, Data: amanhã"
Validate: "Falta tipo de consulta e horário específico"
Act:      "Pergunta: Que tipo de consulta e qual horário?"
```

**Vantagem**: Processo transparente e debuggável, fácil de otimizar.

---

## Estrutura de Arquivos

### **Organização por Domínio**
```
src/
├── api/                       # FastAPI endpoints
│   ├── main.py               # Aplicação principal
│   ├── routers/              # Rotas organizadas
│   │   ├── chat.py           # POST /chat/message + SSE
│   │   ├── data.py           # CRUD de registros estruturados
│   │   └── system.py         # Health checks, metrics
│   └── schemas/              # Modelos Pydantic
│       ├── chat.py           # ChatMessage, ChatResponse
│       └── consulta.py       # Consulta, ConsultaCreate
├── chat/                      # Sistema conversacional
│   ├── chat_client.py        # Cliente OpenAI + function calling
│   ├── context_manager.py    # Gerenciamento de contexto/memória
│   ├── entity_extractor.py   # Extração de entidades específicas
│   └── functions/            # Funções disponíveis para o agente
│       ├── consultation_functions.py  # Funções específicas de consulta
│       └── validation_functions.py    # Funções de validação
├── models/                    # SQLAlchemy models
│   ├── consulta.py           # Modelo principal Consulta
│   ├── session.py            # Sessões de chat
│   └── extraction_log.py     # Log de extrações para debugging
├── repositories/              # Padrão Repository (CRUD)
│   ├── consulta_repository.py
│   └── session_repository.py
├── services/                  # Lógica de negócio
│   ├── consultation_service.py  # Orquestração completa
│   └── data_structure_service.py # Transformação de dados
├── core/                      # Configuração e utils
│   ├── config.py             # Settings via environment
│   ├── database.py           # Conexão PostgreSQL
│   └── logging.py            # Setup do Loguru
└── main.py                    # Entry point CLI (para testes)
```

### **N8N Workflows Structure**
```
n8n_workflows/
├── chat_interface.json        # Workflow principal de chat
├── data_viewer.json          # Visualização de dados estruturados
├── extraction_debug.json     # Debug de extrações
└── system_monitor.json       # Monitoramento de saúde
```

---

## Modelo de Dados

### **Schema Principal**
```sql
-- Registros estruturados (exemplo: consultas)
CREATE TABLE consultas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    data DATE NOT NULL,
    horario TIME NOT NULL,
    tipo_consulta VARCHAR(100) NOT NULL,
    observacoes TEXT,
    status VARCHAR(50) DEFAULT 'agendada',
    confidence_score DECIMAL(3,2),  -- Confiança na extração
    session_id VARCHAR(100),         -- Referência à sessão de chat
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sessões de chat para contexto
CREATE TABLE chat_sessions (
    id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100),
    context JSONB,                   -- Contexto da conversa
    last_activity TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active'
);

-- Log de extrações para debugging e melhoria
CREATE TABLE extraction_logs (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    raw_message TEXT NOT NULL,
    extracted_data JSONB,
    confidence_score DECIMAL(3,2),
    reasoning_steps TEXT,            -- Debug do processo
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **Extensibilidade de Domínios**
```sql
-- Template para novos domínios
CREATE TABLE tickets_jira (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255),
    descricao TEXT,
    prioridade VARCHAR(50),
    assignee VARCHAR(100),
    -- campos específicos do domínio
    session_id VARCHAR(100),
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Configuração Docker

### **Multi-Service Architecture**
```yaml
# docker-compose.yml
services:
  # PostgreSQL para dados estruturados
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=data_agent
      - POSTGRES_USER=agent_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  # PostgREST para API automática
  postgrest:
    image: postgrest/postgrest
    environment:
      - PGRST_DB_URI=postgresql://agent_user:${DB_PASSWORD}@postgres:5432/data_agent
      - PGRST_DB_SCHEMAS=public
      - PGRST_DB_ANON_ROLE=agent_user
    ports:
      - "3000:3000"
    depends_on:
      - postgres

  # FastAPI backend
  api:
    build: .
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://agent_user:${DB_PASSWORD}@postgres:5432/data_agent
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - .:/app
    depends_on:
      - postgres

  # N8N para interface visual
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER:-admin}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD:-admin123}
      - WEBHOOK_URL=http://localhost:5678/
      - GENERIC_TIMEZONE=America/Sao_Paulo
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - api
```

---

## Configuração de Ambiente

### **Variáveis Essenciais**
```bash
# .env
# OpenAI (obrigatório)
OPENAI_API_KEY=sua_chave_aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=1500

# Database
DB_PASSWORD=secure_password_here
DATABASE_URL=postgresql://agent_user:${DB_PASSWORD}@localhost:5432/data_agent

# N8N Interface
N8N_USER=admin
N8N_PASSWORD=admin123

# Chat Configuration
CHAT_CONTEXT_WINDOW=4000
CHAT_MAX_MESSAGES=20
CHAT_ENABLE_FUNCTION_CALLING=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## Quick Start

### **Execução Completa**
```bash
# Clone e configure
git clone <repository>
cd data-structuring-agent
cp .env.example .env
# Editar .env com OPENAI_API_KEY

# Sistema completo
docker-compose up -d

# URLs de acesso:
# http://localhost:5678    - N8N Interface
# http://localhost:8000    - FastAPI (API + docs)
# http://localhost:3000    - PostgREST (dados diretos)
```

### **Teste de Funcionalidade**
```bash
# Teste direto da API de chat
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Quero marcar consulta para João Silva, telefone 11999887766, amanhã às 10h"}'

# Verificar dados estruturados criados
curl "http://localhost:3000/consultas"

# Interface visual via N8N
# Importar workflow: n8n_workflows/chat_interface.json
```

---

## APIs Principais

### **Chat Conversacional**
- `POST /chat/message` - Enviar mensagem + receber resposta estruturada
- `GET /chat/sessions/{id}` - Recuperar contexto de sessão
- `DELETE /chat/sessions/{id}` - Limpar sessão

### **Dados Estruturados**
- `GET /data/consultas` - Listar consultas criadas
- `GET /data/consultas/{id}` - Detalhes de consulta específica
- `PUT /data/consultas/{id}` - Atualizar consulta (correções)
- `DELETE /data/consultas/{id}` - Cancelar consulta

### **Sistema e Debug**
- `GET /system/health` - Status de todos os serviços
- `GET /system/metrics` - Métricas de uso e performance
- `GET /debug/extractions` - Log de extrações para análise

---

## Princípios de Design

### **Interface-First Development**
- N8N como interface principal desde o início
- Visualização de dados estruturados em tempo real
- Workflows demonstram funcionalidades implementadas

### **Incremental Value Delivery**
- Cada etapa entrega funcionalidade testável
- "Hello World" visível para todas as integrações
- Progress visual e tangível a cada implementação

### **Modular Architecture**
- Componentes independentes e testáveis
- Fácil extensão para novos domínios (tickets, leads, etc.)
- Context Engineering otimizado para performance

### **Conversation-Driven Design**
- Interface natural como WhatsApp
- LLM decide dinamicamente o próximo passo
- Usuário não precisa aprender comandos específicos

### **Production-Ready from Start**
- Docker para zero-config setup
- Logging estruturado para debugging
- Configuração via environment variables
- Health checks e monitoramento integrado