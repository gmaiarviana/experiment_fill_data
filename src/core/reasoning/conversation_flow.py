"""
ConversationFlow - Gerencia fluxo natural da conversa
Controla extração de dados, validação e gerenciamento de contexto conversacional.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from src.core.entity_extraction import EntityExtractor
from src.core.data_normalizer import normalize_consulta_data
from src.core.validators import validate_consulta_data


class ConversationFlow:
    """
    Gerencia o fluxo natural da conversa, incluindo extração, validação e contexto.
    """
    
    def __init__(self):
        """
        Inicializa o gerenciador de fluxo conversacional.
        """
        self.entity_extractor = EntityExtractor()
        
        logger.info("ConversationFlow inicializado com EntityExtractor")
    
    def initialize_context(self) -> Dict[str, Any]:
        """
        Inicializa contexto de conversa.
        
        Returns:
            Dict: Contexto inicial da sessão
        """
        return {
            "session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": datetime.now().isoformat(),
            "extracted_data": {},
            "conversation_history": [],
            "total_confidence": 0.0,
            "confidence_count": 0,
            "average_confidence": 0.0,
            "last_action": None,
            "last_response": None
        }
    
    async def extract_data(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai dados da mensagem usando EntityExtractor.
        
        Args:
            message (str): Mensagem para extrair dados
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Dados extraídos e metadados
        """
        try:
            logger.info(f"Extraindo dados da mensagem: '{message[:50]}...'")
            
            # Extrai entidades usando EntityExtractor com contexto para acumulação
            extraction_result = await self.entity_extractor.extract_consulta_entities(message, context)
            
            if extraction_result.get("success"):
                extracted_data = extraction_result.get("extracted_data", {})
                
                # Normaliza dados extraídos
                if extracted_data:
                    normalized_data = normalize_consulta_data(extracted_data)
                    
                    # Calcula confidence médio
                    confidence = extraction_result.get("confidence", 0.0)
                    
                    logger.info(f"Dados extraídos: {list(normalized_data.keys())}, Confidence: {confidence:.2f}")
                    
                    return {
                        "action": "extract",
                        "extracted_data": normalized_data,
                        "confidence": confidence,
                        "raw_extraction": extraction_result
                    }
                else:
                    logger.info("Nenhum dado extraído da mensagem")
                    return {
                        "action": "extract",
                        "extracted_data": {},
                        "confidence": 0.0,
                        "raw_extraction": extraction_result
                    }
            else:
                logger.warning(f"Falha na extração: {extraction_result.get('error')}")
                return {
                    "action": "error",
                    "error": extraction_result.get("error", "Erro desconhecido na extração"),
                    "extracted_data": {},
                    "confidence": 0.0
                }
                
        except Exception as e:
            logger.error(f"Erro na extração de dados: {str(e)}")
            return {
                "action": "error",
                "error": str(e),
                "extracted_data": {},
                "confidence": 0.0
            }
    
    async def validate_data(self, extracted_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida dados extraídos usando validators.
        
        Args:
            extracted_data (Dict[str, Any]): Dados extraídos para validar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da validação
        """
        try:
            logger.info(f"Validando dados: {list(extracted_data.keys())}")
            
            # Valida dados usando validators
            validation_result = validate_consulta_data(extracted_data)
            
            if validation_result.get("is_valid"):
                logger.info("Dados validados com sucesso")
                return {
                    "action": "validate",
                    "is_valid": True,
                    "validation_errors": [],
                    "confidence": validation_result.get("confidence", 0.8)
                }
            else:
                errors = validation_result.get("errors", [])
                logger.warning(f"Dados inválidos: {errors}")
                return {
                    "action": "validate",
                    "is_valid": False,
                    "validation_errors": errors,
                    "confidence": validation_result.get("confidence", 0.3)
                }
                
        except Exception as e:
            logger.error(f"Erro na validação: {str(e)}")
            return {
                "action": "error",
                "error": str(e),
                "is_valid": False,
                "validation_errors": [str(e)],
                "confidence": 0.0
            }
    
    def update_context(self, context: Dict[str, Any], extract_result: Optional[Dict[str, Any]], 
                      act_result: Dict[str, Any]) -> None:
        """
        Atualiza contexto com resultados do processamento.
        
        Args:
            context (Dict[str, Any]): Contexto a ser atualizado
            extract_result (Optional[Dict[str, Any]]): Resultado da extração
            act_result (Dict[str, Any]): Resultado da ação
        """
        # Atualiza dados extraídos se houver
        if extract_result and extract_result.get("extracted_data"):
            # O EntityExtractor retorna dados em estrutura aninhada
            extracted_data = extract_result["extracted_data"]
            
            # Se os dados estão em normalized_data, usa eles
            if isinstance(extracted_data, dict) and "normalized_data" in extracted_data:
                normalized_data = extracted_data["normalized_data"]
                context["extracted_data"].update(normalized_data)
                logger.info(f"Contexto atualizado com dados normalizados: {list(normalized_data.keys())}")
            else:
                # Caso contrário, usa os dados diretamente
                context["extracted_data"].update(extracted_data)
                logger.info(f"Contexto atualizado com dados diretos: {list(extracted_data.keys())}")
        
        # Atualiza métricas de confidence
        confidence = act_result.get("confidence", 0.0)
        context["total_confidence"] += confidence
        context["confidence_count"] += 1
        context["average_confidence"] = context["total_confidence"] / context["confidence_count"]
        
        # Atualiza última ação e resposta
        context["last_action"] = act_result.get("action")
        context["last_response"] = act_result.get("response")
    
    def add_to_history(self, context: Dict[str, Any], user_message: str, action: str, 
                      response: str, confidence: float) -> None:
        """
        Adiciona entrada ao histórico da conversa.
        
        Args:
            context (Dict[str, Any]): Contexto da sessão
            user_message (str): Mensagem do usuário
            action (str): Ação executada
            response (str): Resposta gerada
            confidence (float): Confidence da ação
        """
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "action": action,
            "response": response,
            "confidence": confidence,
            "extracted_data": context.get("extracted_data", {}).copy()
        }
        
        context["conversation_history"].append(history_entry)
        
        # Mantém apenas últimas 20 entradas para evitar crescimento excessivo
        if len(context["conversation_history"]) > 20:
            context["conversation_history"] = context["conversation_history"][-20:]
    
    def get_context_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera resumo do contexto atual.
        
        Args:
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resumo do contexto
        """
        extracted_data = context.get("extracted_data", {})
        
        # Calcula duração da sessão
        start_time = datetime.fromisoformat(context.get("start_time", datetime.now().isoformat()))
        duration = datetime.now() - start_time
        duration_str = self._format_duration(duration)
        
        # Conta campos preenchidos
        filled_fields = sum(1 for value in extracted_data.values() if value)
        total_fields = len(extracted_data)
        
        # Gera resumo dos dados
        data_summary = self._summarize_extracted_data(extracted_data)
        
        return {
            "session_id": context.get("session_id"),
            "duration": duration_str,
            "filled_fields": filled_fields,
            "total_fields": total_fields,
            "completion_percentage": (filled_fields / total_fields * 100) if total_fields > 0 else 0,
            "average_confidence": context.get("average_confidence", 0.0),
            "data_summary": data_summary,
            "last_action": context.get("last_action"),
            "message_count": len(context.get("conversation_history", []))
        }
    
    def _format_duration(self, duration) -> str:
        """
        Formata duração em formato legível.
        
        Args:
            duration: Objeto timedelta
            
        Returns:
            str: Duração formatada
        """
        total_seconds = int(duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def _summarize_extracted_data(self, data: Dict[str, Any]) -> str:
        """
        Cria resumo dos dados extraídos.
        
        Args:
            data (Dict[str, Any]): Dados extraídos
            
        Returns:
            str: Resumo formatado
        """
        if not data:
            return "Nenhum dado coletado"
        
        summary_parts = []
        field_names = {
            "nome": "Nome",
            "telefone": "Telefone", 
            "data": "Data",
            "horario": "Horário",
            "tipo_consulta": "Tipo de Consulta"
        }
        
        for field, value in data.items():
            if value:
                display_name = field_names.get(field, field.title())
                summary_parts.append(f"{display_name}: {value}")
        
        return "; ".join(summary_parts) if summary_parts else "Nenhum dado válido" 