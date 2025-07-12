from openai import OpenAI
import os


class OpenAIClient:
    """
    Cliente para integração com a API OpenAI.
    """
    
    def __init__(self):
        """
        Inicializa o cliente OpenAI carregando a chave da API do ambiente.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
        self.system_prompt = "Você é um assistente conversacional amigável. Responda de forma natural e útil."
    
    async def chat_completion(self, message: str) -> str:
        """
        Envia uma mensagem para o modelo OpenAI e retorna a resposta.
        
        Args:
            message (str): Mensagem do usuário
            
        Returns:
            str: Resposta do modelo ou mensagem de erro amigável
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_message = f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}"
            return error_message 