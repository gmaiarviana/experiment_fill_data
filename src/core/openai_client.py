import requests
import json
from typing import Dict, Any, Optional
from src.core.config import get_settings


class OpenAIClient:
    """
    Cliente para integração com a API OpenAI usando requests.
    """
    
    def __init__(self):
        """
        Inicializa o cliente OpenAI usando configuração centralizada.
        """
        # Get centralized settings with all configurations
        settings = get_settings()
        
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.timeout = settings.OPENAI_TIMEOUT
        self.system_prompt = "Você é um assistente conversacional amigável. Responda de forma natural e útil."
        self.api_url = settings.OPENAI_API_URL
    
    async def chat_completion(self, message: str, system_prompt: str = None) -> str:
        """
        Envia uma mensagem para o modelo OpenAI e retorna a resposta.
        
        Args:
            message (str): Mensagem do usuário
            system_prompt (str, optional): Prompt do sistema personalizado
            
        Returns:
            str: Resposta do modelo ou mensagem de erro amigável
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Usa system prompt personalizado ou padrão
            prompt = system_prompt if system_prompt else self.system_prompt
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message}
                ],
                "max_tokens": self.max_tokens
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            response_data = response.json()
            return response_data["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            error_message = f"Erro de conexão com a API OpenAI: {str(e)}"
            return error_message
        except json.JSONDecodeError as e:
            error_message = f"Erro ao processar resposta da API: {str(e)}"
            return error_message
        except KeyError as e:
            error_message = f"Resposta inesperada da API: {str(e)}"
            return error_message
        except Exception as e:
            error_message = f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}"
            return error_message
    
    async def extract_entities(self, message: str, function_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai entidades de uma mensagem usando OpenAI function calling.
        
        Args:
            message (str): Mensagem do usuário
            function_schema (Dict): Schema da função para extração
            
        Returns:
            Dict: Dados extraídos com confidence score ou erro
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system", 
                        "content": "Você é um especialista em extrair informações de consultas médicas. Extraia apenas informações explicitamente mencionadas pelo usuário. Para campos não mencionados, use null."
                    },
                    {"role": "user", "content": message}
                ],
                "functions": [function_schema],
                "function_call": {"name": function_schema["name"]},
                "max_tokens": self.max_tokens
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            # Verifica se o modelo retornou uma function call
            message_response = response_data["choices"][0]["message"]
            
            if "function_call" in message_response:
                function_args = json.loads(message_response["function_call"]["arguments"])
                
                # Calcula confidence score baseado na completude dos dados
                total_fields = len(function_schema["parameters"]["properties"])
                filled_fields = sum(1 for value in function_args.values() if value is not None and value != "")
                confidence = filled_fields / total_fields if total_fields > 0 else 0.0
                
                return {
                    "success": True,
                    "extracted_data": function_args,
                    "confidence_score": round(confidence, 2),
                    "missing_fields": [key for key, value in function_args.items() if value is None or value == ""]
                }
            else:
                return {
                    "success": False,
                    "error": "Modelo não conseguiu extrair dados estruturados",
                    "raw_response": message_response.get("content", "")
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Erro de conexão com a API OpenAI: {str(e)}"
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Erro ao processar resposta da API: {str(e)}"
            }
        except KeyError as e:
            return {
                "success": False,
                "error": f"Resposta inesperada da API: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao processar extração: {str(e)}"
            }