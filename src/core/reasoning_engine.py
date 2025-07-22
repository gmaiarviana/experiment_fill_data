from typing import Dict, Any, Optional, List
from datetime import datetime
from src.core.logging.logger_factory import get_logger

logger = get_logger(__name__)
from src.core.entity_extraction import EntityExtractor
from src.core.question_generator import QuestionGenerator
from src.core.data_summarizer import DataSummarizer
from src.core.conversation_manager import ConversationManager
from src.core.openai_client import OpenAIClient
from src.core.reasoning import ReasoningCoordinator
import random
import json


class ReasoningEngine:
    """
    Motor de raciocínio que implementa o loop Think → Extract → Validate → Act
    para processamento inteligente de mensagens conversacionais.
    
    REFATORADO: Agora usa módulos especializados internamente mantendo API 100% compatível.
    """
    
    def __init__(self, 
                 openai_client: Optional[OpenAIClient] = None,
                 entity_extractor: Optional[EntityExtractor] = None):
        """
        Inicializa o motor de raciocínio com o coordenador modular.
        
        Args:
            openai_client: Cliente OpenAI opcional para dependency injection
            entity_extractor: EntityExtractor opcional para dependency injection
        """
        # Initialize shared dependencies
        self.openai_client = openai_client or OpenAIClient()
        self.entity_extractor = entity_extractor or EntityExtractor(openai_client=self.openai_client)
        
        # Coordenador modular que orquestra todos os componentes
        self.coordinator = ReasoningCoordinator()
        
        # Componentes legados mantidos para compatibilidade
        self.question_generator = QuestionGenerator()
        self.data_summarizer = DataSummarizer()
        self.conversation_manager = ConversationManager()
        
        logger.info("ReasoningEngine refatorado inicializado com coordenador modular")
    
    def _get_response_template(self, template_type: str, **kwargs) -> str:
        """
        Gera uma resposta usando templates para tornar o diálogo mais natural.
        
        Args:
            template_type (str): Tipo de template a usar
            **kwargs: Parâmetros para formatar o template
            
        Returns:
            str: Resposta formatada
        """
        return self.question_generator.generate_contextual_question(template_type, **kwargs)
    
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
                context = self.conversation_manager.initialize_context()
            
            # DELEGA PARA O COORDENADOR MODULAR
            result = await self.coordinator.process_message(message, context)
            
            # Adiciona mensagem ao histórico usando ConversationManager (mantém compatibilidade)
            self.conversation_manager.add_to_history(
                context, 
                message, 
                result.get("action", "unknown"), 
                result.get("response", ""), 
                result.get("confidence", 0.0)
            )
            
            logger.info(f"Processamento concluído. Ação: {result['action']}, Confidence: {result.get('confidence', 0.0):.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Erro no processamento da mensagem: {str(e)}")
            return self._create_error_response("Erro interno no processamento", str(e))
    
    # MÉTODOS LEGADOS MANTIDOS PARA COMPATIBILIDADE
    # Estes métodos agora delegam para os módulos modulares
    
    async def _think(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        THINK: Analisa a mensagem e decide o próximo passo usando LLM reasoning real.
        
        Args:
            message (str): Mensagem para analisar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da análise com ação decidida
        """
        # Delega para o LLMStrategist do coordenador
        return await self.coordinator.llm_strategist.analyze_message(message, context)
    
    async def _reason_strategy(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Usa OpenAI para decidir a estratégia de ação baseada na mensagem e contexto.
        
        Args:
            message (str): Mensagem do usuário
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado do reasoning com ação decidida
        """
        # Delega para o LLMStrategist do coordenador
        return await self.coordinator.llm_strategist._reason_with_llm(message, context)
    
    def _create_context_summary_for_llm(self, existing_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> str:
        """
        Cria resumo do contexto para o LLM.
        
        Args:
            existing_data (Dict[str, Any]): Dados já extraídos
            conversation_history (List[Dict[str, Any]]): Histórico da conversa
            
        Returns:
            str: Resumo formatado do contexto
        """
        # Delega para o LLMStrategist do coordenador
        return self.coordinator.llm_strategist._create_context_summary_for_llm(existing_data, conversation_history)
    
    async def _think_fallback(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback para lógica Python quando LLM falha.
        
        Args:
            message (str): Mensagem para analisar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da análise usando lógica Python
        """
        # Delega para o FallbackHandler do coordenador
        return await self.coordinator.fallback_handler.analyze_message_fallback(message, context)
    
    def is_data_complete(self, data: Dict[str, Any]) -> bool:
        """
        Verifica se dados estão completos.
        
        Args:
            data (Dict[str, Any]): Dados para verificar
            
        Returns:
            bool: True se dados estão completos
        """
        # Delega para o FallbackHandler do coordenador
        return self.coordinator.fallback_handler._is_data_complete(data)
    
    def _get_missing_fields(self, data: Dict[str, Any]) -> List[str]:
        """
        Identifica campos obrigatórios que estão faltando.
        
        Args:
            data (Dict[str, Any]): Dados atuais
            
        Returns:
            List[str]: Lista de campos faltantes
        """
        # Delega para o FallbackHandler do coordenador
        return self.coordinator.fallback_handler._get_missing_fields(data)
    
    def get_missing_fields_questions(self, missing_fields: List[str]) -> List[str]:
        """
        Gera perguntas para campos faltantes.
        
        Args:
            missing_fields (List[str]): Lista de campos faltantes
            
        Returns:
            List[str]: Lista de perguntas
        """
        questions = []
        for field in missing_fields:
            question = self.coordinator.fallback_handler._get_field_question(field)
            questions.append(question)
        return questions
    
    def _has_data_potential(self, message: str) -> bool:
        """
        Verifica se mensagem tem potencial de conter dados.
        
        Args:
            message (str): Mensagem para verificar
            
        Returns:
            bool: True se tem potencial de dados
        """
        # Delega para o FallbackHandler do coordenador
        return self.coordinator.fallback_handler._has_data_potential(message.lower().strip())
    
    async def _extract(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        EXTRACT: Extrai dados da mensagem usando EntityExtractor.
        
        Args:
            message (str): Mensagem para extrair dados
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Dados extraídos e metadados
        """
        # Delega para o ConversationFlow do coordenador
        return await self.coordinator.conversation_flow.extract_data(message, context)
    
    async def _validate(self, extracted_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        VALIDATE: Valida dados extraídos usando validators.
        
        Args:
            extracted_data (Dict[str, Any]): Dados extraídos para validar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da validação
        """
        # Delega para o ConversationFlow do coordenador
        return await self.coordinator.conversation_flow.validate_data(extracted_data, context)
    
    async def _act(self, think_result: Dict[str, Any], extract_result: Optional[Dict[str, Any]], 
                   validate_result: Optional[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        ACT: Decide resposta final baseada nos resultados de todas as fases.
        
        Args:
            think_result (Dict[str, Any]): Resultado da análise THINK
            extract_result (Optional[Dict[str, Any]]): Resultado da extração
            validate_result (Optional[Dict[str, Any]]): Resultado da validação
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resposta final e ação decidida
        """
        # Delega para o ResponseComposer do coordenador
        return await self.coordinator.response_composer.compose_response(think_result, extract_result, validate_result, context)
    
    async def _act_fallback(self, think_result: Dict[str, Any], extract_result: Optional[Dict[str, Any]], 
                           validate_result: Optional[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback para lógica Python quando LLM falha na fase ACT.
        
        Args:
            think_result (Dict[str, Any]): Resultado da análise THINK
            extract_result (Optional[Dict[str, Any]]): Resultado da extração
            validate_result (Optional[Dict[str, Any]]): Resultado da validação
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resposta final usando lógica Python
        """
        # Delega para o ResponseComposer do coordenador
        return await self.coordinator.response_composer.compose_response(think_result, extract_result, validate_result, context)
    
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
    
    def _initialize_context(self) -> Dict[str, Any]:
        """
        Inicializa contexto de conversa.
        
        Returns:
            Dict: Contexto inicial da sessão
        """
        # Delega para o ConversationFlow do coordenador
        return self.coordinator.conversation_flow.initialize_context()
    
    def update_context(self, context: Dict[str, Any], new_data: Dict[str, Any], action: str) -> Dict[str, Any]:
        """
        Atualiza contexto com novos dados.
        
        Args:
            context (Dict[str, Any]): Contexto a ser atualizado
            new_data (Dict[str, Any]): Novos dados
            action (str): Ação executada
            
        Returns:
            Dict: Contexto atualizado
        """
        # Delega para o ConversationFlow do coordenador
        self.coordinator.conversation_flow.update_context(context, {"extracted_data": new_data}, {"action": action})
        return context
    
    def get_context_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera resumo do contexto atual.
        
        Args:
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resumo do contexto
        """
        # Delega para o ConversationFlow do coordenador
        return self.coordinator.conversation_flow.get_context_summary(context)
    
    def _calculate_session_duration(self, context: Dict[str, Any]) -> str:
        """
        Calcula duração da sessão.
        
        Args:
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            str: Duração formatada
        """
        # Delega para o ConversationFlow do coordenador
        summary = self.coordinator.conversation_flow.get_context_summary(context)
        return summary.get("duration", "0s")
    
    def _summarize_extracted_data(self, data: Dict[str, Any]) -> str:
        """
        Cria resumo dos dados extraídos.
        
        Args:
            data (Dict[str, Any]): Dados extraídos
            
        Returns:
            str: Resumo formatado
        """
        # Delega para o ConversationFlow do coordenador
        return self.coordinator.conversation_flow._summarize_extracted_data(data)
    
    def _get_field_display_name(self, field: str) -> str:
        """
        Converte nome do campo para display name.
        
        Args:
            field (str): Nome do campo
            
        Returns:
            str: Nome para exibição
        """
        # Delega para o LLMStrategist do coordenador
        return self.coordinator.llm_strategist._get_field_display_name(field)
    
    def _format_validation_errors(self, errors: List[str]) -> str:
        """
        Formata erros de validação para exibição.
        
        Args:
            errors (List[str]): Lista de erros
            
        Returns:
            str: Erros formatados
        """
        # Delega para o ResponseComposer do coordenador
        return self.coordinator.response_composer._format_validation_errors(errors) 