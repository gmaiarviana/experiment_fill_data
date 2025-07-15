from typing import Dict, Any, Optional
from loguru import logger
from src.core.openai_client import OpenAIClient
from src.core.data_normalizer import normalize_consulta_data


class EntityExtractor:
    """
    Extrator de entidades para consultas médicas usando OpenAI function calling.
    """
    
    def __init__(self):
        """
        Inicializa o extrator com cliente OpenAI e schema da função.
        """
        self.openai_client = OpenAIClient()
        self.consulta_schema = {
            "name": "extract_consulta_info",
            "description": "Extrai informações de agendamento de consulta médica",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome completo do paciente"
                    },
                    "telefone": {
                        "type": "string", 
                        "description": "Número de telefone do paciente (formato brasileiro)"
                    },
                    "data": {
                        "type": "string",
                        "description": "Data da consulta no formato YYYY-MM-DD"
                    },
                    "horario": {
                        "type": "string",
                        "description": "Horário da consulta no formato HH:MM"
                    },
                    "tipo_consulta": {
                        "type": "string",
                        "description": "Tipo de consulta (ex: rotina, urgente, retorno, primeira consulta)"
                    }
                },
                "required": []
            }
        }
    
    async def extract_consulta_entities(self, message: str) -> Dict[str, Any]:
        """
        Extrai entidades de consulta de uma mensagem em linguagem natural.
        
        Args:
            message (str): Mensagem em linguagem natural
            
        Returns:
            Dict: Resultado da extração com dados estruturados e confidence score
        """
        result = await self.openai_client.extract_entities(
            message=message,
            function_schema=self.consulta_schema
        )
        
        if result["success"]:
            # Aplica normalização aos dados extraídos
            try:
                normalization_result = normalize_consulta_data(result["extracted_data"])
                
                # Usa dados normalizados e confidence score do normalizador
                result["extracted_data"] = normalization_result["normalized_data"]
                result["confidence_score"] = normalization_result["confidence_score"]
                result["normalization_applied"] = True
                
                # Adiciona informações de validação se houver erros
                if normalization_result["validation_errors"]:
                    result["validation_errors"] = normalization_result["validation_errors"]
                    logger.warning(f"Erros de validação na normalização: {normalization_result['validation_errors']}")
                
                logger.info(f"Normalização aplicada com sucesso. Confidence score: {normalization_result['confidence_score']}")
                
            except Exception as e:
                # Se normalização falhar, usa dados originais e loga warning
                logger.warning(f"Falha na normalização, usando dados originais: {str(e)}")
                result["normalization_applied"] = False
                result["normalization_error"] = str(e)
            
            # Adiciona informações específicas sobre campos faltantes
            missing_fields = result["missing_fields"]
            
            # Mapeia campos para perguntas amigáveis
            field_questions = {
                "nome": "Qual é o nome completo do paciente?",
                "telefone": "Qual é o telefone para contato?", 
                "data": "Para qual data você gostaria de agendar?",
                "horario": "Qual horário prefere?",
                "tipo_consulta": "Que tipo de consulta é esta?"
            }
            
            suggested_questions = [
                field_questions[field] for field in missing_fields 
                if field in field_questions
            ]
            
            result["suggested_questions"] = suggested_questions
            result["is_complete"] = len(missing_fields) == 0
        
        return result
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Retorna o schema da função de extração.
        
        Returns:
            Dict: Schema da função OpenAI
        """
        return self.consulta_schema