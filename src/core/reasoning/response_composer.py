"""
ResponseComposer - Compõe respostas naturais e contextuais
Gera respostas conversacionais baseadas no contexto e resultados do reasoning.
"""

from typing import Dict, Any, Optional, List
import random
from src.core.logging.logger_factory import get_logger
logger = get_logger(__name__)
class ResponseComposer:
    """
    Compositor de respostas que gera diálogo natural e contextual.
    Consolidado com funcionalidades de geração de perguntas.
    """
    
    def __init__(self):
        """
        Inicializa o compositor de respostas.
        """
        
        # Templates para variação de respostas
        self.confirmation_templates = [
            "Perfeito!",
            "Ótimo!",
            "Excelente!",
            "Muito bem!",
            "Anotado!",
            "Entendi!",
            "Certo!",
            "Beleza!"
        ]
        
        self.next_question_templates = [
            "Para qual data você gostaria de agendar?",
            "Que dia seria melhor para você?",
            "Qual data funciona melhor?",
            "Quando você gostaria de vir?",
            "Para quando você quer marcar?"
        ]
        
        self.name_question_templates = [
            "Qual é o seu nome?",
            "Como você se chama?",
            "Pode me dizer seu nome?",
            "Qual é o seu nome completo?",
            "Como posso te chamar?"
        ]
        
        self.phone_question_templates = [
            "Qual é o seu telefone?",
            "Pode me passar seu número?",
            "Qual é o seu celular?",
            "Me informe seu telefone para contato",
            "Qual número posso usar para te contatar?"
        ]
        
        self.time_question_templates = [
            "Que horário seria melhor?",
            "Qual horário funciona para você?",
            "Que horas você prefere?",
            "Qual horário seria ideal?",
            "Que tal às 14h ou 15h?"
        ]
        
        self.consultation_question_templates = [
            "Que tipo de consulta você precisa?",
            "Qual é o motivo da consulta?",
            "Que tipo de atendimento você busca?",
            "Qual especialidade você precisa?",
            "Que tipo de avaliação você quer?"
        ]
        
        # Templates contextuais consolidados do QuestionGenerator
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
            ]
        }
        
        # Mapeamento de campos para perguntas
        self.field_questions = {
            "nome": "Qual é o nome completo do paciente?",
            "telefone": "Qual é o telefone para contato?", 
            "data": "Para qual data você gostaria de agendar?",
            "horario": "Qual horário prefere?",
            "tipo_consulta": "Que tipo de consulta é esta?"
        }
        
        logger.info("ResponseComposer inicializado com templates consolidados de geração de perguntas")
    
    async def compose_response(self, think_result: Dict[str, Any], extract_result: Optional[Dict[str, Any]], 
                             validate_result: Optional[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compõe resposta final baseada nos resultados de todas as fases.
        
        Args:
            think_result (Dict[str, Any]): Resultado da análise THINK
            extract_result (Optional[Dict[str, Any]]): Resultado da extração
            validate_result (Optional[Dict[str, Any]]): Resultado da validação
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resposta final e ação decidida
        """
        try:
            action = think_result.get("action", "error")
            
            # Compõe resposta baseada na ação
            if action == "extract":
                return await self._compose_extract_response(think_result, extract_result, validate_result, context)
            elif action == "ask":
                return await self._compose_ask_response(think_result, context)
            elif action == "confirm":
                return await self._compose_confirm_response(think_result, context)
            elif action == "complete":
                return await self._compose_complete_response(think_result, context)
            elif action == "error":
                return self._compose_error_response(think_result)
            else:
                return self._compose_fallback_response(think_result, context)
                
        except Exception as e:
            logger.error(f"Erro no ResponseComposer: {str(e)}")
            return {
                "action": "error",
                "response": "Desculpe, ocorreu um erro interno. Pode tentar novamente?",
                "error": str(e),
                "confidence": 0.0
            }
    
    async def _compose_extract_response(self, think_result: Dict[str, Any], extract_result: Optional[Dict[str, Any]], 
                                      validate_result: Optional[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compõe resposta para ação de extração, usando completion_strategy do contexto.
        """
        extracted_data = extract_result.get("extracted_data", {}) if extract_result else {}
        validation_errors = validate_result.get("validation_errors", []) if validate_result else []
        completion_strategy = context.get("completion_strategy")
        progression_pattern = context.get("progression_pattern", "indefinido")
        # Se há erros de validação, solicita correção
        if validation_errors:
            error_message = self._format_validation_errors(validation_errors)
            return {
                "action": "extract",
                "response": f"Entendi! Mas preciso de algumas correções: {error_message}",
                "extracted_data": extracted_data,
                "validation_errors": validation_errors,
                "confidence": think_result.get("confidence", 0.5)
            }
        # Se extraiu dados válidos, confirma e pergunta próximo campo
        if extracted_data:
            correction_msg = self._detect_correction_context(context, extracted_data)
            if completion_strategy:
                next_step = completion_strategy
            else:
                next_step = self._get_next_question(context, extracted_data)
            confirmation = self._create_smart_confirmation(extracted_data, context)
            response = f"{confirmation} {next_step}"
            if correction_msg:
                response = f"{correction_msg} {response}"
            # Adiciona resposta antecipatória se padrão for randômico
            if progression_pattern == "randômico":
                anticipatory = self._create_anticipatory_response(context, extracted_data)
                response = f"{confirmation} {anticipatory}"
            return {
                "action": "extract",
                "response": response,
                "extracted_data": extracted_data,
                "validation_errors": [],
                "confidence": think_result.get("confidence", 0.8)
            }
        # Se não extraiu nada, pergunta diretamente
        return await self._compose_ask_response(think_result, context)
    
    async def _compose_ask_response(self, think_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compõe resposta para ação de pergunta.
        
        Args:
            think_result (Dict[str, Any]): Resultado da análise
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resposta para pergunta
        """
        missing_fields = think_result.get("missing_fields", [])
        existing_data = context.get("extracted_data", {})
        
        if missing_fields:
            # Gera pergunta específica para o próximo campo
            next_field = missing_fields[0]
            question = self._generate_field_question(next_field, existing_data)
            
            return {
                "action": "ask",
                "response": question,
                "missing_fields": missing_fields,
                "confidence": think_result.get("confidence", 0.7),
                "extracted_data": existing_data  # INCLUIR DADOS EXTRAÍDOS
            }
        else:
            # Fallback se não há campos específicos
            return {
                "action": "ask",
                "response": random.choice(self.name_question_templates),
                "missing_fields": ["nome"],
                "confidence": think_result.get("confidence", 0.5),
                "extracted_data": existing_data  # INCLUIR DADOS EXTRAÍDOS
            }
    
    async def _compose_confirm_response(self, think_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compõe resposta para ação de confirmação.
        
        Args:
            think_result (Dict[str, Any]): Resultado da análise
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resposta para confirmação
        """
        existing_data = context.get("extracted_data", {})
        
        # Cria resumo dos dados para confirmação
        data_summary = self._create_confirmation_summary(existing_data)
        
        response = f"Perfeito! Vou confirmar os dados da sua consulta:\n\n{data_summary}\n\nEstá tudo correto?"
        
        return {
            "action": "confirm",
            "response": response,
            "extracted_data": existing_data,
            "confidence": think_result.get("confidence", 0.9)
        }
    
    async def _compose_complete_response(self, think_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compõe resposta para ação de finalização.
        
        Args:
            think_result (Dict[str, Any]): Resultado da análise
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resposta para finalização
        """
        existing_data = context.get("extracted_data", {})
        
        # Cria resumo final
        final_summary = self._create_final_summary(existing_data)
        
        response = f"Excelente! Sua consulta foi agendada com sucesso:\n\n{final_summary}\n\nObrigado por escolher nossos serviços!"
        
        return {
            "action": "complete",
            "response": response,
            "extracted_data": existing_data,
            "confidence": think_result.get("confidence", 1.0)
        }
    
    def _compose_error_response(self, think_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compõe resposta para ação de erro.
        
        Args:
            think_result (Dict[str, Any]): Resultado da análise
            
        Returns:
            Dict: Resposta de erro
        """
        error_message = think_result.get("error", "Erro desconhecido")
        
        return {
            "action": "error",
            "response": f"Desculpe, ocorreu um erro: {error_message}. Pode tentar novamente?",
            "error": error_message,
            "confidence": 0.0
        }
    
    def _compose_fallback_response(self, think_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compõe resposta de fallback para ações não reconhecidas.
        
        Args:
            think_result (Dict[str, Any]): Resultado da análise
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resposta de fallback
        """
        return {
            "action": "ask",
            "response": "Desculpe, não entendi completamente. Pode reformular sua mensagem?",
            "confidence": 0.3
        }
    
    def _create_extraction_confirmation(self, extracted_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Cria confirmação natural dos dados extraídos sem expor dados técnicos.
        
        Args:
            extracted_data (Dict[str, Any]): Dados extraídos
            context (Dict[str, Any]): Contexto da conversa
            
        Returns:
            str: Confirmação natural
        """
        # Identifica o tipo de dado extraído para confirmação contextual
        if "nome" in extracted_data:
            nome = extracted_data["nome"]
            # Extrai primeiro nome para uso mais pessoal
            primeiro_nome = nome.split()[0] if nome else "você"
            return f"{random.choice(self.confirmation_templates)} {primeiro_nome}!"
        
        elif "telefone" in extracted_data:
            return f"{random.choice(self.confirmation_templates)} Anotei seu telefone!"
        
        elif "data" in extracted_data:
            return f"{random.choice(self.confirmation_templates)} Data anotada!"
        
        elif "horario" in extracted_data:
            return f"{random.choice(self.confirmation_templates)} Horário perfeito!"
        
        elif "tipo_consulta" in extracted_data:
            return f"{random.choice(self.confirmation_templates)} Entendi o tipo de consulta!"
        
        # Confirmação genérica para múltiplos campos
        else:
            return f"{random.choice(self.confirmation_templates)} Anotei as informações!"
    
    def _get_next_question(self, context: Dict[str, Any], extracted_data: Dict[str, Any]) -> str:
        """
        Gera próxima pergunta com progressão contextual fluida e baseada no padrão de progressão.
        """
        all_data = context.get("extracted_data", {}).copy()
        all_data.update(extracted_data)
        missing_fields = self._get_missing_fields(all_data)
        progression_pattern = context.get("progression_pattern", "indefinido")
        if not missing_fields:
            return "Agora posso confirmar os dados da sua consulta?"
        next_field = missing_fields[0]
        # Variação baseada no padrão de progressão
        if progression_pattern == "sequencial":
            if next_field == "data" and "nome" in all_data:
                nome = all_data["nome"]
                primeiro_nome = nome.split()[0] if nome else "você"
                return f"{primeiro_nome}, para qual data você gostaria de agendar?"
            elif next_field == "horario" and "data" in all_data:
                return f"Que horário seria melhor para o dia {all_data['data']}?"
            elif next_field == "tipo_consulta" and "nome" in all_data:
                nome = all_data["nome"]
                primeiro_nome = nome.split()[0] if nome else "você"
                return f"{primeiro_nome}, que tipo de consulta você precisa?"
            else:
                return self._generate_field_question(next_field, all_data)
        elif progression_pattern == "randômico":
            # Para padrão randômico, sugere resumo e pergunta aberta
            summary = self._create_confirmation_summary(all_data)
            return f"Ótimo! Já tenho: {summary}. Qual informação deseja informar agora?"
        else:
            return self._generate_field_question(next_field, all_data)
    
    def _get_missing_fields(self, data: Dict[str, Any]) -> List[str]:
        """
        Identifica campos obrigatórios que estão faltando.
        
        Args:
            data (Dict[str, Any]): Dados atuais
            
        Returns:
            List[str]: Lista de campos faltantes
        """
        required_fields = ["nome", "telefone", "data", "horario", "tipo_consulta"]
        return [field for field in required_fields if not data.get(field)]
    
    def _generate_field_question(self, field: str, existing_data: Dict[str, Any]) -> str:
        """
        Gera pergunta específica para um campo com variação.
        
        Args:
            field (str): Campo para perguntar
            existing_data (Dict[str, Any]): Dados já coletados
            
        Returns:
            str: Pergunta formatada com variação
        """
        if field == "nome":
            return random.choice(self.name_question_templates)
        elif field == "telefone":
            return random.choice(self.phone_question_templates)
        elif field == "data":
            return random.choice(self.next_question_templates)
        elif field == "horario":
            return random.choice(self.time_question_templates)
        elif field == "tipo_consulta":
            return random.choice(self.consultation_question_templates)
        else:
            return f"Pode me informar o {field}?"
    
    def _create_confirmation_summary(self, data: Dict[str, Any]) -> str:
        """
        Cria resumo organizado e amigável para confirmação.
        
        Args:
            data (Dict[str, Any]): Dados para confirmar
            
        Returns:
            str: Resumo formatado e amigável
        """
        summary_parts = []
        
        if "nome" in data and data["nome"]:
            summary_parts.append(f"👤 **Paciente:** {data['nome']}")
        
        if "telefone" in data and data["telefone"]:
            summary_parts.append(f"📞 **Telefone:** {data['telefone']}")
        
        if "data" in data and data["data"]:
            summary_parts.append(f"📅 **Data:** {data['data']}")
        
        if "horario" in data and data["horario"]:
            summary_parts.append(f"🕐 **Horário:** {data['horario']}")
        
        if "tipo_consulta" in data and data["tipo_consulta"]:
            summary_parts.append(f"🏥 **Tipo de consulta:** {data['tipo_consulta']}")
        
        return "\n".join(summary_parts)
    
    def _create_final_summary(self, data: Dict[str, Any]) -> str:
        """
        Cria resumo final para confirmação.
        
        Args:
            data (Dict[str, Any]): Dados finais
            
        Returns:
            str: Resumo final formatado
        """
        return self._create_confirmation_summary(data)
    
    def _format_validation_errors(self, errors: List[str]) -> str:
        """
        Formata erros de validação para exibição.
        
        Args:
            errors (List[str]): Lista de erros
            
        Returns:
            str: Erros formatados
        """
        if len(errors) == 1:
            return errors[0]
        else:
            return "; ".join(errors[:-1]) + f" e {errors[-1]}" 

    def _create_smart_confirmation(self, extracted_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Cria confirmação inteligente usando antecipação contextual do próximo campo.
        """
        anticipated_next = context.get("anticipated_next", [])
        confirmation = self._create_extraction_confirmation(extracted_data, context)
        if anticipated_next:
            next_field = anticipated_next[0]
            next_hint = self._generate_field_question(next_field, extracted_data)
            return f"{confirmation} {next_hint}"
        return confirmation

    def _detect_correction_context(self, context: Dict[str, Any], new_data: Dict[str, Any]) -> Optional[str]:
        """
        Detecta se houve correção de dados e retorna mensagem apropriada.
        """
        previous_data = context.get("extracted_data", {})
        corrections = []
        for key, value in new_data.items():
            if key in previous_data and previous_data[key] != value:
                corrections.append(key)
        if corrections:
            fields = ", ".join([self._get_field_display_name(f) for f in corrections])
            return f"Entendi, você corrigiu o(s) campo(s): {fields}. Obrigado pela atualização!"
        return None

    def _create_anticipatory_response(self, context: Dict[str, Any], extracted_data: Dict[str, Any]) -> str:
        """
        Sugere próximo campo logicamente, usando antecipação contextual.
        """
        anticipated_next = context.get("anticipated_next", [])
        if anticipated_next:
            next_field = anticipated_next[0]
            return self._generate_field_question(next_field, extracted_data)
        return "Há mais algum dado que gostaria de informar?"

    def _get_field_display_name(self, field: str) -> str:
        field_mapping = {
            "nome": "Nome",
            "telefone": "Telefone",
            "data": "Data",
            "horario": "Horário",
            "tipo_consulta": "Tipo de consulta"
        }
        return field_mapping.get(field, field.title())
    
    # ============= MÉTODOS CONSOLIDADOS DO QUESTIONGENERATOR =============
    
    def get_missing_fields_questions(self, missing_fields: List[str], context: Dict[str, Any] = None) -> List[str]:
        """Consolidado do QuestionGenerator"""
        questions = []
        for field in missing_fields:
            if field in self.field_questions:
                questions.append(self.field_questions[field])
            else:
                questions.append(f"Qual é o {field}?")
        return questions

    def generate_contextual_question(self, template_type: str, **kwargs) -> str:
        """Consolidado do QuestionGenerator"""
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
        """Consolidado do QuestionGenerator"""
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
        """Consolidado do QuestionGenerator"""
        summary = self.generate_data_summary(extracted_data)
        missing_questions = self.get_missing_fields_questions(missing_fields)
        missing_text = ", ".join(missing_questions)
        return self.generate_contextual_question("data_summary", summary=summary, missing=missing_text)

    def generate_progress_question(self, extracted_data: Dict[str, Any], missing_fields: List[str], context: Dict[str, Any] = None) -> str:
        """Consolidado do QuestionGenerator"""
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
        """Consolidado do QuestionGenerator"""
        summary = self.generate_data_summary(extracted_data)
        return self.generate_contextual_question("summary_before_confirm", summary=summary) if "summary_before_confirm" in self.context_templates else f"Resumo: {summary}. Posso confirmar?" 