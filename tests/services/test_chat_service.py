import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime
from src.services.chat_service import ChatService
from src.services.session_service import SessionService


class TestChatService:
    """Testes para o serviço de chat."""

    def setup_method(self):
        """Setup para cada teste."""
        self.mock_session_service = MagicMock(spec=SessionService)
        self.chat_service = ChatService(session_service=self.mock_session_service)

    @patch('src.services.chat_service.get_settings')
    def test_chat_service_initialization(self, mock_get_settings):
        """Testa inicialização do ChatService."""
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings
        
        chat_service = ChatService()
        
        assert chat_service.settings == mock_settings
        assert chat_service.session_service is not None

    def test_get_or_create_session_context_new_session(self):
        """Testa criação de nova sessão."""
        self.mock_session_service.get_session.return_value = None
        self.mock_session_service.create_session.return_value = {
            "session_start": "2025-07-22T15:30:00",
            "conversation_history": [],
            "extracted_data": {},
            "total_confidence": 0.0,
            "confidence_count": 0,
            "average_confidence": 0.0
        }

        context = self.chat_service._get_or_create_session_context("test_session")

        assert context["session_id"] == "test_session"
        self.mock_session_service.create_session.assert_called_once()

    def test_get_or_create_session_context_existing_session(self):
        """Testa recuperação de sessão existente."""
        existing_context = {
            "session_start": "2025-07-22T15:30:00",
            "conversation_history": [{"user_message": "test"}],
            "extracted_data": {"nome": "João"},
            "total_confidence": 0.8,
            "confidence_count": 1,
            "average_confidence": 0.8
        }
        self.mock_session_service.get_session.return_value = existing_context

        context = self.chat_service._get_or_create_session_context("existing_session")

        assert context["session_id"] == "existing_session"
        assert context["extracted_data"]["nome"] == "João"
        self.mock_session_service.create_session.assert_not_called()

    @patch('src.services.chat_service.get_openai_client')
    @patch.object(ChatService, '_get_or_create_session_context')
    @pytest.mark.asyncio
    async def test_process_message_full_llm_mode(self, mock_get_context, mock_get_openai):
        """Testa processamento de mensagem com modo full LLM."""
        # Setup
        mock_context = {
            "session_id": "test_session",
            "extracted_data": {},
            "conversation_history": [],
            "total_confidence": 0.0,
            "confidence_count": 0,
            "average_confidence": 0.0
        }
        mock_get_context.return_value = mock_context
        
        mock_openai_client = AsyncMock()
        mock_openai_client.full_llm_completion.return_value = json.dumps({
            "response": "Olá! Como posso ajudar?",
            "action": "extract",
            "extracted_data": {"nome": "João Silva"},
            "confidence": 0.8,
            "next_questions": ["Qual é o seu telefone?"],
            "validation_errors": [],
            "missing_fields": ["telefone"]
        })
        mock_get_openai.return_value = mock_openai_client
        
        self.chat_service.settings = MagicMock(USE_FULL_LLM_VALIDATION=True)

        # Execute
        result = await self.chat_service.process_message("Olá, sou João Silva")

        # Assert
        assert result["response"] == "Olá! Como posso ajudar?"
        assert result["action"] == "extract"
        assert result["extracted_data"]["nome"] == "João Silva"
        assert result["confidence"] == 0.8
        assert "Qual é o seu telefone?" in result["next_questions"]
        self.mock_session_service.update_session.assert_called_once()

    @patch('src.services.chat_service.ReasoningCoordinator')
    @patch.object(ChatService, '_get_or_create_session_context')
    @patch.object(ChatService, '_handle_persistence')
    @pytest.mark.asyncio
    async def test_process_message_reasoning_engine_mode(self, mock_handle_persistence, mock_get_context, mock_reasoning_coordinator):
        """Testa processamento de mensagem com reasoning engine."""
        # Setup
        mock_context = {
            "session_id": "test_session",
            "extracted_data": {},
            "conversation_history": [],
            "total_confidence": 0.0,
            "confidence_count": 0,
            "average_confidence": 0.0
        }
        mock_get_context.return_value = mock_context
        
        mock_reasoning_instance = AsyncMock()
        mock_reasoning_instance.process_message.return_value = {
            "response": "Dados processados com sucesso",
            "action": "extract",
            "extracted_data": {"nome": "João Silva", "telefone": "11999888777"},
            "confidence": 0.9,
            "next_questions": []
        }
        mock_reasoning_coordinator.return_value = mock_reasoning_instance
        
        mock_handle_persistence.return_value = (123, "success")
        
        self.chat_service.settings = MagicMock(USE_FULL_LLM_VALIDATION=False)

        # Execute
        result = await self.chat_service.process_message("João Silva, telefone 11999888777")

        # Assert
        assert result["response"] == "Dados processados com sucesso\n\n✅ Consulta registrada com sucesso! (ID: 123)"
        assert result["action"] == "extract"
        assert result["consultation_id"] == 123
        assert result["persistence_status"] == "success"
        mock_reasoning_instance.process_message.assert_called_once()

    @patch('src.services.chat_service.get_openai_client')
    @patch.object(ChatService, '_get_or_create_session_context')
    @pytest.mark.asyncio
    async def test_process_message_openai_fallback(self, mock_get_context, mock_get_openai):
        """Testa fallback para OpenAI quando reasoning engine falha."""
        # Setup
        mock_context = {
            "session_id": "test_session",
            "extracted_data": {},
            "conversation_history": [],
            "total_confidence": 0.0,
            "confidence_count": 0,
            "average_confidence": 0.0
        }
        mock_get_context.return_value = mock_context
        
        mock_openai_client = AsyncMock()
        mock_openai_client.chat_completion.return_value = "Resposta do OpenAI"
        mock_get_openai.return_value = mock_openai_client
        
        self.chat_service.settings = MagicMock(USE_FULL_LLM_VALIDATION=False)

        # Simulate reasoning engine failure
        with patch('src.services.chat_service.ReasoningCoordinator') as mock_reasoning:
            mock_reasoning.return_value = None

            # Execute
            result = await self.chat_service.process_message("Olá")

        # Assert
        assert result["response"] == "Resposta do OpenAI"
        assert result["action"] == "fallback"
        assert result["confidence"] == 0.0

    @patch('src.services.chat_service.get_consultation_service')
    @pytest.mark.asyncio
    async def test_handle_persistence_success(self, mock_get_consultation):
        """Testa persistência bem-sucedida."""
        mock_consultation_service = AsyncMock()
        mock_consultation_service.process_and_persist.return_value = {
            "success": True,
            "consultation_id": 456
        }
        mock_get_consultation.return_value = mock_consultation_service

        extracted_data = {
            "normalized_data": {
                "nome": "João Silva",
                "telefone": "11999888777"
            }
        }

        consultation_id, status = await self.chat_service._handle_persistence(
            "João Silva, telefone 11999888777",
            "test_session",
            extracted_data,
            "extract"
        )

        assert consultation_id == 456
        assert status == "success"

    @patch('src.services.chat_service.get_consultation_service')
    @pytest.mark.asyncio
    async def test_handle_persistence_failure(self, mock_get_consultation):
        """Testa falha na persistência."""
        mock_consultation_service = AsyncMock()
        mock_consultation_service.process_and_persist.return_value = {
            "success": False,
            "errors": ["Dados incompletos"]
        }
        mock_get_consultation.return_value = mock_consultation_service

        extracted_data = {
            "normalized_data": {
                "nome": "João Silva"
            }
        }

        consultation_id, status = await self.chat_service._handle_persistence(
            "João Silva",
            "test_session",
            extracted_data,
            "extract"
        )

        assert consultation_id is None
        assert status == "failed"

    @pytest.mark.asyncio
    async def test_handle_persistence_not_applicable(self):
        """Testa quando persistência não é aplicável."""
        consultation_id, status = await self.chat_service._handle_persistence(
            "Olá",
            "test_session",
            {},
            "greet"
        )

        assert consultation_id is None
        assert status == "not_applicable"

    def test_update_context_with_data(self):
        """Testa atualização de contexto com dados extraídos."""
        context = {
            "extracted_data": {},
            "total_confidence": 0.0,
            "confidence_count": 0,
            "average_confidence": 0.0
        }

        extracted_data = {
            "nome": "João Silva",
            "telefone": "11999888777",
            "email": None  # Deve ser ignorado
        }

        self.chat_service._update_context_with_data(context, extracted_data, 0.8)

        assert context["extracted_data"]["nome"] == "João Silva"
        assert context["extracted_data"]["telefone"] == "11999888777"
        assert "email" not in context["extracted_data"]
        assert context["total_confidence"] == 0.8
        assert context["confidence_count"] == 1
        assert context["average_confidence"] == 0.8

    def test_add_persistence_success_message_extract(self):
        """Testa mensagem de sucesso para ação extract."""
        response_text = "Dados extraídos"
        result = self.chat_service._add_persistence_success_message(response_text, "extract", 123)
        
        assert "✅ Consulta registrada com sucesso! (ID: 123)" in result

    def test_add_persistence_success_message_confirm(self):
        """Testa mensagem de sucesso para ação confirm."""
        response_text = "Dados confirmados"
        result = self.chat_service._add_persistence_success_message(response_text, "confirm", 456)
        
        assert "✅ Consulta confirmada e salva! (ID: 456)" in result

    def test_add_persistence_error_message(self):
        """Testa mensagem de erro na persistência."""
        response_text = "Dados processados"
        errors = ["Campo nome obrigatório", "Telefone inválido"]
        result = self.chat_service._add_persistence_error_message(response_text, errors)
        
        assert "⚠️ Não foi possível salvar a consulta" in result
        assert "Campo nome obrigatório" in result
        assert "Telefone inválido" in result

    def test_create_error_response(self):
        """Testa criação de resposta de erro."""
        error_message = "Erro de conexão"
        session_id = "test_session"
        
        result = self.chat_service._create_error_response(error_message, session_id)
        
        assert "Ocorreu um erro ao processar sua mensagem" in result["response"]
        assert "Erro de conexão" in result["response"]
        assert result["session_id"] == session_id
        assert result["action"] == "error"
        assert result["confidence"] == 0.0
        assert result["persistence_status"] == "error"


class TestChatServiceErrorHandling:
    """Testes para tratamento de erros no ChatService."""

    def setup_method(self):
        """Setup para cada teste."""
        self.mock_session_service = MagicMock(spec=SessionService)
        self.chat_service = ChatService(session_service=self.mock_session_service)

    @patch('src.services.chat_service.get_openai_client')
    @patch.object(ChatService, '_get_or_create_session_context')
    @pytest.mark.asyncio
    async def test_process_message_json_decode_error(self, mock_get_context, mock_get_openai):
        """Testa tratamento de erro de JSON no modo full LLM."""
        mock_context = {
            "session_id": "test_session",
            "extracted_data": {},
            "conversation_history": [],
            "total_confidence": 0.0,
            "confidence_count": 0,
            "average_confidence": 0.0
        }
        mock_get_context.return_value = mock_context
        
        mock_openai_client = AsyncMock()
        mock_openai_client.full_llm_completion.return_value = "Invalid JSON response"
        mock_get_openai.return_value = mock_openai_client
        
        self.chat_service.settings = MagicMock(USE_FULL_LLM_VALIDATION=True)

        result = await self.chat_service.process_message("Teste")

        assert "Error processing AI response" in result["response"]
        assert result["action"] == "error"

    @patch.object(ChatService, '_get_or_create_session_context')
    @pytest.mark.asyncio
    async def test_process_message_general_exception(self, mock_get_context):
        """Testa tratamento de exceção geral."""
        mock_get_context.side_effect = Exception("Erro inesperado")

        result = await self.chat_service.process_message("Teste")

        assert "Ocorreu um erro ao processar sua mensagem" in result["response"]
        assert "Erro inesperado" in result["response"]
        assert result["action"] == "error"

    @patch('src.services.chat_service.get_openai_client')
    @patch.object(ChatService, '_get_or_create_session_context')
    @pytest.mark.asyncio
    async def test_process_message_openai_client_unavailable(self, mock_get_context, mock_get_openai):
        """Testa quando cliente OpenAI não está disponível."""
        mock_context = {
            "session_id": "test_session",
            "extracted_data": {},
            "conversation_history": [],
            "total_confidence": 0.0,
            "confidence_count": 0,
            "average_confidence": 0.0
        }
        mock_get_context.return_value = mock_context
        mock_get_openai.return_value = None
        
        self.chat_service.settings = MagicMock(USE_FULL_LLM_VALIDATION=True)

        result = await self.chat_service.process_message("Teste")

        assert "AI service unavailable" in result["response"]
        assert result["action"] == "error"

    @patch('src.services.chat_service.get_consultation_service')
    @pytest.mark.asyncio
    async def test_handle_persistence_service_unavailable(self, mock_get_consultation):
        """Testa quando serviço de consulta não está disponível."""
        mock_get_consultation.return_value = None

        consultation_id, status = await self.chat_service._handle_persistence(
            "João Silva",
            "test_session",
            {"normalized_data": {"nome": "João Silva"}},
            "extract"
        )

        assert consultation_id is None
        assert status == "service_unavailable"

    @patch('src.services.chat_service.get_consultation_service')
    @pytest.mark.asyncio
    async def test_handle_persistence_exception(self, mock_get_consultation):
        """Testa exceção durante persistência."""
        mock_consultation_service = AsyncMock()
        mock_consultation_service.process_and_persist.side_effect = Exception("Erro de DB")
        mock_get_consultation.return_value = mock_consultation_service

        consultation_id, status = await self.chat_service._handle_persistence(
            "João Silva",
            "test_session",
            {"normalized_data": {"nome": "João Silva"}},
            "extract"
        )

        assert consultation_id is None
        assert status == "error"