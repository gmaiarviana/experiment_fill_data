import requests
import json
import os


class OpenAIClient:
    """
    Cliente para integração com a API OpenAI usando requests.
    """
    
    def __init__(self):
        """
        Inicializa o cliente OpenAI carregando as variáveis de ambiente.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
        
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
        self.system_prompt = "Você é um assistente conversacional amigável. Responda de forma natural e útil."
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    async def chat_completion(self, message: str) -> str:
        """
        Envia uma mensagem para o modelo OpenAI e retorna a resposta.
        
        Args:
            message (str): Mensagem do usuário
            
        Returns:
            str: Resposta do modelo ou mensagem de erro amigável
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message}
                ],
                "max_tokens": self.max_tokens
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
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