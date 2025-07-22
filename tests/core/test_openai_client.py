import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import requests
from src.core.openai_client import OpenAIClient


class TestOpenAIClient:
    """Testes para o cliente OpenAI."""

    def setup_method(self):
        """Setup para cada teste."""
        self.client = OpenAIClient()

    @patch('src.core.openai_client.get_settings')
    def test_client_initialization(self, mock_settings):
        """Testa inicialização do cliente."""
        mock_settings.return_value = MagicMock(
            OPENAI_API_KEY="test-key",
            OPENAI_MODEL="gpt-3.5-turbo",
            OPENAI_MAX_TOKENS=1000,
            OPENAI_TIMEOUT=30,
            OPENAI_API_URL="https://api.openai.com/v1/chat/completions"
        )
        
        client = OpenAIClient()
        
        assert client.api_key == "test-key"
        assert client.model == "gpt-3.5-turbo"
        assert client.max_tokens == 1000
        assert client.timeout == 30
        assert client.api_url == "https://api.openai.com/v1/chat/completions"

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_chat_completion_success(self, mock_post):
        """Testa chat completion com sucesso."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Olá! Como posso ajudar?"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = await self.client.chat_completion("Olá")

        assert result == "Olá! Como posso ajudar?"
        mock_post.assert_called_once()

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_chat_completion_with_custom_prompt(self, mock_post):
        """Testa chat completion com prompt customizado."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Resposta customizada"}}]
        }
        mock_post.return_value = mock_response

        custom_prompt = "Você é um assistente médico."
        result = await self.client.chat_completion("Olá", custom_prompt)

        assert result == "Resposta customizada"
        
        call_args = mock_post.call_args
        data = call_args[1]["json"]
        assert data["messages"][0]["content"] == custom_prompt

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_chat_completion_request_exception(self, mock_post):
        """Testa tratamento de erro de request."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Erro de conexão")

        result = await self.client.chat_completion("Olá")

        assert "Erro de conexão com a API OpenAI" in result
        assert "Erro de conexão" in result

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_chat_completion_json_decode_error(self, mock_post):
        """Testa tratamento de erro de JSON."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_post.return_value = mock_response

        result = await self.client.chat_completion("Olá")

        assert "Erro ao processar resposta da API" in result

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_chat_completion_key_error(self, mock_post):
        """Testa tratamento de erro de estrutura de resposta."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"invalid": "structure"}
        mock_post.return_value = mock_response

        result = await self.client.chat_completion("Olá")

        assert "Resposta inesperada da API" in result


class TestOpenAIClientEntityExtraction:
    """Testes para extração de entidades."""

    def setup_method(self):
        """Setup para cada teste."""
        self.client = OpenAIClient()
        self.function_schema = {
            "name": "extract_consultation",
            "parameters": {
                "properties": {
                    "nome": {"type": "string"},
                    "telefone": {"type": "string"},
                    "data": {"type": "string"},
                    "horario": {"type": "string"}
                }
            }
        }

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_extract_entities_success(self, mock_post):
        """Testa extração de entidades com sucesso."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "function_call": {
                        "arguments": json.dumps({
                            "nome": "João Silva",
                            "telefone": "11999888777",
                            "data": "2025-07-25",
                            "horario": "14:00"
                        })
                    }
                }
            }]
        }
        mock_post.return_value = mock_response

        result = await self.client.extract_entities(
            "João Silva, telefone 11999888777, consulta para 25/07 às 14h",
            self.function_schema
        )

        assert result["success"] is True
        assert result["extracted_data"]["nome"] == "João Silva"
        assert result["confidence_score"] == 1.0  # Todos os campos preenchidos
        assert len(result["missing_fields"]) == 0

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_extract_entities_partial_data(self, mock_post):
        """Testa extração com dados parciais."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "function_call": {
                        "arguments": json.dumps({
                            "nome": "João Silva",
                            "telefone": None,
                            "data": "2025-07-25",
                            "horario": None
                        })
                    }
                }
            }]
        }
        mock_post.return_value = mock_response

        result = await self.client.extract_entities(
            "João Silva para 25/07",
            self.function_schema
        )

        assert result["success"] is True
        assert result["extracted_data"]["nome"] == "João Silva"
        assert result["confidence_score"] == 0.5  # 2 de 4 campos preenchidos
        assert "telefone" in result["missing_fields"]
        assert "horario" in result["missing_fields"]

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_extract_entities_no_function_call(self, mock_post):
        """Testa quando o modelo não retorna function call."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Desculpe, não consegui entender."
                }
            }]
        }
        mock_post.return_value = mock_response

        result = await self.client.extract_entities(
            "Mensagem confusa",
            self.function_schema
        )

        assert result["success"] is False
        assert "não conseguiu extrair dados estruturados" in result["error"]

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_extract_entities_request_error(self, mock_post):
        """Testa tratamento de erro de request na extração."""
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")

        result = await self.client.extract_entities(
            "João Silva",
            self.function_schema
        )

        assert result["success"] is False
        assert "Erro de conexão com a API OpenAI" in result["error"]


class TestOpenAIClientFullLLM:
    """Testes para processamento full LLM."""

    def setup_method(self):
        """Setup para cada teste."""
        self.client = OpenAIClient()

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_full_llm_completion_success(self, mock_post):
        """Testa full LLM completion com JSON válido."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "response": "Olá! Como posso ajudar?",
                        "action": "extract",
                        "extracted_data": {
                            "nome": None,
                            "telefone": None,
                            "data": None,
                            "horario": None,
                            "tipo_consulta": None
                        },
                        "confidence": 0.8,
                        "next_questions": ["Qual é o seu nome?"],
                        "validation_errors": [],
                        "missing_fields": ["nome", "telefone", "data", "horario"]
                    }, ensure_ascii=False)
                }
            }]
        }
        mock_post.return_value = mock_response

        result = await self.client.full_llm_completion("Olá")
        result_data = json.loads(result)

        assert result_data["response"] == "Olá! Como posso ajudar?"
        assert result_data["action"] == "extract"
        assert result_data["confidence"] == 0.8

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_full_llm_completion_with_context(self, mock_post):
        """Testa full LLM completion com contexto."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "response": "Perfeito, João!",
                        "action": "extract",
                        "extracted_data": {"nome": "João Silva"},
                        "confidence": 0.9,
                        "next_questions": [],
                        "validation_errors": [],
                        "missing_fields": []
                    })
                }
            }]
        }
        mock_post.return_value = mock_response

        context = {
            "extracted_data": {
                "nome": "João Silva",
                "telefone": "11999888777"
            }
        }

        result = await self.client.full_llm_completion("Confirmo", context)
        result_data = json.loads(result)

        assert result_data["response"] == "Perfeito, João!"
        assert result_data["confidence"] == 0.9

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_full_llm_completion_invalid_json_fallback(self, mock_post):
        """Testa fallback quando LLM retorna JSON inválido."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "Resposta não JSON do modelo"
                }
            }]
        }
        mock_post.return_value = mock_response

        result = await self.client.full_llm_completion("Olá")
        result_data = json.loads(result)

        assert result_data["response"] == "Resposta não JSON do modelo"
        assert result_data["action"] == "extract"
        assert result_data["confidence"] == 0.5

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_full_llm_completion_connection_error(self, mock_post):
        """Testa tratamento de erro de conexão."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Sem conexão")

        result = await self.client.full_llm_completion("Olá")
        result_data = json.loads(result)

        assert "erro de conexão" in result_data["response"].lower()
        assert result_data["action"] == "error"
        assert result_data["confidence"] == 0.0
        assert len(result_data["validation_errors"]) > 0

    @patch('src.core.openai_client.requests.post')
    @pytest.mark.asyncio
    async def test_full_llm_completion_general_error(self, mock_post):
        """Testa tratamento de erro geral."""
        mock_post.side_effect = Exception("Erro inesperado")

        result = await self.client.full_llm_completion("Olá")
        result_data = json.loads(result)

        assert "erro" in result_data["response"].lower()
        assert result_data["action"] == "error"
        assert result_data["confidence"] == 0.0