from typing import List, Dict, Any
from loguru import logger


class QuestionGenerator:
    """
    Gerador de perguntas para guiar a conversação de forma natural e contextual.
    """
    
    def __init__(self):
        """
        Inicializa o gerador de perguntas com templates e mapeamentos.
        """
        # Mapeamento de campos para perguntas amigáveis
        self.field_questions = {
            "nome": "Qual é o nome completo do paciente?",
            "telefone": "Qual é o telefone para contato?", 
            "data": "Para qual data você gostaria de agendar?",
            "horario": "Qual horário prefere?",
            "tipo_consulta": "Que tipo de consulta é esta?"
        }
        
        # Templates para diferentes contextos
        self.context_templates = {
            "welcome": [
                "Olá! Vou te ajudar a agendar sua consulta. Para começar, qual é o nome do paciente?",
                "Oi! Vou te auxiliar no agendamento. Primeiro, preciso saber o nome do paciente.",
                "Perfeito! Vamos agendar sua consulta. Qual é o nome completo do paciente?"
            ],
            "progress_single": [
                "Ótimo! Agora preciso do {field}.",
                "Perfeito! Agora me informe o {field}.",
                "Excelente! Agora preciso saber o {field}."
            ],
            "progress_multiple": [
                "Já tenho {count} informações. Ainda preciso de: {fields}.",
                "Ótimo progresso! Com {count} dados coletados, agora preciso de: {fields}.",
                "Perfeito! Já tenho {count} informações. Falta apenas: {fields}."
            ],
            "data_summary": [
                "Perfeito! {summary}. Agora preciso de: {missing}.",
                "Excelente! {summary}. Para completar, preciso de: {missing}.",
                "Ótimo! {summary}. Ainda preciso de: {missing}."
            ],
            "correction": [
                "Entendi, vou corrigir. Pode me informar novamente os dados corretos?",
                "Claro! Vou ajustar. Pode me passar as informações corretas?",
                "Perfeito! Vou corrigir. Pode me informar os dados certos?"
            ],
            "confirmation": [
                "Perfeito! Tenho todas as informações. Posso confirmar o agendamento?",
                "Excelente! Agendamento completo. Posso prosseguir com a confirmação?",
                "Ótimo! Tenho todos os dados necessários. Posso confirmar?"
            ],
            "complete": [
                "Perfeito! Agendamento confirmado com sucesso! ✅",
                "Excelente! Consulta agendada com sucesso! ✅",
                "Ótimo! Agendamento realizado com sucesso! ✅"
            ]
        }
        
        logger.info("QuestionGenerator inicializado com templates e mapeamentos")
    
    def get_missing_fields_questions(self, missing_fields: List[str], context: Dict[str, Any] = None) -> List[str]:
        """
        Gera perguntas específicas para campos faltantes.
        
        Args:
            missing_fields: Lista de campos que ainda precisam ser preenchidos
            context: Contexto da conversa (opcional)
            
        Returns:
            Lista de perguntas para os campos faltantes
        """
        questions = []
        
        for field in missing_fields:
            if field in self.field_questions:
                questions.append(self.field_questions[field])
            else:
                questions.append(f"Qual é o {field}?")
        
        return questions
    
    def generate_contextual_question(self, template_type: str, **kwargs) -> str:
        """
        Gera uma pergunta contextual usando templates.
        
        Args:
            template_type: Tipo de template a usar
            **kwargs: Parâmetros para formatar o template
            
        Returns:
            Pergunta formatada
        """
        import random
        
        if template_type not in self.context_templates:
            logger.warning(f"Template type '{template_type}' não encontrado")
            return "Desculpe, não consegui processar sua mensagem."
        
        templates = self.context_templates[template_type]
        template = random.choice(templates)
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Erro ao formatar template {template_type}: {e}")
            return templates[0] if templates else "Desculpe, não consegui processar sua mensagem."
    
    def generate_data_summary_question(self, extracted_data: Dict[str, Any], missing_fields: List[str]) -> str:
        """
        Gera uma pergunta que resume dados já coletados e solicita campos faltantes.
        
        Args:
            extracted_data: Dados já extraídos
            missing_fields: Campos que ainda faltam
            
        Returns:
            Pergunta contextual com resumo
        """
        # Cria resumo dos dados já coletados
        summary_parts = []
        
        if extracted_data.get("nome"):
            summary_parts.append(f"nome: {extracted_data['nome']}")
        if extracted_data.get("telefone"):
            summary_parts.append(f"telefone: {extracted_data['telefone']}")
        if extracted_data.get("data"):
            summary_parts.append(f"data: {extracted_data['data']}")
        if extracted_data.get("horario"):
            summary_parts.append(f"horário: {extracted_data['horario']}")
        if extracted_data.get("tipo_consulta"):
            summary_parts.append(f"tipo: {extracted_data['tipo_consulta']}")
        
        summary = ", ".join(summary_parts) if summary_parts else "algumas informações"
        
        # Gera perguntas para campos faltantes
        missing_questions = self.get_missing_fields_questions(missing_fields)
        missing_text = ", ".join(missing_questions)
        
        return self.generate_contextual_question("data_summary", summary=summary, missing=missing_text)
    
    def generate_specific_question(self, field: str, context: Dict[str, Any] = None) -> str:
        """
        Gera uma pergunta específica para um campo.
        
        Args:
            field: Campo para o qual gerar a pergunta
            context: Contexto da conversa (opcional)
            
        Returns:
            Pergunta específica para o campo
        """
        if field in self.field_questions:
            return self.field_questions[field]
        else:
            return f"Qual é o {field}?"
    
    def should_ask_specific_question(self, message: str, context: Dict[str, Any]) -> bool:
        """
        Determina se deve fazer uma pergunta específica baseada no contexto.
        
        Args:
            message: Mensagem do usuário
            context: Contexto da conversa
            
        Returns:
            True se deve fazer pergunta específica
        """
        # Se o usuário está repetindo a pergunta ou pedindo detalhes
        message_lower = message.lower()
        if any(word in message_lower for word in ["detalhes", "específico", "mais", "qual"]):
            return True
        
        # Se a última ação foi perguntar e o usuário não respondeu adequadamente
        conversation_history = context.get("conversation_history", [])
        if conversation_history and conversation_history[-1].get("action") == "ask":
            return True
        
        return False 