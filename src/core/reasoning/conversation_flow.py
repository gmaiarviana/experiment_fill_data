"""
ConversationFlow - Gerencia fluxo natural da conversa
Controla extração de dados, validação e gerenciamento de contexto conversacional.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from src.core.logging.logger_factory import get_logger
logger = get_logger(__name__)
from src.core.entity_extraction import EntityExtractor
from src.core.validation.normalizers.data_normalizer import DataNormalizer
from src.core.validation.validation_orchestrator import ValidationOrchestrator
class ConversationFlow:
    """
    Gerencia o fluxo natural da conversa, incluindo extração, validação e contexto.
    """
    
    def __init__(self):
        """
        Inicializa o gerenciador de fluxo conversacional.
        """
        self.entity_extractor = EntityExtractor()
        self.data_normalizer = DataNormalizer(strict_mode=False)
        self.validation_orchestrator = ValidationOrchestrator()
        logger.info("ConversationFlow inicializado com EntityExtractor e DataNormalizer")
    
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
        Agora antecipa próximos campos necessários e evita re-extrações desnecessárias.
        """
        try:
            logger.info(f"Extraindo dados da mensagem: '{message[:50]}...'")

            # Verifica se já temos todos os dados necessários
            missing_fields = self._anticipate_next_steps(context)
            if not missing_fields:
                logger.info("Todos os campos necessários já foram preenchidos. Nenhuma extração necessária.")
                return {
                    "action": "skip",
                    "extracted_data": context.get("extracted_data", {}),
                    "confidence": 1.0,
                    "raw_extraction": None,
                    "anticipated_next": [],
                    "progression_pattern": None
                }

            # Extrai entidades usando EntityExtractor com contexto para acumulação
            extraction_result = await self.entity_extractor.extract_consulta_entities(message, context)

            if extraction_result.get("success"):
                extracted_data = extraction_result.get("extracted_data", {})

                # Normaliza dados extraídos (skip if already normalized)
                if extracted_data:
                    # Check if data is already normalized (has English field names)
                    has_english_fields = any(field in extracted_data for field in ["name", "phone", "consultation_date", "consultation_time"])
                    
                    if has_english_fields:
                        # Data already normalized by entity_extraction
                        logger.info("Data already normalized by entity_extraction, using as-is")
                        normalized_data = extracted_data
                    else:
                        # Data needs normalization
                        normalization_result = self.data_normalizer.normalize_consultation_data(extracted_data)
                        normalized_data = normalization_result.normalized_data
                    confidence = extraction_result.get("confidence", 0.0)
                    anticipated_next = self._anticipate_next_steps(context, normalized_data)
                    progression_pattern = self._detect_data_progression(context, normalized_data)
                    logger.info(f"Dados extraídos: {list(normalized_data.keys())}, Confidence: {confidence:.2f}")
                    return {
                        "action": "extract",
                        "extracted_data": normalized_data,
                        "confidence": confidence,
                        "raw_extraction": extraction_result,
                        "anticipated_next": anticipated_next,
                        "progression_pattern": progression_pattern
                    }
                else:
                    logger.info("Nenhum dado extraído da mensagem")
                    anticipated_next = self._anticipate_next_steps(context)
                    progression_pattern = self._detect_data_progression(context)
                    return {
                        "action": "extract",
                        "extracted_data": {},
                        "confidence": 0.0,
                        "raw_extraction": extraction_result,
                        "anticipated_next": anticipated_next,
                        "progression_pattern": progression_pattern
                    }
            else:
                logger.warning(f"Falha na extração: {extraction_result.get('error')}")
                anticipated_next = self._anticipate_next_steps(context)
                progression_pattern = self._detect_data_progression(context)
                return {
                    "action": "error",
                    "error": extraction_result.get("error", "Erro desconhecido na extração"),
                    "extracted_data": {},
                    "confidence": 0.0,
                    "anticipated_next": anticipated_next,
                    "progression_pattern": progression_pattern
                }
        except Exception as e:
            logger.error(f"Erro na extração de dados: {str(e)}")
            anticipated_next = self._anticipate_next_steps(context)
            progression_pattern = self._detect_data_progression(context)
            return {
                "action": "error",
                "error": str(e),
                "extracted_data": {},
                "confidence": 0.0,
                "anticipated_next": anticipated_next,
                "progression_pattern": progression_pattern
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
            
            # Valida dados usando ValidationOrchestrator
            validation_summary = self.validation_orchestrator.validate_data(extracted_data)
            
            if validation_summary.is_valid:
                logger.info("Dados validados com sucesso")
                return {
                    "action": "validate",
                    "is_valid": True,
                    "validation_errors": [],
                    "confidence": validation_summary.overall_confidence
                }
            else:
                errors = validation_summary.suggestions or []
                logger.warning(f"Dados inválidos: {errors}")
                return {
                    "action": "validate",
                    "is_valid": False,
                    "validation_errors": errors,
                    "confidence": validation_summary.overall_confidence
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
        Agora inclui padrões de progressão do usuário.
        """
        # Atualiza dados extraídos se houver
        if extract_result and extract_result.get("extracted_data"):
            extracted_data = extract_result["extracted_data"]
            for key, value in extracted_data.items():
                if value is not None and value != "":
                    context["extracted_data"][key] = value
                elif key not in context["extracted_data"]:
                    context["extracted_data"][key] = value
            logger.info(f"Contexto atualizado (merge) com dados: {list(extracted_data.keys())}")

        # Atualiza métricas de confidence
        confidence = act_result.get("confidence", 0.0)
        context["total_confidence"] += confidence
        context["confidence_count"] += 1
        context["average_confidence"] = context["total_confidence"] / context["confidence_count"]

        # Atualiza última ação e resposta
        context["last_action"] = act_result.get("action")
        context["last_response"] = act_result.get("response")

        # Atualiza padrão de progressão do usuário
        progression_pattern = extract_result.get("progression_pattern") if extract_result else None
        if progression_pattern:
            context["progression_pattern"] = progression_pattern
        else:
            # Detecta e atualiza se possível
            context["progression_pattern"] = self._detect_data_progression(context)

        # Sugere estratégia de conclusão
        context["completion_strategy"] = self._suggest_completion_strategy(context)
    
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
        
        # Gera resumo dos dados usando DataSummarizer
        from src.core.data_summarizer import DataSummarizer
        summarizer = DataSummarizer()
        data_summary = summarizer.summarize_extracted_data(extracted_data)
        
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
    
 

    def _anticipate_next_steps(self, context: Dict[str, Any], new_data: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Prevê próximos campos necessários baseado no contexto e dados novos.
        """
        # Campos obrigatórios para consulta
        required_fields = ["nome", "telefone", "data", "horario", "tipo_consulta"]
        extracted = context.get("extracted_data", {}).copy()
        if new_data:
            extracted.update(new_data)
        missing = [field for field in required_fields if not extracted.get(field)]
        return missing

    def _detect_data_progression(self, context: Dict[str, Any], new_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Identifica se o usuário está fornecendo dados de forma sequencial ou randômica.
        """
        # Analisa histórico de preenchimento dos campos
        required_fields = ["nome", "telefone", "data", "horario", "tipo_consulta"]
        history = context.get("conversation_history", [])
        field_order = []
        for entry in history:
            extracted = entry.get("extracted_data", {})
            for field in required_fields:
                if field in extracted and extracted[field] and field not in field_order:
                    field_order.append(field)
        # Inclui novos dados se fornecidos
        if new_data:
            for field in required_fields:
                if field in new_data and new_data[field] and field not in field_order:
                    field_order.append(field)
        # Verifica se o usuário está seguindo a ordem padrão
        if field_order == required_fields[:len(field_order)]:
            return "sequencial"
        elif len(set(field_order)) == len(field_order):
            return "randômico"
        return "indefinido"

    def _suggest_completion_strategy(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Sugere estratégia de conclusão baseada no padrão do usuário.
        Retorna None - delegando para ResponseComposer.
        """
        # Estratégia movida para ResponseComposer para consolidação
        return None 