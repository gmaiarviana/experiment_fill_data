from typing import Dict, Any, Optional, List
from loguru import logger
from src.core.entity_extraction import EntityExtractor
from src.core.data_normalizer import normalize_consulta_data


class ReasoningEngine:
    """
    Motor de raciocínio que implementa o loop Think → Extract → Validate → Act
    para processamento inteligente de mensagens conversacionais.
    """
    
    def __init__(self):
        """
        Inicializa o motor de raciocínio com o extrator de entidades.
        """
        self.entity_extractor = EntityExtractor()
        logger.info("ReasoningEngine inicializado com EntityExtractor")
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Processa uma mensagem através do loop Think → Extract → Validate → Act.
        
        Args:
            message (str): Mensagem do usuário para processar
            context (Dict[str, Any], optional): Contexto da sessão de conversa
            
        Returns:
            Dict: Resultado do processamento com ação, resposta e dados
        """
        try:
            logger.info(f"Iniciando processamento da mensagem: '{message[:50]}...'")
            
            # Inicializa contexto se não fornecido
            if context is None:
                context = {
                    "session_data": {},
                    "conversation_history": [],
                    "extracted_data": {},
                    "confidence_threshold": 0.7
                }
            
            # THINK: Analisa mensagem e decide próximo passo
            think_result = await self._think(message, context)
            logger.debug(f"THINK: {think_result}")
            
            if think_result["action"] == "error":
                return self._create_error_response("Erro na análise da mensagem", think_result.get("error"))
            
            # EXTRACT: Extrai dados se necessário
            extract_result = None
            if think_result["action"] in ["extract", "extract_and_ask"]:
                extract_result = await self._extract(message, context)
                logger.debug(f"EXTRACT: {extract_result}")
                
                if extract_result["action"] == "error":
                    return self._create_error_response("Erro na extração de dados", extract_result.get("error"))
            
            # VALIDATE: Valida dados extraídos
            validate_result = None
            if extract_result and extract_result.get("extracted_data"):
                validate_result = await self._validate(extract_result["extracted_data"], context)
                logger.debug(f"VALIDATE: {validate_result}")
                
                if validate_result["action"] == "error":
                    return self._create_error_response("Erro na validação de dados", validate_result.get("error"))
            
            # ACT: Decide resposta final
            act_result = await self._act(think_result, extract_result, validate_result, context)
            logger.debug(f"ACT: {act_result}")
            
            # Atualiza contexto com dados extraídos
            if extract_result and extract_result.get("extracted_data"):
                context["extracted_data"].update(extract_result["extracted_data"])
            
            # Adiciona mensagem ao histórico
            context["conversation_history"].append({
                "message": message,
                "timestamp": "now",  # TODO: usar datetime real
                "action": act_result["action"]
            })
            
            logger.info(f"Processamento concluído. Ação: {act_result['action']}")
            return act_result
            
        except Exception as e:
            logger.error(f"Erro no processamento da mensagem: {str(e)}")
            return self._create_error_response("Erro interno no processamento", str(e))
    
    async def _think(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        THINK: Analisa a mensagem e decide o próximo passo.
        
        Args:
            message (str): Mensagem para analisar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da análise com ação decidida
        """
        try:
            logger.debug("Executando THINK...")
            
            # Análise simples baseada em palavras-chave e contexto
            message_lower = message.lower()
            
            # Verifica se é uma confirmação
            confirmation_words = ["sim", "confirmo", "correto", "certo", "ok", "perfeito"]
            if any(word in message_lower for word in confirmation_words):
                return {
                    "action": "confirm",
                    "reason": "Mensagem identificada como confirmação",
                    "confidence": 0.9
                }
            
            # Verifica se é uma negação/correção
            negation_words = ["não", "não é", "errado", "incorreto", "mudar", "corrigir"]
            if any(word in message_lower for word in negation_words):
                return {
                    "action": "ask",
                    "reason": "Mensagem identificada como negação/correção",
                    "response": "Entendi, vou corrigir. Pode me informar novamente os dados corretos?",
                    "next_questions": ["Qual é o nome correto?", "Qual é o telefone correto?"],
                    "confidence": 0.8
                }
            
            # Verifica se já temos dados suficientes no contexto
            existing_data = context.get("extracted_data", {})
            required_fields = ["name", "phone", "consulta_date", "horario"]
            missing_fields = [field for field in required_fields if not existing_data.get(field)]
            
            # Se tem poucos dados ou é primeira mensagem, extrai
            if len(existing_data) < 2 or not context.get("conversation_history"):
                return {
                    "action": "extract",
                    "reason": "Primeira extração ou dados insuficientes",
                    "confidence": 0.9
                }
            
            # Se tem dados mas faltam campos específicos, pergunta
            if missing_fields:
                field_questions = {
                    "name": "Qual é o nome completo do paciente?",
                    "phone": "Qual é o telefone para contato?",
                    "consulta_date": "Para qual data você gostaria de agendar?",
                    "horario": "Qual horário prefere?"
                }
                
                next_questions = [field_questions[field] for field in missing_fields[:2]]
                
                return {
                    "action": "ask",
                    "reason": f"Faltam campos: {missing_fields}",
                    "response": "Preciso de mais algumas informações para completar o agendamento.",
                    "next_questions": next_questions,
                    "confidence": 0.8
                }
            
            # Se tem todos os dados, confirma
            return {
                "action": "confirm",
                "reason": "Dados completos, solicitando confirmação",
                "response": "Perfeito! Tenho todas as informações. Posso confirmar o agendamento?",
                "confidence": 0.9
            }
            
        except Exception as e:
            logger.error(f"Erro no THINK: {str(e)}")
            return {
                "action": "error",
                "error": str(e)
            }
    
    async def _extract(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        EXTRACT: Extrai dados da mensagem usando EntityExtractor.
        
        Args:
            message (str): Mensagem para extrair dados
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da extração
        """
        try:
            logger.debug("Executando EXTRACT...")
            
            # Usa EntityExtractor para extrair dados
            extraction_result = await self.entity_extractor.extract_consulta_entities(message)
            
            if not extraction_result["success"]:
                return {
                    "action": "error",
                    "error": extraction_result.get("error", "Falha na extração")
                }
            
            # Combina com dados existentes do contexto
            existing_data = context.get("extracted_data", {})
            new_data = extraction_result.get("extracted_data", {})
            
            # Atualiza dados existentes com novos dados
            combined_data = {**existing_data, **new_data}
            
            return {
                "action": "extract_success",
                "extracted_data": combined_data,
                "confidence_score": extraction_result.get("confidence_score", 0.0),
                "missing_fields": extraction_result.get("missing_fields", []),
                "suggested_questions": extraction_result.get("suggested_questions", [])
            }
            
        except Exception as e:
            logger.error(f"Erro no EXTRACT: {str(e)}")
            return {
                "action": "error",
                "error": str(e)
            }
    
    async def _validate(self, extracted_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        VALIDATE: Valida e normaliza dados extraídos.
        
        Args:
            extracted_data (Dict[str, Any]): Dados extraídos para validar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da validação
        """
        try:
            logger.debug("Executando VALIDATE...")
            
            # Usa data_normalizer para validar e normalizar
            validation_result = normalize_consulta_data(extracted_data)
            
            return {
                "action": "validate_success",
                "normalized_data": validation_result.get("normalized_data", {}),
                "validation_errors": validation_result.get("validation_errors", []),
                "confidence_score": validation_result.get("confidence_score", 0.0),
                "original_data": validation_result.get("original_data", {})
            }
            
        except Exception as e:
            logger.error(f"Erro no VALIDATE: {str(e)}")
            return {
                "action": "error",
                "error": str(e)
            }
    
    async def _act(self, think_result: Dict[str, Any], extract_result: Optional[Dict[str, Any]], 
                   validate_result: Optional[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        ACT: Decide a resposta final baseada nos resultados anteriores.
        
        Args:
            think_result (Dict[str, Any]): Resultado do THINK
            extract_result (Optional[Dict[str, Any]]): Resultado do EXTRACT
            validate_result (Optional[Dict[str, Any]]): Resultado do VALIDATE
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resposta final com ação e dados
        """
        try:
            logger.debug("Executando ACT...")
            
            # Se houve erro em qualquer etapa anterior
            if think_result["action"] == "error":
                return self._create_error_response("Erro na análise", think_result.get("error"))
            
            if extract_result and extract_result["action"] == "error":
                return self._create_error_response("Erro na extração", extract_result.get("error"))
            
            if validate_result and validate_result["action"] == "error":
                return self._create_error_response("Erro na validação", validate_result.get("error"))
            
            # Decide ação baseada no resultado do THINK
            if think_result["action"] == "ask":
                return {
                    "action": "ask",
                    "response": think_result.get("response", "Preciso de mais informações."),
                    "next_questions": think_result.get("next_questions", []),
                    "data": context.get("extracted_data", {}),
                    "confidence": think_result.get("confidence", 0.0)
                }
            
            elif think_result["action"] == "confirm":
                return {
                    "action": "confirm",
                    "response": think_result.get("response", "Posso confirmar os dados?"),
                    "data": context.get("extracted_data", {}),
                    "confidence": think_result.get("confidence", 0.0)
                }
            
            elif think_result["action"] == "extract":
                # Se extraiu dados, analisa resultado
                if extract_result and extract_result["action"] == "extract_success":
                    extracted_data = extract_result["extracted_data"]
                    confidence_score = extract_result.get("confidence_score", 0.0)
                    missing_fields = extract_result.get("missing_fields", [])
                    
                    # Se confidence score é alto e dados estão completos
                    if confidence_score > 0.8 and not missing_fields:
                        return {
                            "action": "complete",
                            "response": "Perfeito! Agendamento confirmado com sucesso.",
                            "data": extracted_data,
                            "confidence": confidence_score
                        }
                    
                    # Se tem dados mas faltam campos
                    elif extracted_data and missing_fields:
                        return {
                            "action": "ask",
                            "response": "Ótimo! Agora preciso de mais algumas informações.",
                            "next_questions": extract_result.get("suggested_questions", [])[:2],
                            "data": extracted_data,
                            "confidence": confidence_score
                        }
                    
                    # Se extração foi bem-sucedida mas dados insuficientes
                    else:
                        return {
                            "action": "ask",
                            "response": "Entendi! Pode me fornecer mais detalhes sobre o agendamento?",
                            "next_questions": [
                                "Qual é o nome completo do paciente?",
                                "Qual é o telefone para contato?",
                                "Para qual data você gostaria de agendar?"
                            ],
                            "data": extracted_data,
                            "confidence": confidence_score
                        }
                
                # Se extração falhou
                else:
                    return {
                        "action": "ask",
                        "response": "Não consegui entender completamente. Pode reformular?",
                        "next_questions": [
                            "Qual é o nome do paciente?",
                            "Qual é o telefone?",
                            "Para quando é o agendamento?"
                        ],
                        "data": {},
                        "confidence": 0.0
                    }
            
            # Ação padrão
            return {
                "action": "ask",
                "response": "Como posso ajudar com o agendamento?",
                "next_questions": ["Qual é o nome do paciente?"],
                "data": {},
                "confidence": 0.0
            }
            
        except Exception as e:
            logger.error(f"Erro no ACT: {str(e)}")
            return self._create_error_response("Erro na decisão final", str(e))
    
    def _create_error_response(self, message: str, error: str = None) -> Dict[str, Any]:
        """
        Cria resposta de erro padronizada.
        
        Args:
            message (str): Mensagem de erro
            error (str, optional): Detalhes do erro
            
        Returns:
            Dict: Resposta de erro padronizada
        """
        return {
            "action": "error",
            "response": message,
            "error": error,
            "data": {},
            "next_questions": []
        }
    
    def get_context_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retorna resumo do contexto atual.
        
        Args:
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resumo do contexto
        """
        extracted_data = context.get("extracted_data", {})
        history = context.get("conversation_history", [])
        
        return {
            "total_messages": len(history),
            "extracted_fields": list(extracted_data.keys()),
            "data_completeness": len(extracted_data) / 5.0,  # Assumindo 5 campos principais
            "last_action": history[-1]["action"] if history else None
        } 