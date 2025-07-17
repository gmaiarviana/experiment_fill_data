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
- **React 18 + TypeScript**: Interface web conversacional MVP com transparência do agente
- **Vite**: Build tool para desenvolvimento rápido e hot reload
- **Tailwind CSS**: Styling responsivo e moderno
- **HTTP REST**: Interface chama FastAPI via `http://api:8000` com polling inteligente

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

### **7. Arquitetura Modular para Conversação Inteligente**

**Decisão**: Sistema modular com componentes especializados para evitar loops, repetições e facilitar manutenção.

**Componentes Modulares**:
- **QuestionGenerator**: Geração de perguntas contextuais e templates de resposta
- **DataSummarizer**: Sumarização de dados e verificação de completude
- **ConversationManager**: Gestão de estado da conversa e prevenção de loops
- **ReasoningEngine**: Motor de raciocínio que orquestra os componentes

**Benefícios**:
- Evita loops e repetições na conversa
- Código mais limpo e fácil de manter
- Componentes isolados para testes e ajustes
- Melhor experiência do usuário

### **8. Interface MVP com Transparência do Agente**

**Decisão**: Interface React focada em mostrar o processo interno do agente, não apenas conversar com ele.

**Layout de 3 Colunas**:
```
┌─────────────────┬─────────────────┬─────────────────┐
│                 │                 │                 │
│   CHAT          │   REASONING     │   DADOS         │
│   INTERFACE     │   LOOP DEBUG    │   ESTRUTURADOS  │
│                 │                 │                 │
│   [Input]       │   Think: ...    │   Nome: João    │
│   [Histórico]   │   Extract: ...  │   Tel: (11)...  │
│                 │   Validate: ... │   Data: ...     │
│                 │   Act: ...      │   Conf: 85%     │
└─────────────────┴─────────────────┴─────────────────┘
```

**Transparência Implementada**:
- **Reasoning Panel**: 4 passos principais com detalhes relevantes e timestamps
- **Data Panel**: Dados estruturados com confidence scores e status de validação
- **Polling Inteligente**: 500ms durante processamento, 2s em idle
- **Sem Persistência**: Apenas último ciclo de reasoning visível

**Vantagem**: Debugging eficiente e demonstração transparente do funcionamento do agente.

### **8. Containerização Padronizada**

**Decisão**: Sistema completo containerizado com Docker Compose para zero-config setup.

**Arquitetura de Containers**:
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   FastAPI       │    │   React         │
│   (5432)        │◄───┤   (8000)        │◄───┤   (3001)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲
         │                       │
         └───────────────────────┘
                    │
         ┌─────────────────┐
         │   PostgREST     │
         │   (3000)        │
         └─────────────────┘
```

**Padrões Docker**:
- **Multi-stage builds**: Otimização de imagens para produção
- **Volume mounting**: Hot reload para desenvolvimento
- **Network isolation**: Comunicação segura entre serviços
- **Environment variables**: Configuração centralizada via .env
- **Health checks**: Monitoramento automático de serviços

**Vantagem**: Setup consistente em qualquer ambiente, desenvolvimento e produção.

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
│   ├── data_normalizer.py    # Normalização e formatação de dados
│   ├── question_generator.py # Geração de perguntas contextuais
│   ├── data_summarizer.py    # Sumarização e análise de dados
│   └── conversation_manager.py # Gestão de estado da conversa
└── main.py                    # Entry point CLI (para testes)

### **Frontend React (Etapa 4)**
```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatPanel.tsx          # Interface de chat responsiva
│   │   ├── ReasoningPanel.tsx     # Debug do reasoning loop
│   │   ├── DataPanel.tsx          # Dados estruturados em tempo real
│   │   └── Layout.tsx             # Layout de 3 colunas responsivo
│   ├── hooks/
│   │   └── useAgentDebug.ts       # Hook para debug do agente
│   ├── services/
│   │   └── api.ts                 # Integração HTTP REST com FastAPI
│   └── App.tsx                    # Componente principal
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── index.html
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
    container_name: postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: data_agent
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped

  # FastAPI backend
  api:
    build: .
    container_name: api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: ${DATABASE_URL:-postgresql://postgres:password@postgres:5432/data_agent}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      OPENAI_MODEL: ${OPENAI_MODEL:-gpt-4o-mini}
      OPENAI_MAX_TOKENS: ${OPENAI_MAX_TOKENS:-500}
    volumes:
      - .:/app
    depends_on:
      - postgres
    networks:
      - app-network
    restart: unless-stopped

  # PostgREST para API automática
  postgrest:
    image: postgrest/postgrest
    container_name: postgrest
    ports:
      - "3000:3000"
    environment:
      PGRST_DB_URI: ${PGRST_DB_URI:-postgresql://postgres:password@postgres:5432/data_agent}
      PGRST_DB_SCHEMA: ${PGRST_DB_SCHEMA:-public}
      PGRST_DB_ANON_ROLE: ${PGRST_DB_ANON_ROLE:-anon}
      PGRST_JWT_SECRET: ${PGRST_JWT_SECRET:-your-jwt-secret}
    depends_on:
      - postgres
    networks:
      - app-network
    restart: unless-stopped

  # React frontend (Etapa 4)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: frontend
    ports:
      - "3001:3001"
    environment:
      VITE_API_URL: ${VITE_API_URL:-http://localhost:8000}
      NODE_ENV: ${NODE_ENV:-development}
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - api
    networks:
      - app-network
    restart: unless-stopped
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
# http://localhost:3001    - Interface React conversacional (Etapa 4)
```

---

## Configuração de Ambiente

### **Variáveis Essenciais**
```bash
# Copiar template de variáveis
cp env.example .env

# Editar .env com suas configurações:
# OPENAI_API_KEY=sua_chave_aqui (OBRIGATÓRIO)
# POSTGRES_PASSWORD=senha_segura (recomendado)
# VITE_API_URL=http://localhost:8000 (padrão)
```

**Variáveis Obrigatórias:**
- `OPENAI_API_KEY`: Chave da API OpenAI para chat conversacional

**Variáveis com Defaults:**
- `POSTGRES_USER=postgres`, `POSTGRES_PASSWORD=password`
- `OPENAI_MODEL=gpt-4o-mini`, `OPENAI_MAX_TOKENS=500`
- `VITE_API_URL=http://localhost:8000`, `NODE_ENV=development`
- `LOG_LEVEL=INFO`, `LOG_FORMAT=json`

---

## Quick Start

### **Execução Completa**
```bash
# Clone e configure
git clone <repository>
cd data-structuring-agent
cp env.example .env
# Editar .env com OPENAI_API_KEY

# Sistema completo (incluindo frontend React)
docker-compose up -d

# URLs de acesso:
# http://localhost:8000    - FastAPI (API + docs)
# http://localhost:3000    - PostgREST (dados diretos)
# http://localhost:3001    - Interface React conversacional (Etapa 4)
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
# Sistema completo via Docker
docker-compose up -d              # Iniciar todos os serviços
docker-compose down               # Parar todos os serviços
docker-compose logs -f api        # Ver logs do backend
docker-compose logs -f frontend   # Ver logs do frontend

# Setup do banco de dados
docker exec api python -m src.main setup-db

# Testes via API (recomendado)
curl -X POST "http://localhost:8000/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Olá, quero marcar uma consulta"}'

# Frontend React (desenvolvimento local - opcional)
cd frontend
npm install
npm run dev          # Desenvolvimento local na porta 3001
npm run build        # Build de produção
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
- Interface React conversacional MVP com transparência do agente (etapa 4)
- Visualização de dados estruturados e reasoning loop em tempo real
- Experiência demonstrável focada em debugging e validação do sistema

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

### **Agent Transparency**
- Interface mostra processo interno do agente (Think → Extract → Validate → Act)
- Debugging visual em tempo real para validação do sistema
- Transparência total para demonstração e otimização
- MVP focado em funcionalidade e visibilidade, não complexidade visual