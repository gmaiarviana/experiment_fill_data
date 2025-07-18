"""
ResponseComposer - Compõe respostas naturais e contextuais
Gera respostas conversacionais baseadas no contexto e resultados do reasoning.
"""

from typing import Dict, Any, Optional, List
from loguru import logger
from src.core.question_generator import QuestionGenerator


class ResponseComposer:
    """
    Compositor de respostas que gera diálogo natural e contextual.
    """
    
    def __init__(self):
        """
        Inicializa o compositor de respostas.
        """
        self.question_generator = QuestionGenerator()
        
        logger.info("ResponseComposer inicializado com QuestionGenerator")
    
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
        Compõe resposta para ação de extração.
        
        Args:
            think_result (Dict[str, Any]): Resultado da análise
            extract_result (Optional[Dict[str, Any]]): Resultado da extração
            validate_result (Optional[Dict[str, Any]]): Resultado da validação
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resposta para extração
        """
        extracted_data = extract_result.get("extracted_data", {}) if extract_result else {}
        validation_errors = validate_result.get("validation_errors", []) if validate_result else []
        
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
            confirmation = self._create_extraction_confirmation(extracted_data)
            next_question = self._get_next_question(context, extracted_data)
            
            response = f"{confirmation} {next_question}"
            
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
                "confidence": think_result.get("confidence", 0.7)
            }
        else:
            # Fallback se não há campos específicos
            return {
                "action": "ask",
                "response": "Preciso de mais informações para agendar sua consulta. Pode me dizer seu nome?",
                "missing_fields": ["nome"],
                "confidence": think_result.get("confidence", 0.5)
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
    
    def _create_extraction_confirmation(self, extracted_data: Dict[str, Any]) -> str:
        """
        Cria confirmação dos dados extraídos.
        
        Args:
            extracted_data (Dict[str, Any]): Dados extraídos
            
        Returns:
            str: Confirmação formatada
        """
        confirmations = []
        field_names = {
            "nome": "Nome",
            "telefone": "Telefone",
            "data": "Data",
            "horario": "Horário", 
            "tipo_consulta": "Tipo de consulta"
        }
        
        for field, value in extracted_data.items():
            if value:
                display_name = field_names.get(field, field.title())
                confirmations.append(f"{display_name}: {value}")
        
        if len(confirmations) == 1:
            return f"Anotado! {confirmations[0]}."
        else:
            return f"Anotado! {', '.join(confirmations[:-1])} e {confirmations[-1]}."
    
    def _get_next_question(self, context: Dict[str, Any], extracted_data: Dict[str, Any]) -> str:
        """
        Gera próxima pergunta baseada no contexto.
        
        Args:
            context (Dict[str, Any]): Contexto da sessão
            extracted_data (Dict[str, Any]): Dados extraídos
            
        Returns:
            str: Próxima pergunta
        """
        all_data = context.get("extracted_data", {}).copy()
        all_data.update(extracted_data)
        
        missing_fields = self._get_missing_fields(all_data)
        
        if missing_fields:
            next_field = missing_fields[0]
            return self._generate_field_question(next_field, all_data)
        else:
            return "Agora posso confirmar os dados da sua consulta?"
    
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
        Gera pergunta específica para um campo.
        
        Args:
            field (str): Campo para perguntar
            existing_data (Dict[str, Any]): Dados já coletados
            
        Returns:
            str: Pergunta formatada
        """
        field_questions = {
            "nome": "Qual é o seu nome completo?",
            "telefone": "Qual é o seu telefone para contato?",
            "data": "Para qual data você gostaria de agendar?",
            "horario": "Qual horário seria melhor para você?",
            "tipo_consulta": "Que tipo de consulta você precisa?"
        }
        
        return field_questions.get(field, f"Pode me informar o {field}?")
    
    def _create_confirmation_summary(self, data: Dict[str, Any]) -> str:
        """
        Cria resumo para confirmação.
        
        Args:
            data (Dict[str, Any]): Dados para confirmar
            
        Returns:
            str: Resumo formatado
        """
        summary_parts = []
        field_names = {
            "nome": "Nome",
            "telefone": "Telefone",
            "data": "Data",
            "horario": "Horário",
            "tipo_consulta": "Tipo de consulta"
        }
        
        for field, value in data.items():
            if value:
                display_name = field_names.get(field, field.title())
                summary_parts.append(f"• {display_name}: {value}")
        
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