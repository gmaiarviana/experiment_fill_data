# Data Structuring Agent - Sistema de Extração Conversacional

## Visão Geral

Sistema conversacional que transforma **conversas naturais** em **dados estruturados**. O usuário conversa naturalmente (como WhatsApp), e o sistema automaticamente extrai, organiza e armazena informações em registros estruturados.



### Conceito Central
- **Input**: Conversa natural e fluida
- **Processamento**: Extração inteligente de entidades e intenções via LLM
- **Output**: Dados estruturados (cards/tickets/registros)
- **Interface**: Interface React para visualização e interação (etapa 4)

---

## Stack Tecnológica

### **Core Services**
- **Python 3.11**: Linguagem principal para backend
- **FastAPI**: API REST para endpoints + WebSocket/SSE para chat
- **SQLAlchemy**: ORM para persistência de dados
- **PostgreSQL**: Banco de dados principal (via Docker)
- **OpenAI API**: LLM para conversação via requests HTTP (estável)
- **ReasoningEngine**: Motor de raciocínio para decisões conversacionais
- **Docker Compose**: Containerização completa

### **Interface e Acesso aos Dados**
- **PostgREST**: API REST automática para acesso direto aos dados
- **React (etapa 4)**: Interface web conversacional para interação natural
- **Webhooks**: Formulários web para input do usuário
- **HTTP Integration**: Interface chama FastAPI via `http://api:8000`

### **Bibliotecas Especializadas**
- **Pydantic**: Validação e serialização de dados estruturados
- **Loguru**: Logging estruturado e debugging
- **python-multipart**: Upload de arquivos e dados multipart
- **asyncio**: Processamento assíncrono para chat streaming
- **validators**: Validação de dados brasileiros (CPF, telefone, CEP)
- **python-dateutil**: Parsing e manipulação de datas em português

---

## Decisões Arquiteturais

### **1. Arquitetura Modular com Context Engineering**

**Princípio**: Sistema modular onde cada componente tem responsabilidade específica, seguindo princípios de Context Engineering para LLMs.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ React Interface │    │  Chat Service   │    │ Data Service    │
│   (Conversation)│───▶│ (Conversation)  │───▶│ (Structured)    │
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

### **3. Abordagem Híbrida LLM + Código**

**Decisão**: Combinar LLM para naturalidade com código para precisão e eficiência.

**LLM Responsibilities**:
- Extração de entidades de linguagem natural
- Reasoning conversacional (Think → Extract → Validate → Act)
- Geração de perguntas específicas para dados faltantes
- Context awareness e continuidade de sessão

**Code Responsibilities**:
- Validação de dados (telefones brasileiros, datas futuras)
- Normalização (formatação, capitalização)
- Regras de negócio específicas
- Operações de banco de dados

**Vantagem**: Otimiza custo/performance mantendo flexibilidade conversacional.

### **4. Framework Extensível por Domínio**

**Decisão**: Arquitetura genérica que aceita novos casos de uso além de consultas médicas.

```python
# Estrutura genérica
domains/
├── consultation/     # Primeiro caso de uso
│   ├── entities.py   # nome, telefone, data, horário, tipo
│   ├── prompts.py    # System prompts específicos
│   └── validators.py # Regras de negócio específicas
└── future_domain/    # Futuras extensões
```

**Vantagem**: Sistema evolui sem retrabalho arquitetural, novos domínios são plug-and-play.

### **5. Function Calling Architecture**

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

### **6. Reasoning Loop Simplificado**

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
├── domains/                   # Framework extensível
│   └── consultation/         # Domínio de consultas médicas
│       ├── entities.py       # Definição de entidades
│       ├── prompts.py        # System prompts específicos
│       ├── validators.py     # Validação e normalização
│       └── functions.py      # Function calling definitions
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
│   ├── logging.py            # Setup do Loguru
│   ├── validators.py         # Validação de dados brasileiros
│   └── data_normalizer.py    # Normalização e formatação de dados
└── main.py                    # Entry point CLI (para testes)
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
```

---

## URLs de Acesso

### **Sistema Completo**
```bash
# Executar todos os serviços
docker-compose up -d

# URLs principais:
# http://localhost:8000    - FastAPI Backend + Docs
# http://localhost:3000    - PostgREST (dados diretos)

# Interface React (etapa 4):
# http://localhost:3001    - Interface conversacional
```

---

## Configuração de Ambiente

### **Variáveis Essenciais**
```bash
# .env
# OpenAI (obrigatório para chat conversacional)
OPENAI_API_KEY=sua_chave_aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=500

# Database
DB_PASSWORD=secure_password_here
DATABASE_URL=postgresql://agent_user:${DB_PASSWORD}@localhost:5432/data_agent

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
# http://localhost:8000    - FastAPI (API + docs)
# http://localhost:3000    - PostgREST (dados diretos)
```

### **Teste de Funcionalidade**
```bash
# Teste chat conversacional completo
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá, quero marcar uma consulta para João Silva amanhã às 14h"}'

# Verificar dados estruturados criados
curl "http://localhost:8000/consultations"

# Teste de extração de entidades
curl -X POST "http://localhost:8000/extract/entities" \
  -H "Content-Type: application/json" \
  -d '{"message": "Maria Santos, telefone 11987654321, consulta de cardiologia"}'

### **Comandos Principais**
```bash
# Setup do banco de dados
docker exec api python -m src.main setup-db

# Testes via API (recomendado)
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá, quero marcar uma consulta"}'
```

---

## APIs Principais

### **Chat Conversacional**
- `POST /chat/message` - Enviar mensagem + receber resposta estruturada com extração automática
- `GET /sessions/{session_id}` - Recuperar contexto de sessão
- `DELETE /sessions/{session_id}` - Limpar sessão
- `GET /sessions` - Listar todas as sessões ativas

### **Dados Estruturados**
- `GET /consultations` - Listar consultas criadas
- `GET /consultations/{id}` - Detalhes de consulta específica
- `POST /extract/entities` - Extrair entidades de texto natural
- `POST /validate` - Validar dados estruturados antes da persistência

### **Sistema e Debug**
- `GET /system/health` - Status de PostgreSQL e FastAPI com verificação em paralelo
- `GET /system/metrics` - Métricas de uso e performance (planejado)
- `GET /debug/extractions` - Log de extrações para análise (planejado)

### **Configuração e Ambiente**
- **Sistema centralizado**: Configuração via `src/core/config.py` com validação
- **Variáveis obrigatórias**: `DATABASE_URL`, `OPENAI_API_KEY` com validação automática
- **Configurações opcionais**: `LOG_LEVEL`, `DEBUG`, `HOST`, `PORT` com defaults
- **Container compatibility**: Host 0.0.0.0 e environment variables acessíveis
- **Arquivo .env.example**: Template completo com todas as variáveis necessárias

### **Logging e Monitoramento**
- **Logs estruturados JSON**: Configurados via Loguru com `serialize=True`
- **Níveis configuráveis**: Via environment variable `LOG_LEVEL` (default: INFO)
- **Chat tracking**: Cada mensagem logada com timestamp e detalhes
- **Visualização**: `docker logs api --tail N` para logs recentes
- **Health monitoring**: Endpoint `/system/health` verifica todos os serviços

---

## Princípios de Design

### **Interface-First Development**
- Interface React conversacional como objetivo principal (etapa 4)
- Visualização de dados estruturados em tempo real
- Experiência demonstrável e profissional desde o início

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
- Configuração centralizada via environment variables
- Health checks e monitoramento integrado