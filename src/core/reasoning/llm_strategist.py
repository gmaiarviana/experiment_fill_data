"""
LLMStrategist - Strategy pattern para LLM reasoning
Gerencia estratégias de análise usando OpenAI com fallback para lógica Python.
"""

from typing import Dict, Any, List
from loguru import logger
from src.core.openai_client import OpenAIClient
from .fallback_handler import FallbackHandler


class LLMStrategist:
    """
    Estrategista que usa LLM para análise inteligente de mensagens.
    Implementa strategy pattern com fallback para lógica Python.
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
        
        Args:
            message (str): Mensagem para analisar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da análise com ação decidida
        """
        try:
            logger.debug("Executando LLM reasoning...")
            
            # Tenta LLM reasoning primeiro
            llm_result = await self._reason_with_llm(message, context)
            
            if llm_result.get("success"):
                return llm_result["result"]
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
    
    async def _reason_with_llm(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Usa OpenAI para decidir estratégia de ação baseada na mensagem e contexto.
        
        Args:
            message (str): Mensagem do usuário
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado do reasoning com ação decidida
        """
        try:
            logger.info("Iniciando LLM reasoning...")
            
            # Prepara contexto para o LLM
            existing_data = context.get("extracted_data", {})
            conversation_history = context.get("conversation_history", [])
            
            # Cria resumo do contexto atual
            context_summary = self._create_context_summary_for_llm(existing_data, conversation_history)
            
            # System prompt específico para reasoning conversacional
            system_prompt = """Você é um assistente especializado em agendamento de consultas médicas. Sua função é analisar mensagens e decidir a melhor ação a tomar.

ANÁLISE NECESSÁRIA:
1. Identifique se a mensagem contém dados para extração (nome, telefone, data, horário, tipo de consulta)
2. Avalie se é uma confirmação, negação, ou nova informação
3. Considere o contexto da conversa e dados já coletados
4. Decida a ação mais apropriada

AÇÕES POSSÍVEIS:
- "extract": Extrair dados da mensagem (quando há informações para extrair)
- "ask": Fazer pergunta específica (quando faltam dados)
- "confirm": Solicitar confirmação (quando dados parecem completos)
- "complete": Finalizar agendamento (quando tudo está confirmado)
- "error": Erro no processamento

RESPONDA APENAS COM JSON válido no formato:
{
    "action": "extract|ask|confirm|complete|error",
    "reason": "explicação da decisão",
    "confidence": 0.0-1.0,
    "response": "resposta para o usuário (se aplicável)",
    "missing_fields": ["campo1", "campo2"] (se action=ask)
}"""

            # User prompt com contexto
            user_prompt = f"""CONTEXTO ATUAL:
{context_summary}

MENSAGEM DO USUÁRIO:
{message}

Analise a mensagem e decida a melhor ação a tomar."""

            # Chama OpenAI
            response = await self.openai_client.chat_completion(
                message=user_prompt,
                system_prompt=system_prompt
            )
            
            if isinstance(response, str):
                # Tenta parsear JSON da resposta
                try:
                    import json
                    result = json.loads(response)
                    
                    # Valida estrutura básica
                    if "action" in result and "confidence" in result:
                        logger.info(f"LLM reasoning bem-sucedido: {result['action']}")
                        return {
                            "success": True,
                            "result": result
                        }
                    else:
                        raise ValueError("Resposta LLM não contém campos obrigatórios")
                        
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Erro ao parsear resposta LLM: {str(e)}")
                    return {
                        "success": False,
                        "error": f"Resposta LLM inválida: {str(e)}"
                    }
            else:
                return {
                    "success": False,
                    "error": "Erro desconhecido na API OpenAI"
                }
                
        except Exception as e:
            logger.error(f"Erro no LLM reasoning: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_context_summary_for_llm(self, existing_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]) -> str:
        """
        Cria resumo do contexto para o LLM.
        
        Args:
            existing_data (Dict[str, Any]): Dados já extraídos
            conversation_history (List[Dict[str, Any]]): Histórico da conversa
            
        Returns:
            str: Resumo formatado do contexto
        """
        summary_parts = []
        
        # Dados já coletados
        if existing_data:
            data_summary = "DADOS JÁ COLETADOS:\n"
            for field, value in existing_data.items():
                if value:  # Só mostra campos com valor
                    display_name = self._get_field_display_name(field)
                    data_summary += f"- {display_name}: {value}\n"
            summary_parts.append(data_summary)
        
        # Histórico recente (últimas 3 mensagens)
        if conversation_history:
            recent_history = conversation_history[-3:]
            history_summary = "HISTÓRICO RECENTE:\n"
            for entry in recent_history:
                user_msg = entry.get("user_message", "")[:100]
                action = entry.get("action", "")
                history_summary += f"- Usuário: {user_msg} → Ação: {action}\n"
            summary_parts.append(history_summary)
        
        # Campos obrigatórios
        required_fields = ["nome", "telefone", "data", "horario", "tipo_consulta"]
        missing_fields = [field for field in required_fields if not existing_data.get(field)]
        
        if missing_fields:
            missing_summary = "CAMPOS AINDA NECESSÁRIOS:\n"
            for field in missing_fields:
                display_name = self._get_field_display_name(field)
                missing_summary += f"- {display_name}\n"
            summary_parts.append(missing_summary)
        
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