"""
ReasoningCoordinator - Orquestra o processamento otimizado
Versão simplificada: usa apenas LLMStrategist otimizado para processamento completo.
"""

from typing import Dict, Any, Optional
from src.core.logging.logger_factory import get_logger
logger = get_logger(__name__)
from .llm_strategist import LLMStrategist
from .conversation_flow import ConversationFlow
from .response_composer import ResponseComposer
from .fallback_handler import FallbackHandler


class ReasoningCoordinator:
    """
    Coordenador principal que orquestra o processamento otimizado.
    Versão simplificada: usa apenas LLMStrategist para processamento completo.
    """
    
    def __init__(self):
        """
        Inicializa o coordenador com componentes otimizados.
        """
        self.llm_strategist = LLMStrategist()
        self.conversation_flow = ConversationFlow()
        self.response_composer = ResponseComposer()
        self.fallback_handler = FallbackHandler()
        
        logger.info("ReasoningCoordinator inicializado com processamento otimizado")
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Processa uma mensagem usando LLMStrategist otimizado.
        
        Args:
            message (str): Mensagem do usuário para processar
            context (Dict[str, Any], optional): Contexto da sessão de conversa
            
        Returns:
            Dict: Resultado do processamento com ação, resposta e dados
        """
        try:
            logger.info(f"Coordenador iniciando processamento otimizado: '{message[:50]}...'")
            
            # Inicializa contexto se não fornecido
            if context is None:
                context = self.conversation_flow.initialize_context()
            
            # PROCESSAMENTO OTIMIZADO: LLMStrategist faz tudo
            llm_result = await self.llm_strategist.analyze_message(message, context)
            logger.debug(f"LLM Result: {llm_result}")
            
            if llm_result["action"] == "error":
                return self._create_error_response("Erro na análise da mensagem", llm_result.get("error"))
            
            # Atualiza contexto com resultados do LLM
            self._update_context_with_llm_results(context, llm_result)
            
            logger.info(f"Coordenador concluído. Ação: {llm_result['action']}, Confidence: {llm_result.get('confidence', 0.0):.2f}")
            return llm_result
            
        except Exception as e:
            logger.error(f"Erro no coordenador: {str(e)}")
            return self._create_error_response("Erro interno no coordenador", str(e))
    
    def _update_context_with_llm_results(self, context: Dict[str, Any], llm_result: Dict[str, Any]) -> None:
        """
        Atualiza contexto com resultados do LLM otimizado.
        
        Args:
            context (Dict[str, Any]): Contexto da sessão
            llm_result (Dict[str, Any]): Resultado do LLM
        """
        # Atualiza dados extraídos se houver
        extracted_data = llm_result.get("extracted_data", {})
        if extracted_data:
            for key, value in extracted_data.items():
                if value is not None and value != "":
                    context["extracted_data"][key] = value
            logger.info(f"Contexto atualizado com dados: {list(extracted_data.keys())}")

        # Atualiza métricas de confidence
        confidence = llm_result.get("confidence", 0.0)
        context["total_confidence"] += confidence
        context["confidence_count"] += 1
        context["average_confidence"] = context["total_confidence"] / context["confidence_count"]

        # Atualiza última ação e resposta
        context["last_action"] = llm_result.get("action")
        context["last_response"] = llm_result.get("response")

        # Atualiza histórico da conversa
        context["conversation_history"].append({
            "user_message": context.get("last_user_message", ""),
            "action": llm_result.get("action"),
            "confidence": confidence,
            "timestamp": context.get("last_timestamp", "")
        })
    
    def _create_error_response(self, message: str, error: str = None) -> Dict[str, Any]:
        """
        Cria resposta de erro padronizada.
        
        Args:
            message (str): Mensagem de erro
            error (str, optional): Detalhes do erro
            
        Returns:
            Dict: Resposta de erro estruturada
        """
        return {
            "action": "error",
            "response": message,
            "extracted_data": {},
            "confidence": 0.0,
            "error": error
        }
    
    def get_context_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtém resumo do contexto para debug e monitoramento.
        
        Args:
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resumo do contexto
        """
        return {
            "total_messages": len(context.get("conversation_history", [])),
            "extracted_fields": list(context.get("extracted_data", {}).keys()),
            "data_completeness": len([v for v in context.get("extracted_data", {}).values() if v]) / 5.0,  # 5 campos obrigatórios
            "last_action": context.get("last_action", "unknown"),
            "average_confidence": context.get("average_confidence", 0.0)
        } 