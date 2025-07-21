from typing import Dict, Any, Optional, List
from loguru import logger
from src.core.openai_client import OpenAIClient
from src.core.data_normalizer import normalize_consulta_data
from src.core.validators import parse_relative_time, parse_relative_date
import re


class EntityExtractor:
    """
    Extrator de entidades para consultas médicas usando OpenAI function calling.
    """
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        """
        Inicializa o extrator com cliente OpenAI e schema da função.
        
        Args:
            openai_client: Cliente OpenAI opcional para dependency injection.
                          Se None, cria uma nova instância.
        """
        self.openai_client = openai_client or OpenAIClient()
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
                        "description": "Data da consulta (aceita expressões como 'amanhã', 'próxima segunda', 'semana que vem' ou formato YYYY-MM-DD)"
                    },
                    "horario": {
                        "type": "string",
                        "description": "Horário da consulta (aceita expressões como '12', '12:00', 'meio-dia', 'tarde', 'manhã' ou formato HH:MM)"
                    },
                    "tipo_consulta": {
                        "type": "string",
                        "description": "Tipo de consulta (ex: rotina, urgente, retorno, primeira consulta)"
                    }
                },
                "required": []
            }
        }
    
    async def extract_consulta_entities(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extrai entidades de consulta de uma mensagem em linguagem natural.
        
        Args:
            message (str): Mensagem em linguagem natural
            context (Dict[str, Any], optional): Contexto da sessão com dados já extraídos
            
        Returns:
            Dict: Resultado da extração com dados estruturados e confidence score
        """
        # Prepara contexto para melhorar extração
        enhanced_message = self._enhance_message_with_context(message, context)
        
        result = await self.openai_client.extract_entities(
            message=enhanced_message,
            function_schema=self.consulta_schema
        )
        
        if result["success"]:
            # Combina com dados existentes do contexto
            existing_data = context.get("extracted_data", {}) if context else {}
            new_data = result["extracted_data"]
            
            # Atualiza dados existentes com novos dados (novos dados têm prioridade)
            combined_data = {**existing_data, **new_data}
            
            # Aplica processamento temporal aos dados combinados
            processed_data = self._process_temporal_data(combined_data, message)
            result["extracted_data"] = processed_data
            result["temporal_processing_applied"] = True
            
            # Aplica normalização aos dados processados
            try:
                normalization_result = normalize_consulta_data(processed_data)
                
                # Usa dados normalizados e confidence score do normalizador
                result["extracted_data"] = normalization_result["normalized_data"]
                result["confidence_score"] = self._calculate_improved_confidence(
                    normalization_result["normalized_data"],
                    normalization_result["validation_errors"],
                    context,
                    message
                )
                result["normalization_applied"] = True
                
                # Adiciona informações de validação se houver erros
                if normalization_result["validation_errors"]:
                    result["validation_errors"] = normalization_result["validation_errors"]
                    logger.warning(f"Erros de validação na normalização: {normalization_result['validation_errors']}")
                
                logger.info(f"Normalização aplicada com sucesso. Confidence score: {result['confidence_score']:.2f}")
                
            except Exception as e:
                # Se normalização falhar, usa dados processados e loga warning
                logger.warning(f"Falha na normalização, usando dados processados: {str(e)}")
                result["normalization_applied"] = False
                result["normalization_error"] = str(e)
                result["confidence_score"] = self._calculate_improved_confidence(
                    processed_data, [], context, message
                )
            
            # Adiciona informações específicas sobre campos faltantes
            missing_fields = self._get_missing_fields(result["extracted_data"])
            result["missing_fields"] = missing_fields
            
            # Mapeia campos para perguntas amigáveis e contextuais
            field_questions = {
                "nome": "Qual é o nome completo do paciente?",
                "telefone": "Qual é o telefone para contato?", 
                "data": "Para qual data você gostaria de agendar?",
                "horario": "Qual horário prefere?",
                "tipo_consulta": "Que tipo de consulta é esta?"
            }
            
            # Gera perguntas mais específicas baseadas no contexto
            suggested_questions = []
            for field in missing_fields:
                if field in field_questions:
                    suggested_questions.append(field_questions[field])
                else:
                    suggested_questions.append(f"Qual é o {field}?")
            
            result["suggested_questions"] = suggested_questions
            result["is_complete"] = len(missing_fields) == 0
            
            logger.info(f"Confidence score final: {result['confidence_score']:.2f}")
        
        return result
    
    def _enhance_message_with_context(self, message: str, context: Dict[str, Any] = None) -> str:
        """
        Enriquece a mensagem com contexto para melhorar extração.
        
        Args:
            message: Mensagem original
            context: Contexto da sessão
            
        Returns:
            Mensagem enriquecida com contexto
        """
        if not context or not context.get("extracted_data"):
            return message
        
        existing_data = context["extracted_data"]
        context_info = []
        
        # Adiciona informações já conhecidas como contexto
        if existing_data.get("nome"):
            context_info.append(f"nome já informado: {existing_data['nome']}")
        if existing_data.get("telefone"):
            context_info.append(f"telefone já informado: {existing_data['telefone']}")
        if existing_data.get("data"):
            context_info.append(f"data já informada: {existing_data['data']}")
        if existing_data.get("horario"):
            context_info.append(f"horário já informado: {existing_data['horario']}")
        if existing_data.get("tipo_consulta"):
            context_info.append(f"tipo de consulta já informado: {existing_data['tipo_consulta']}")
        
        # Adiciona contexto temporal se detectado
        temporal_info = self._detect_temporal_expressions(message)
        if temporal_info["has_date_expression"] or temporal_info["has_time_expression"]:
            temporal_context = []
            if temporal_info["has_date_expression"]:
                temporal_context.append(f"expressão de data detectada: {temporal_info['date_expression']}")
            if temporal_info["has_time_expression"]:
                temporal_context.append(f"expressão de horário detectada: {temporal_info['time_expression']}")
            if temporal_info["combined_expressions"]:
                temporal_context.append(f"expressões combinadas: {', '.join(temporal_info['combined_expressions'])}")
            
            if temporal_context:
                context_info.append(f"contexto temporal: {'; '.join(temporal_context)}")
        
        if context_info:
            enhanced_message = f"Contexto: {'; '.join(context_info)}. Nova mensagem: {message}"
            logger.debug(f"Mensagem enriquecida com contexto: {enhanced_message}")
            return enhanced_message
        
        return message
    
    def _calculate_improved_confidence(self, extracted_data: Dict[str, Any], validation_errors: List[str], context: Dict[str, Any] = None, message: str = "") -> float:
        """
        Calcula confidence score melhorado baseado em múltiplos fatores.
        
        Args:
            extracted_data: Dados extraídos
            validation_errors: Erros de validação
            context: Contexto da sessão
            message: Mensagem original para análise temporal
            
        Returns:
            Confidence score entre 0.0 e 1.0
        """
        confidence_factors = []
        
        # Fator 1: Número de campos extraídos (0.0 - 0.35)
        extracted_count = len([v for v in extracted_data.values() if v and str(v).strip()])
        total_fields = 5  # nome, telefone, data, horario, tipo_consulta
        if extracted_count > 0:
            field_ratio = extracted_count / total_fields
            confidence_factors.append(field_ratio * 0.35)
        
        # Fator 2: Qualidade dos dados (0.0 - 0.25)
        if not validation_errors:
            confidence_factors.append(0.25)
        else:
            # Penaliza por erros de validação
            error_penalty = min(0.25, len(validation_errors) * 0.1)
            confidence_factors.append(max(0.0, 0.25 - error_penalty))
        
        # Fator 3: Completude dos dados obrigatórios (0.0 - 0.2)
        required_fields = ["nome", "telefone", "data", "horario"]
        required_count = sum(1 for field in required_fields if extracted_data.get(field))
        if required_count > 0:
            required_ratio = required_count / len(required_fields)
            confidence_factors.append(required_ratio * 0.2)
        
        # Fator 4: Progresso da conversa (0.0 - 0.1)
        if context and context.get("conversation_history"):
            history_length = len(context["conversation_history"])
            if history_length > 1:
                # Pequeno bônus para conversas em andamento
                progress_bonus = min(0.1, history_length * 0.02)
                confidence_factors.append(progress_bonus)
        
        # Fator 5: Processamento temporal bem-sucedido (0.0 - 0.1)
        if message:
            temporal_info = self._detect_temporal_expressions(message)
            temporal_bonus = 0.0
            
            # Bônus para expressões temporais detectadas e processadas
            if temporal_info["has_date_expression"] and extracted_data.get("data"):
                temporal_bonus += 0.05
            if temporal_info["has_time_expression"] and extracted_data.get("horario"):
                temporal_bonus += 0.03
            if temporal_info["combined_expressions"]:
                temporal_bonus += 0.02
            
            confidence_factors.append(min(0.1, temporal_bonus))
        
        # Calcula confidence final
        if confidence_factors:
            calculated_confidence = sum(confidence_factors)
            # Garante que está entre 0.0 e 1.0
            return max(0.0, min(1.0, calculated_confidence))
        
        return 0.0
    
    def _get_missing_fields(self, extracted_data: Dict[str, Any]) -> List[str]:
        """
        Identifica campos faltantes baseado nos dados extraídos.
        
        Args:
            extracted_data: Dados extraídos
            
        Returns:
            Lista de campos faltantes
        """
        # Mapeia campos normalizados para campos originais
        field_mapping = {
            "name": "nome",
            "phone": "telefone",
            "consulta_date": "data",
            "horario": "horario",
            "tipo_consulta": "tipo_consulta"
        }
        
        required_fields = ["nome", "telefone", "data", "horario", "tipo_consulta"]
        missing_fields = []
        
        for field in required_fields:
            # Verifica se o campo existe diretamente ou através do mapeamento
            field_value = None
            if field in extracted_data:
                field_value = extracted_data[field]
            else:
                # Procura pelo campo mapeado
                for mapped_key, mapped_field in field_mapping.items():
                    if mapped_field == field and mapped_key in extracted_data:
                        field_value = extracted_data[mapped_key]
                        break
            
            if not field_value or not str(field_value).strip():
                missing_fields.append(field)
        
        return missing_fields
    
    def _detect_temporal_expressions(self, message: str) -> Dict[str, Any]:
        """
        Identifica expressões temporais na mensagem.
        
        Args:
            message: Mensagem para análise
            
        Returns:
            Dict com expressões temporais detectadas
        """
        temporal_info = {
            "has_date_expression": False,
            "has_time_expression": False,
            "date_expression": "",
            "time_expression": "",
            "combined_expressions": []
        }
        
        # Padrões para detectar expressões temporais
        date_patterns = [
            r'\b(amanhã|amanha)\b',
            r'\b(hoje|depois de amanhã|depois de amanha|ontem|anteontem)\b',
            r'\b(próxima|proxima)\s+(segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)\b',
            r'\b(segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)\s+(que vem|próxima|proxima)\b',
            r'\b(semana|mês|mes)\s+(que vem|passada)\b',
            r'\b(próximo|proximo)\s+(dia|mês|mes|ano)\b'
        ]
        
        time_patterns = [
            r'\b(de|pela)\s+(manhã|manha|tarde|noite)\b',
            r'\b(manhã|manha|tarde|noite)\b',
            r'\b(\d{1,2})h?\b',
            r'\b(\d{1,2}):(\d{2})\b',
            r'\b(meio-dia|meio dia|meia-noite|meia noite)\b'
        ]
        
        # Detecta expressões de data
        for pattern in date_patterns:
            matches = re.findall(pattern, message.lower())
            if matches:
                temporal_info["has_date_expression"] = True
                temporal_info["date_expression"] = matches[0] if isinstance(matches[0], str) else " ".join(matches[0])
                break
        
        # Detecta expressões de horário
        for pattern in time_patterns:
            matches = re.findall(pattern, message.lower())
            if matches:
                temporal_info["has_time_expression"] = True
                temporal_info["time_expression"] = matches[0] if isinstance(matches[0], str) else " ".join(matches[0])
                break
        
        # Detecta expressões combinadas como "amanhã de manhã"
        combined_patterns = [
            r'\b(amanhã|amanha)\s+(de\s+)?(manhã|manha|tarde|noite)\b',
            r'\b(hoje)\s+(de\s+)?(manhã|manha|tarde|noite)\b',
            r'\b(próxima|proxima)\s+(segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)\s+(de\s+)?(manhã|manha|tarde|noite)\b'
        ]
        
        for pattern in combined_patterns:
            matches = re.findall(pattern, message.lower())
            if matches:
                temporal_info["combined_expressions"].append(matches[0] if isinstance(matches[0], str) else " ".join(matches[0]))
        
        return temporal_info
    
    def _process_temporal_data(self, extracted_data: Dict[str, Any], message: str) -> Dict[str, Any]:
        """
        Aplica parsers temporais automaticamente aos dados extraídos.
        
        Args:
            extracted_data: Dados extraídos pelo OpenAI
            message: Mensagem original
            
        Returns:
            Dados processados com informações temporais melhoradas
        """
        processed_data = extracted_data.copy()
        temporal_info = self._detect_temporal_expressions(message)
        
        # Processa campo de data se necessário
        if temporal_info["has_date_expression"]:
            date_result = parse_relative_date(temporal_info["date_expression"])
            if date_result["valid"]:
                processed_data["data"] = date_result["iso_date"]
                logger.info(f"Data processada: {temporal_info['date_expression']} -> {date_result['iso_date']}")
        
        # Processa campo de horário se necessário
        if temporal_info["has_time_expression"]:
            time_result = parse_relative_time(temporal_info["time_expression"])
            if time_result["valid"]:
                processed_data["horario"] = time_result["time"]
                logger.info(f"Horário processado: {temporal_info['time_expression']} -> {time_result['time']}")
        
        # Processa expressões combinadas
        for combined_expr in temporal_info["combined_expressions"]:
            # Extrai componentes da expressão combinada
            if "amanhã" in combined_expr or "amanha" in combined_expr:
                # Processa data primeiro
                date_result = parse_relative_date("amanhã")
                if date_result["valid"]:
                    processed_data["data"] = date_result["iso_date"]
                
                # Processa horário
                time_part = combined_expr.replace("amanhã", "").replace("amanha", "").strip()
                if time_part:
                    time_result = parse_relative_time(time_part)
                    if time_result["valid"]:
                        processed_data["horario"] = time_result["time"]
                        logger.info(f"Expressão combinada processada: {combined_expr} -> data: {date_result['iso_date']}, horário: {time_result['time']}")
            
            elif "hoje" in combined_expr:
                # Processa apenas horário para hoje
                time_part = combined_expr.replace("hoje", "").strip()
                if time_part:
                    time_result = parse_relative_time(time_part)
                    if time_result["valid"]:
                        processed_data["horario"] = time_result["time"]
                        logger.info(f"Expressão combinada processada: {combined_expr} -> horário: {time_result['time']}")
        
        return processed_data
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Retorna o schema da função de extração.
        
        Returns:
            Dict: Schema da função OpenAI
        """
        return self.consulta_schema