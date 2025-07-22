import requests
import json
from typing import Dict, Any, Optional
from src.core.config import get_settings
from src.core.logging.logger_factory import get_logger

logger = get_logger(__name__)


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
                logger.info(f"OpenAI raw function_args: {function_args}")
                
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

    async def full_llm_completion(self, message: str, context: Dict[str, Any] = None) -> str:
        """
        Completa processamento 100% LLM com prompt robusto para agendamento de consultas.
        
        Args:
            message (str): Mensagem do usuário
            context (Dict[str, Any], optional): Contexto da sessão
            
        Returns:
            str: Resposta JSON estruturada do LLM
        """
        try:
            # Prompt robusto para garantir respostas estruturadas
            system_prompt = """Você é um assistente especializado em agendamento de consultas médicas. Sua função é processar mensagens e retornar respostas estruturadas em JSON.

REGRAS OBRIGATÓRIAS:
1. SEMPRE retorne um JSON válido com todos os campos obrigatórios
2. Extraia TODOS os dados mencionados na mensagem
3. Calcule confidence score baseado na completude e qualidade dos dados
4. Identifique intenções como confirmação, correção, cancelamento, reagendamento
5. Mantenha contexto de conversas anteriores
6. Valide dados extraídos (telefone brasileiro, datas futuras, etc.)

CAMPOS DE EXTRAÇÃO:
- nome: Nome completo do paciente
- telefone: Telefone brasileiro (formato: (11) 99988-8777)
- data: Data da consulta (formato: YYYY-MM-DD)
- horario: Horário da consulta (formato: HH:MM)
- tipo_consulta: Tipo de consulta (ex: rotina, cardiologia, oftalmologia)

VALIDAÇÕES:
- Telefone: deve ter 10-11 dígitos com DDD válido
- Data: deve ser futura
- Nome: deve ter pelo menos 2 palavras
- Horário: deve estar entre 08:00 e 18:00

AÇÕES POSSÍVEIS:
- "extract": Extrair dados da mensagem
- "ask": Fazer pergunta específica
- "confirm": Solicitar confirmação
- "complete": Finalizar agendamento
- "correction": Usuário corrigiu dado
- "reschedule": Usuário quer reagendar
- "cancel": Usuário quer cancelar
- "clarify": Mensagem ambígua

FORMATO DE RESPOSTA OBRIGATÓRIO:
{
    "response": "resposta natural para o usuário",
    "action": "extract|ask|confirm|complete|correction|reschedule|cancel|clarify",
    "extracted_data": {
        "nome": "valor ou null",
        "telefone": "valor ou null", 
        "data": "valor ou null",
        "horario": "valor ou null",
        "tipo_consulta": "valor ou null"
    },
    "confidence": 0.0-1.0,
    "next_questions": ["pergunta1", "pergunta2"],
    "validation_errors": ["erro1", "erro2"],
    "missing_fields": ["campo1", "campo2"]
}

EXEMPLOS:
Mensagem: "João Silva, telefone 11999888777, consulta de cardiologia para amanhã às 14h"
Resposta: {
    "response": "Perfeito! Anotei: João Silva, telefone (11) 99988-8777, consulta de cardiologia para 2025-07-23 às 14:00. Está tudo correto?",
    "action": "extract",
    "extracted_data": {
        "nome": "João Silva",
        "telefone": "(11) 99988-8777",
        "data": "2025-07-23",
        "horario": "14:00",
        "tipo_consulta": "cardiologia"
    },
    "confidence": 0.95,
    "next_questions": [],
    "validation_errors": [],
    "missing_fields": []
}

Mensagem: "Como cancelo minha consulta?"
Resposta: {
    "response": "Para cancelar sua consulta, preciso do seu nome e telefone para localizar o agendamento. Pode me informar esses dados?",
    "action": "cancel",
    "extracted_data": {
        "nome": null,
        "telefone": null,
        "data": null,
        "horario": null,
        "tipo_consulta": null
    },
    "confidence": 0.9,
    "next_questions": ["Qual é o seu nome?", "Qual é o seu telefone?"],
    "validation_errors": [],
    "missing_fields": ["nome", "telefone"]
}"""

            # Constrói contexto para o LLM
            context_info = ""
            if context:
                existing_data = context.get("extracted_data", {})
                if existing_data:
                    context_info = "CONTEXTO ATUAL:\n"
                    for field, value in existing_data.items():
                        if value:
                            context_info += f"- {field}: {value}\n"
                    context_info += "\n"

            user_prompt = f"{context_info}MENSAGEM DO USUÁRIO:\n{message}\n\nProcesse esta mensagem e retorne o JSON estruturado."

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": 0.1  # Baixa temperatura para respostas mais consistentes
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            response_data = response.json()
            llm_response = response_data["choices"][0]["message"]["content"]
            
            # Tenta parsear como JSON, se falhar, retorna resposta estruturada de fallback
            try:
                import json
                parsed_response = json.loads(llm_response)
                return llm_response
            except json.JSONDecodeError:
                # Fallback: retorna JSON estruturado básico
                fallback_response = {
                    "response": llm_response,
                    "action": "extract",
                    "extracted_data": {
                        "nome": None,
                        "telefone": None,
                        "data": None,
                        "horario": None,
                        "tipo_consulta": None
                    },
                    "confidence": 0.5,
                    "next_questions": [],
                    "validation_errors": [],
                    "missing_fields": []
                }
                return json.dumps(fallback_response, ensure_ascii=False)
            
        except requests.exceptions.RequestException as e:
            error_response = {
                "response": f"Desculpe, ocorreu um erro de conexão: {str(e)}",
                "action": "error",
                "extracted_data": {},
                "confidence": 0.0,
                "next_questions": [],
                "validation_errors": [f"Erro de conexão: {str(e)}"],
                "missing_fields": []
            }
            return json.dumps(error_response, ensure_ascii=False)
        except Exception as e:
            error_response = {
                "response": f"Desculpe, ocorreu um erro: {str(e)}",
                "action": "error", 
                "extracted_data": {},
                "confidence": 0.0,
                "next_questions": [],
                "validation_errors": [f"Erro interno: {str(e)}"],
                "missing_fields": []
            }
            return json.dumps(error_response, ensure_ascii=False)