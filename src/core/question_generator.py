from typing import List, Dict, Any
from loguru import logger


class QuestionGenerator:
    """
    Gerador de perguntas para guiar a conversação de forma natural e contextual.
    """
    
    def __init__(self):
        self.field_questions = {
            "nome": "Qual é o nome completo do paciente?",
            "telefone": "Qual é o telefone para contato?", 
            "data": "Para qual data você gostaria de agendar?",
            "horario": "Qual horário prefere?",
            "tipo_consulta": "Que tipo de consulta é esta?"
        }
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
            "progress_last": [
                "Agora só falta o {field}!",
                "Estamos quase lá! Só preciso do {field} para finalizar.",
                "Para concluir, só falta o {field}."
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
            ],
            "specific_request": [
                "Claro! Preciso especificamente de: {fields}",
                "Entendi! Para completar, preciso de: {fields}",
                "Perfeito! Agora preciso de: {fields}"
            ],
            "summary_before_confirm": [
                "Resumo do agendamento: {summary}. Posso confirmar?",
                "Confira os dados: {summary}. Está tudo correto para confirmar?",
                "Antes de confirmar, revise: {summary}. Posso agendar?"
            ]
        }
        logger.info("QuestionGenerator inicializado com templates e mapeamentos")

    def get_missing_fields_questions(self, missing_fields: List[str], context: Dict[str, Any] = None) -> List[str]:
        questions = []
        for field in missing_fields:
            if field in self.field_questions:
                questions.append(self.field_questions[field])
            else:
                questions.append(f"Qual é o {field}?")
        return questions

    def generate_contextual_question(self, template_type: str, **kwargs) -> str:
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

    def generate_data_summary(self, extracted_data: Dict[str, Any]) -> str:
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
        return ", ".join(summary_parts) if summary_parts else "(sem dados)"

    def generate_data_summary_question(self, extracted_data: Dict[str, Any], missing_fields: List[str]) -> str:
        summary = self.generate_data_summary(extracted_data)
        missing_questions = self.get_missing_fields_questions(missing_fields)
        missing_text = ", ".join(missing_questions)
        return self.generate_contextual_question("data_summary", summary=summary, missing=missing_text)

    def generate_progress_question(self, extracted_data: Dict[str, Any], missing_fields: List[str], context: Dict[str, Any] = None) -> str:
        completed_count = len([v for v in extracted_data.values() if v and str(v).strip()])
        total_fields = 5
        if completed_count == 0:
            return self.generate_contextual_question("welcome")
        elif completed_count == total_fields - 1 and len(missing_fields) == 1:
            # Só falta um campo
            field = missing_fields[0]
            field_names = {
                "nome": "nome completo",
                "telefone": "telefone",
                "data": "data",
                "horario": "horário",
                "tipo_consulta": "tipo de consulta"
            }
            field_name = field_names.get(field, field)
            return self.generate_contextual_question("progress_last", field=field_name)
        elif completed_count >= 2:
            return self.generate_data_summary_question(extracted_data, missing_fields)
        if missing_fields:
            return self.generate_contextual_question("specific_request", fields=", ".join(missing_fields[:2]))
        else:
            return self.generate_contextual_question("confirmation")

    def generate_summary_before_confirm(self, extracted_data: Dict[str, Any]) -> str:
        summary = self.generate_data_summary(extracted_data)
        return self.generate_contextual_question("summary_before_confirm", summary=summary) 