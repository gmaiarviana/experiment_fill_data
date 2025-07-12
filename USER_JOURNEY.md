# Jornada do Usuário - Data Structuring Agent

## Visão Geral

Sistema conversacional que transforma **conversas naturais** em **dados estruturados**. O usuário conversa naturalmente como no WhatsApp, e o sistema automaticamente extrai, organiza e armazena informações em registros estruturados.

### Conceito Central
- **Input**: Conversa natural e fluida
- **Processamento**: Extração inteligente de entidades e intenções
- **Output**: Dados estruturados (cards/tickets/registros)

---

## Fluxo Principal: Marcar Consulta

### **1. Início da Conversa**

**Usuário inicia naturalmente:**
```
👤 "Oi, preciso marcar uma consulta"
👤 "Quero agendar um horário"
👤 "Preciso de ajuda para marcar consulta pro João"
```

**Sistema responde de forma acolhedora:**
```
🤖 "Claro! Me fale os detalhes da consulta que você quer marcar."
🤖 "Perfeito! Qual consulta você gostaria de agendar?"
```

### **2. Conversa Livre e Extração Inteligente**

**Usuário fornece informações naturalmente:**
```
👤 "É para João Silva, telefone 11999887766, queria para amanhã de manhã"
👤 "Minha mãe Maria, tel (11) 98765-4321, consulta médica na sexta às 14h"
👤 "João da Silva, fone 11 9 9988 7766, dermatologista, qualquer dia da próxima semana"
```

**Sistema processa e extrai automaticamente:**
- **Nome**: João Silva, Maria, João da Silva
- **Telefone**: 11999887766 → formatado para (11) 99988-7766
- **Data**: "amanhã" → 15/01/2025, "sexta" → 17/01/2025, "próxima semana" → range disponível
- **Horário**: "manhã" → necessita esclarecimento, "14h" → 14:00, "qualquer dia" → flexível
- **Tipo**: inferido como "consulta médica", "dermatologista"

### **3. Esclarecimento Inteligente (Quando Necessário)**

**Sistema identifica informações faltantes e pergunta especificamente:**
```
🤖 "Entendi! João Silva, tel. (11) 99988-7766, para amanhã de manhã.
    Que tipo de consulta é? E qual horário específico você prefere?"

🤖 "Perfeito! Para João da Silva na próxima semana com dermatologista.
    Qual dia específico você prefere? E que horário?"
```

**Usuário completa naturalmente:**
```
👤 "Consulta médica, pode ser 9h"
👤 "Terça-feira, 10h da manhã seria ideal"
```

### **4. Confirmação Estruturada**

**Sistema apresenta dados estruturados para validação:**
```
🤖 "Perfeito! Vou marcar:
    📋 Paciente: João Silva
    📞 Telefone: (11) 99988-7766  
    📅 Data: 15/01/2025 (amanhã)
    🕘 Horário: 09:00
    🏥 Tipo: Consulta médica
    
    Confirma?"
```

**Usuário confirma ou corrige:**
```
👤 "Confirma"
👤 "Pode ser 9h30 ao invés de 9h?"
```

### **5. Finalização e Registro**

**Sistema cria registro e confirma:**
```
🤖 "✅ Consulta marcada com sucesso! 
    ID: #001
    Você receberá uma confirmação no telefone cadastrado."
```

---

## Campos de Dados Estruturados

### **Consulta Médica - Campos Obrigatórios**
- **nome**: Nome completo do paciente
- **telefone**: Telefone para contato (formatado)
- **data**: Data da consulta (formato YYYY-MM-DD)
- **horario**: Horário específico (formato HH:MM)
- **tipo_consulta**: Tipo de consulta ou especialidade

### **Campos Opcionais**
- **observacoes**: Observações específicas do usuário
- **medico_preferido**: Preferência de médico específico
- **convenio**: Convênio médico (se aplicável)
- **urgencia**: Nível de urgência (normal, urgente, emergência)

### **Metadados Automáticos**
- **id**: ID único gerado automaticamente
- **status**: created, confirmed, cancelled
- **created_at**: Timestamp de criação
- **session_id**: Identificador da sessão de chat
- **confidence_score**: Confiança na extração (0.0-1.0)

---

## Capacidades do Sistema

### **Extração Inteligente de Entidades**
- **Nomes**: João Silva, Maria Santos, Dr. Carlos
- **Telefones**: 11999887766 → (11) 99988-7766
- **Datas Relativas**: "amanhã", "próxima sexta", "semana que vem"
- **Horários**: "manhã", "14h", "meio-dia", "final da tarde"
- **Especialidades**: "dermatologista", "cardiologista", "clínico geral"

### **Normalização Automática**
- **Telefones**: Formatos diversos → padrão (XX) XXXXX-XXXX
- **Datas**: Linguagem natural → formato ISO (YYYY-MM-DD)
- **Horários**: Descrições → formato 24h (HH:MM)
- **Nomes**: Capitalização adequada

### **Validação Inteligente**
- **Datas**: Não pode ser no passado (exceto histórico)
- **Telefones**: Formato brasileiro válido
- **Horários**: Dentro do horário comercial
- **Campos obrigatórios**: Todos preenchidos antes da confirmação

### **Context Awareness**
- **Sessão**: Lembra informações durante a conversa
- **Usuário**: Reconhece padrões do usuário específico
- **Histórico**: Aprende com interações anteriores

---

## Casos de Uso Especiais

### **Múltiplas Consultas em uma Conversa**
```
👤 "Quero marcar duas consultas: uma para mim João (11) 99999-1111 
    na terça 10h, e outra para minha esposa Maria (11) 99999-2222 
    na quarta 14h, ambas clínico geral"

🤖 "Entendi! Duas consultas:
    📋 Consulta 1: João, (11) 99999-1111, Terça 10:00, Clínico Geral
    📋 Consulta 2: Maria, (11) 99999-2222, Quarta 14:00, Clínico Geral
    
    Confirma ambas?"
```

### **Informações Incompletas**
```
👤 "Quero marcar consulta para semana que vem"

🤖 "Claro! Para qual pessoa? E você tem preferência de dia e horário?"

👤 "Para João, qualquer dia de manhã"

🤖 "Perfeito! João para manhã da próxima semana. 
    Preciso do telefone dele e que tipo de consulta é."
```

### **Correções Durante o Processo**
```
👤 "Não, não é João Silva, é João Santos"

🤖 "Entendido! Corrigi para João Santos. Os outros dados estão corretos?"
```

---

## Fluxos de Erro e Recovery

### **Informação Inválida**
```
👤 "Para ontem às 25h"

🤖 "Vi que você mencionou 'ontem' e '25h'. 
    Consultas precisam ser para datas futuras e horários válidos (00:00-23:59).
    Você poderia me dar uma data futura e horário correto?"
```

### **Dados Conflitantes**
```
👤 "João Silva, telefone 11999887766, para amanhã... 
    Na verdade é João Santos, telefone 11888776655"

🤖 "Entendi que você corrigiu:
    João Silva → João Santos
    (11) 99988-7766 → (11) 88877-6655
    
    Está correto agora?"
```

### **Desistência/Cancelamento**
```
👤 "Deixa pra lá, não quero mais marcar"

🤖 "Sem problemas! Se precisar marcar algo depois, é só falar comigo. 
    Posso ajudar com mais alguma coisa?"
```

---

## Extensibilidade Futura

### **Outras Ações Planejadas**
- **Cancelar Consulta**: "Quero cancelar a consulta do João"
- **Reagendar**: "Preciso mudar a consulta da Maria para outro dia"
- **Consultar Agenda**: "Que consultas tenho marcadas essa semana?"
- **Criar Lembretes**: "Me lembra da consulta 1 hora antes"

### **Outros Domínios de Aplicação**
- **Gestão de Tarefas**: Transcrição de reunião → tickets no Jira
- **Atendimento ao Cliente**: Chat → tickets de suporte estruturados
- **Vendas**: Conversa comercial → leads qualificados no CRM
- **RH**: Entrevista → avaliação estruturada de candidato
- **Financeiro**: Solicitações → orçamentos e propostas organizadas

### **Modalidades Futuras**
- **Áudio**: Chamadas telefônicas → consultas estruturadas
- **E-mail**: Mensagens de e-mail → ações organizadas
- **WhatsApp**: Integração direta com API do WhatsApp Business
- **Voz**: Assistente de voz → comandos executados

---

## Métricas de Sucesso

### **Eficiência**
- **Taxa de Extração Correta**: >90% dos campos extraídos corretamente
- **Tempo Médio de Conversa**: <3 minutos por consulta
- **Taxa de Confirmação**: >95% das extrações confirmadas pelo usuário

### **Experiência do Usuário**
- **Satisfação**: Conversa natural sem fricção
- **Aprendizado**: Sistema melhora com uso (menos esclarecimentos)
- **Confiabilidade**: Dados estruturados sempre corretos

### **Técnicas**
- **Confiança na Extração**: Score médio >0.8
- **Cobertura de Entidades**: Todos os campos obrigatórios identificados
- **Robustez**: Sistema funciona com diferentes estilos de linguagem