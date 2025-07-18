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

## ✅ **ETAPA 3: EXTRAÇÃO INTELIGENTE - CONCLUÍDA**

**Objetivo**: Sistema extrai dados estruturados de conversas naturais usando abordagem híbrida LLM + código, com persistência automática e framework extensível.

**Funcionalidades Implementadas:**
- ✅ **LLM Entity Extraction**: OpenAI function calling para extração de entidades de linguagem natural
- ✅ **Smart Validation & Normalization**: Validação e normalização automática de dados brasileiros
- ✅ **Intelligent Reasoning Loop**: Loop Think → Extract → Validate → Act com context awareness
- ✅ **PostgreSQL Schema Setup**: Schema completo com 3 tabelas (consultas, extraction_logs, chat_sessions)
- ✅ **Data Persistence**: Repository pattern com persistência automática via ConsultationService
- ✅ **Complete Chat Integration**: Sistema conversacional completo com session management e persistência

**Resultado Alcançado**: Sistema conversacional que converte linguagem natural em dados estruturados automaticamente, persiste registros organizados e mantém conversação natural com context awareness.

---

## 🎯 **ETAPA 4: INTERFACE CONVERSACIONAL - PRÓXIMA ETAPA**

**Objetivo**: Interface visual MVP para conversação com transparência total do agente, permitindo ver o reasoning loop e dados estruturados em tempo real.

**Funcionalidades Planejadas:**

### ✅ Funcionalidade 4.1: Interface de Chat Básica
**Critérios de Aceite:**
- Interface de chat responsiva com input de mensagem e histórico de conversa
- Indicador visual de "processando" durante extração pelo agente
- Design limpo e mobile-friendly sem complexidade visual desnecessária
- Integração básica com endpoint `/chat/message` do FastAPI

**Status:** ✅ IMPLEMENTADA
- Interface React criada com Vite, TypeScript e Tailwind
- Integração CORS ajustada para porta 3001
- Testes manuais realizados com sucesso

### ✅ Funcionalidade 4.2: Painel de Debug do Reasoning Loop
**Critérios de Aceite:**
- Painel lateral mostrando os 4 passos do reasoning (Think → Extract → Validate → Act) em tempo real
- Logs detalhados com timestamps de cada etapa do processo
- Status visual de cada passo (running/completed/error) com indicadores de cor
- Exibição apenas do último ciclo completo de reasoning (sem persistência histórica)
- Detalhes relevantes incluídos: entidades extraídas, campos faltantes, ações tomadas

**Status:** ✅ IMPLEMENTADA
- Painel Reasoning Loop Debug implementado em React com integração ao backend
- Exibe os 4 passos do reasoning, status, timestamps e detalhes do ciclo atual
- Integração em tempo real com o endpoint /chat/message
- Transparência total do reasoning loop para debugging e demonstração

### ✅ Funcionalidade 4.3: Painel de Dados Estruturados
**Critérios de Aceite:**
- Painel lateral mostrando dados extraídos em tempo real
- Campos obrigatórios vs opcionais claramente identificados
- Confidence score visual (0-100%) com indicadores de cor para cada campo
- Status de validação (✓/❌/⏳) para cada campo extraído
- Exibição apenas de dados finais normalizados (sem dados brutos)

**Status:** ✅ IMPLEMENTADA
- Componente StructuredDataPanel criado com TypeScript e Tailwind
- Layout de 3 colunas implementado: Chat (2/4) | Reasoning (1/4) | Dados (1/4)
- Validação visual de campos com indicadores de status e confidence score
- Integração completa com backend via lastResponse.extracted_data

### Funcionalidade 4.4: Integração Backend e Polling Inteligente
**Critérios de Aceite Sugeridos:**
- Integração HTTP REST simples com FastAPI (sem WebSocket inicial)
- Polling inteligente: 500ms durante processamento, 2s em idle
- Session management básico com session_id automático
- Tratamento de erros simples com retry automático
- Layout de 3 colunas responsivo (Chat | Reasoning | Dados)

**Resultado Esperado**: Interface MVP que permite conversar naturalmente com o agente enquanto visualiza seu processo de reasoning e acompanha dados sendo extraídos em tempo real, criando transparência total para debugging e demonstração.

---

## 🎯 **ETAPA 5: CONVERSAÇÃO NATURAL - PLANEJADA**

**Objetivo**: Transformar o sistema de robótico para fluido e natural, focando na experiência do usuário final sem comprometer a arquitetura técnica.

**Funcionalidades Planejadas:**

### Funcionalidade 5.1: Modularização do ReasoningEngine
**Critérios de Aceite:**
- Refatorar `ReasoningEngine` (600+ linhas) em módulos especializados
- Criar `src/core/reasoning/` com componentes modulares:
  - `reasoning_coordinator.py`: Orquestra Think→Extract→Validate→Act
  - `llm_strategist.py`: Strategy pattern para LLM reasoning
  - `conversation_flow.py`: Gerencia fluxo natural da conversa
  - `response_composer.py`: Compõe respostas naturais e contextuais
  - `fallback_handler.py`: Lógica Python quando LLM falha
- Manter compatibilidade 100% com sistema atual
- Código mais limpo, testável e fácil de manter
- Zero breaking changes na API existente

### Funcionalidade 5.2: Processamento Inteligente de Datas e Horários
**Critérios de Aceite:**
- Processar expressões naturais automaticamente:
  - "amanhã" → data específica calculada
  - "próxima sexta" → data correta identificada
  - "semana que vem" → range de datas válidas
  - "de manhã", "à tarde" → horários sugeridos
- Validação contextual (não permitir datas passadas)
- Confirmação automática quando ambíguo ("manhã = 9h ou 10h?")
- Integração transparente com sistema de normalização existente
- Usuário nunca vê dados "brutos" - só confirmação final

### Funcionalidade 5.3: Respostas Naturais e Contextuais
**Critérios de Aceite:**
- Eliminar respostas "técnicas" com dados extraídos explícitos
- Progressão contextual fluida:
  ```
  ❌ "Já tenho: nome: João Silva, telefone: (11) 99999-9999. Ainda preciso de: data, horário"
  ✅ "Perfeito, João! Para qual data você gostaria de agendar?"
  ```
- Sistema "lembra" do contexto sem repetir informações
- Confirmação final apresenta resumo organizado
- Tom conversacional amigável e profissional
- Variação nas respostas (não robotizado)

### Funcionalidade 5.4: Fluxo Conversacional Otimizado
**Critérios de Aceite:**
- Detecção inteligente de intenção sem perguntas desnecessárias
- Antecipação de próximos passos baseada no contexto
- Correções e mudanças tratadas naturalmente
- Confirmação inteligente apenas quando necessário
- Zero loops de perguntas repetitivas
- Experiência similar a WhatsApp Business

**Resultado Esperado**: Sistema conversacional indistinguível de atendimento humano qualificado, mantendo toda a robustez técnica com experiência do usuário superior.

---

## 🎯 **ETAPA 6: MEMORY CONVERSACIONAL - PLANEJADA**

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