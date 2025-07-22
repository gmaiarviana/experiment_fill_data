"""
LLMStrategist - Strategy pattern para LLM reasoning
Versão otimizada: uma única chamada LLM para extração + validação + decisão de ação.
"""

from typing import Dict, Any, List
import re
import json
from src.core.logging.logger_factory import get_logger
logger = get_logger(__name__)
from src.core.openai_client import OpenAIClient
from .fallback_handler import FallbackHandler


class LLMStrategist:
    """
    Estrategista que usa LLM para análise inteligente de mensagens.
    Versão otimizada: uma única chamada LLM para todo o processamento.
    """
    
    def __init__(self):
        """
        Inicializa o estrategista com cliente OpenAI e fallback handler.
        """
        self.openai_client = OpenAIClient()
        self.fallback_handler = FallbackHandler()
        
        logger.info("LLMStrategist inicializado com OpenAI e fallback handler")
    
    async def analyze_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa mensagem usando LLM reasoning com fallback.
        Versão otimizada: uma única chamada LLM para extração + validação + decisão.
        
        Args:
            message (str): Mensagem para analisar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da análise com ação decidida
        """
        try:
            logger.debug("Executando LLM reasoning otimizado...")

            # Tenta LLM reasoning otimizado primeiro
            llm_result = await self._reason_with_llm_optimized(message, context)
            
            # Se retornou com sucesso (tem action e não tem error), usa o resultado do LLM
            if llm_result.get("action") and not llm_result.get("error"):
                return llm_result
            else:
                # Fallback para lógica Python se LLM falhar
                logger.warning(f"LLM reasoning falhou: {llm_result.get('error')}. Usando fallback Python.")
                return await self._reason_with_fallback(message, context)
                
        except Exception as e:
            logger.error(f"Erro no LLMStrategist: {str(e)}")
            return {
                "action": "error",
                "error": str(e),
                "confidence": 0.0
            }
    
    async def _reason_with_llm_optimized(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Usa OpenAI para processamento completo: extração + validação + decisão de ação.
        
        Args:
            message (str): Mensagem do usuário
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado completo do processamento
        """
        try:
            logger.info("Iniciando LLM reasoning otimizado...")
            
            existing_data = context.get("extracted_data", {})
            conversation_history = context.get("conversation_history", [])
            context_summary = self._create_context_summary_for_llm(existing_data, conversation_history)
            
            # Prompt otimizado para processamento completo
            system_prompt = """Você é um assistente especializado em agendamento de consultas médicas. Sua função é processar mensagens e retornar respostas estruturadas em JSON.

INSTRUÇÕES CRÍTICAS:
1. SEMPRE retorne um JSON válido com todos os campos obrigatórios
2. Calcule confidence_score baseado na qualidade e completude dos dados extraídos
3. Para tipos de consulta, reconheça termos médicos em português (cardiologia, oftalmologia, dermatologia, etc.)
4. Mantenha contexto de conversas anteriores

CAMPOS OBRIGATÓRIOS NO JSON:
- action: "extract", "ask", "confirm", "complete"
- confidence_score: 0.0 a 1.0 (baseado na qualidade dos dados)
- extracted_data: objeto com dados extraídos
- response: resposta natural para o usuário
- suggested_questions: array de perguntas para completar dados

CÁLCULO DE CONFIDENCE_SCORE:
- 0.9-1.0: Dados completos e válidos (nome completo, telefone válido, data/hora, tipo consulta)
- 0.7-0.8: Dados quase completos, apenas 1-2 campos faltando
- 0.5-0.6: Dados parciais válidos (nome + telefone, ou nome + data)
- 0.3-0.4: Dados mínimos (apenas nome ou apenas telefone)
- 0.1-0.2: Dados inválidos ou muito incompletos
- 0.0: Nenhum dado extraído

TIPOS DE CONSULTA RECONHECIDOS:
- Especialidades: cardiologia, oftalmologia, dermatologia, neurologia, ortopedia, ginecologia, urologia, pediatria
- Tipos gerais: rotina, checkup, primeira consulta, retorno, emergência
- Termos relacionados: oftalmológica, cardiológica, dermatológica, etc.

EXEMPLO DE RESPOSTA:
{
  "action": "extract",
  "confidence_score": 0.85,
  "extracted_data": {
    "nome": "João Silva",
    "telefone": "11999888777",
    "data": "2025-07-23",
    "horario": "14:00",
    "tipo_consulta": "cardiologia"
  },
  "response": "Perfeito! Agendei sua consulta de cardiologia para João Silva no dia 23/07 às 14h. Telefone: (11) 99988-8777",
  "suggested_questions": []
}"""

            user_prompt = f"""CONTEXTO ATUAL:
{context_summary}

MENSAGEM DO USUÁRIO:
{message}

Processe esta mensagem completamente e retorne o JSON estruturado."""

            response = await self.openai_client.chat_completion(
                message=user_prompt,
                system_prompt=system_prompt
            )
            logger.info(f"[DEBUG] Resposta bruta do LLM: {response}")
            if isinstance(response, str):
                try:
                    logger.info(f"[DEBUG] Tentando parsear resposta do LLM como JSON...")
                    result = json.loads(response)
                    logger.info(f"[DEBUG] JSON parseado com sucesso: {result}")
                    if "action" in result and "confidence_score" in result and "extracted_data" in result:
                        logger.info(f"LLM reasoning otimizado bem-sucedido: {result['action']}")
                        return {
                            "action": result["action"],
                            "confidence": result["confidence_score"],  # Mapeia confidence_score para confidence
                            "extracted_data": result["extracted_data"],
                            "response": result.get("response", ""),
                            "next_questions": result.get("suggested_questions", [])
                        }
                    else:
                        missing_fields = []
                        if "action" not in result:
                            missing_fields.append("action")
                        if "confidence_score" not in result:
                            missing_fields.append("confidence_score")
                        if "extracted_data" not in result:
                            missing_fields.append("extracted_data")
                        logger.warning(f"[DEBUG] Campos obrigatórios faltando: {missing_fields}")
                        raise ValueError(f"Resposta LLM não contém campos obrigatórios: {missing_fields}")
                except Exception as e:
                    logger.error(f"[DEBUG] Erro ao parsear resposta do LLM: {e}")
                    logger.error(f"[DEBUG] Resposta bruta recebida: {response}")
                    raise
            else:
                logger.error(f"[DEBUG] Resposta do LLM não é string: {type(response)} - {response}")
                raise ValueError("Resposta do LLM não é string")
        except Exception as e:
            logger.error(f"Erro no LLM reasoning otimizado: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _create_context_summary_for_llm(self, existing_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> str:
        """
        Cria resumo do contexto para o LLM, incluindo progresso conversacional.
        """
        summary_parts = []
        if existing_data:
            data_summary = "DADOS JÁ COLETADOS:\n"
            for field, value in existing_data.items():
                if value:
                    display_name = self._get_field_display_name(field)
                    data_summary += f"- {display_name}: {value}\n"
            summary_parts.append(data_summary)
        if conversation_history:
            recent_history = conversation_history[-3:]
            history_summary = "HISTÓRICO RECENTE:\n"
            for entry in recent_history:
                user_msg = entry.get("user_message", "")[:100]
                action = entry.get("action", "")
                history_summary += f"- Usuário: {user_msg} → Ação: {action}\n"
            summary_parts.append(history_summary)
        required_fields = ["nome", "telefone", "data", "horario", "tipo_consulta"]
        missing_fields = [field for field in required_fields if not existing_data.get(field)]
        if missing_fields:
            missing_summary = "CAMPOS AINDA NECESSÁRIOS:\n"
            for field in missing_fields:
                display_name = self._get_field_display_name(field)
                missing_summary += f"- {display_name}\n"
            summary_parts.append(missing_summary)
        # Progresso conversacional
        progress = f"PROGRESSO: {len([v for v in existing_data.values() if v])}/{len(required_fields)} campos coletados."
        summary_parts.append(progress)
        return "\n".join(summary_parts) if summary_parts else "Nenhum dado coletado ainda."
    
    def _get_field_display_name(self, field: str) -> str:
        """
        Converte nome do campo para display name.
        
        Args:
            field (str): Nome do campo
            
        Returns:
            str: Nome para exibição
        """
        field_mapping = {
            "nome": "Nome completo",
            "telefone": "Telefone",
            "data": "Data da consulta",
            "horario": "Horário da consulta",
            "tipo_consulta": "Tipo de consulta"
        }
        return field_mapping.get(field, field.title())
    
    async def _reason_with_fallback(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback para lógica Python quando LLM falha.
        
        Args:
            message (str): Mensagem para analisar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da análise usando lógica Python
        """
        return await self.fallback_handler.analyze_message_fallback(message, context) 