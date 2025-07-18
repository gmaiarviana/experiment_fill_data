"""
ReasoningCoordinator - Orquestra o loop Think → Extract → Validate → Act
Coordena os componentes especializados para processamento inteligente de mensagens.
"""

from typing import Dict, Any, Optional
from loguru import logger
from .llm_strategist import LLMStrategist
from .conversation_flow import ConversationFlow
from .response_composer import ResponseComposer
from .fallback_handler import FallbackHandler


class ReasoningCoordinator:
    """
    Coordenador principal que orquestra o loop de reasoning conversacional.
    Gerencia o fluxo Think → Extract → Validate → Act usando componentes especializados.
    """
    
    def __init__(self):
        """
        Inicializa o coordenador com todos os componentes especializados.
        """
        self.llm_strategist = LLMStrategist()
        self.conversation_flow = ConversationFlow()
        self.response_composer = ResponseComposer()
        self.fallback_handler = FallbackHandler()
        
        logger.info("ReasoningCoordinator inicializado com componentes especializados")
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Processa uma mensagem através do loop completo de reasoning.
        
        Args:
            message (str): Mensagem do usuário para processar
            context (Dict[str, Any], optional): Contexto da sessão de conversa
            
        Returns:
            Dict: Resultado do processamento com ação, resposta e dados
        """
        try:
            logger.info(f"Coordenador iniciando processamento: '{message[:50]}...'")
            
            # Inicializa contexto se não fornecido
            if context is None:
                context = self.conversation_flow.initialize_context()
            
            # THINK: Analisa mensagem e decide próximo passo
            think_result = await self._execute_think(message, context)
            logger.debug(f"THINK: {think_result}")
            
            if think_result["action"] == "error":
                return self._create_error_response("Erro na análise da mensagem", think_result.get("error"))
            
            # EXTRACT: Extrai dados se necessário
            extract_result = None
            if think_result["action"] in ["extract", "extract_and_ask"]:
                extract_result = await self._execute_extract(message, context)
                logger.debug(f"EXTRACT: {extract_result}")
                
                if extract_result["action"] == "error":
                    return self._create_error_response("Erro na extração de dados", extract_result.get("error"))
            
            # VALIDATE: Valida dados extraídos
            validate_result = None
            if extract_result and extract_result.get("extracted_data"):
                validate_result = await self._execute_validate(extract_result["extracted_data"], context)
                logger.debug(f"VALIDATE: {validate_result}")
                
                if validate_result["action"] == "error":
                    return self._create_error_response("Erro na validação de dados", validate_result.get("error"))
            
            # ACT: Decide resposta final
            act_result = await self._execute_act(think_result, extract_result, validate_result, context)
            logger.debug(f"ACT: {act_result}")
            
            # Atualiza contexto com resultados
            self._update_context_with_results(context, extract_result, act_result)
            
            logger.info(f"Coordenador concluído. Ação: {act_result['action']}, Confidence: {act_result.get('confidence', 0.0):.2f}")
            return act_result
            
        except Exception as e:
            logger.error(f"Erro no coordenador: {str(e)}")
            return self._create_error_response("Erro interno no coordenador", str(e))
    
    async def _execute_think(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa a fase THINK usando o LLMStrategist.
        
        Args:
            message (str): Mensagem para analisar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da análise com ação decidida
        """
        return await self.llm_strategist.analyze_message(message, context)
    
    async def _execute_extract(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa a fase EXTRACT usando o ConversationFlow.
        
        Args:
            message (str): Mensagem para extrair dados
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Dados extraídos e validados
        """
        return await self.conversation_flow.extract_data(message, context)
    
    async def _execute_validate(self, extracted_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa a fase VALIDATE usando o ConversationFlow.
        
        Args:
            extracted_data (Dict[str, Any]): Dados extraídos para validar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da validação
        """
        return await self.conversation_flow.validate_data(extracted_data, context)
    
    async def _execute_act(self, think_result: Dict[str, Any], extract_result: Optional[Dict[str, Any]], 
                          validate_result: Optional[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa a fase ACT usando o ResponseComposer.
        
        Args:
            think_result (Dict[str, Any]): Resultado da análise THINK
            extract_result (Optional[Dict[str, Any]]): Resultado da extração
            validate_result (Optional[Dict[str, Any]]): Resultado da validação
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resposta final e ação decidida
        """
        return await self.response_composer.compose_response(think_result, extract_result, validate_result, context)
    
    def _update_context_with_results(self, context: Dict[str, Any], extract_result: Optional[Dict[str, Any]], 
                                   act_result: Dict[str, Any]) -> None:
        """
        Atualiza o contexto com os resultados do processamento.
        
        Args:
            context (Dict[str, Any]): Contexto a ser atualizado
            extract_result (Optional[Dict[str, Any]]): Resultado da extração
            act_result (Dict[str, Any]): Resultado da ação
        """
        # Atualiza dados extraídos
        if extract_result and extract_result.get("extracted_data"):
            context["extracted_data"].update(extract_result["extracted_data"])
        
        # Atualiza métricas de confidence
        confidence = act_result.get("confidence", 0.0)
        context["total_confidence"] += confidence
        context["confidence_count"] += 1
        context["average_confidence"] = context["total_confidence"] / context["confidence_count"]
        
        # Atualiza contexto usando ConversationFlow
        self.conversation_flow.update_context(context, extract_result, act_result)
    
    def _create_error_response(self, message: str, error: str = None) -> Dict[str, Any]:
        """
        Cria resposta de erro padronizada.
        
        Args:
            message (str): Mensagem de erro para o usuário
            error (str, optional): Detalhes técnicos do erro
            
        Returns:
            Dict: Resposta de erro formatada
        """
        return {
            "action": "error",
            "response": message,
            "error": error,
            "confidence": 0.0,
            "extracted_data": {},
            "validation_errors": []
        } 