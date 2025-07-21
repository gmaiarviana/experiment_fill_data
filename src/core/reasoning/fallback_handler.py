"""
FallbackHandler - Lógica Python quando LLM falha
Implementa estratégias de fallback para garantir funcionamento mesmo sem LLM.
"""

from typing import Dict, Any, List
import re
from datetime import datetime, timedelta
from src.core.logging.logger_factory import get_logger
logger = get_logger(__name__)


class FallbackHandler:
    """
    Handler de fallback que implementa lógica Python para análise de mensagens.
    Usado quando LLM não está disponível ou falha.
    """
    
    def __init__(self):
        """
        Inicializa o handler de fallback.
        """
        logger.info("FallbackHandler inicializado com lógica Python")
    
    async def analyze_message_fallback(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa mensagem usando lógica Python pura.
        
        Args:
            message (str): Mensagem para analisar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da análise com ação decidida
        """
        try:
            logger.info("Executando análise com fallback Python...")
            
            # Normaliza mensagem
            message_lower = message.lower().strip()
            
            # Verifica se há dados para extrair
            has_data_potential = self._has_data_potential(message_lower)
            
            # Verifica se é confirmação
            is_confirmation = self._is_confirmation(message_lower)
            
            # Verifica se é negação
            is_denial = self._is_denial(message_lower)
            
            # Obtém dados existentes
            existing_data = context.get("extracted_data", {})
            
            # Decide ação baseada na análise
            if is_confirmation and self._is_data_complete(existing_data):
                return {
                    "action": "complete",
                    "reason": "Usuário confirmou dados completos",
                    "confidence": 0.8,
                    "response": "Perfeito! Vou finalizar o agendamento."
                }
            elif is_denial:
                return {
                    "action": "ask",
                    "reason": "Usuário negou dados, precisa corrigir",
                    "confidence": 0.7,
                    "missing_fields": self._get_missing_fields(existing_data),
                    "response": "Entendi! Vamos corrigir. Pode me informar novamente?"
                }
            elif has_data_potential:
                return {
                    "action": "extract",
                    "reason": "Mensagem contém dados para extração",
                    "confidence": 0.6,
                    "response": ""
                }
            else:
                # Pergunta próximo campo faltante
                missing_fields = self._get_missing_fields(existing_data)
                if missing_fields:
                    next_field = missing_fields[0]
                    question = self._get_field_question(next_field)
                    return {
                        "action": "ask",
                        "reason": "Solicitando próximo campo obrigatório",
                        "confidence": 0.5,
                        "missing_fields": missing_fields,
                        "response": question
                    }
                else:
                    return {
                        "action": "confirm",
                        "reason": "Todos os dados coletados, solicitando confirmação",
                        "confidence": 0.7,
                        "response": "Perfeito! Vou confirmar os dados da sua consulta."
                    }
                    
        except Exception as e:
            logger.error(f"Erro no fallback handler: {str(e)}")
            return {
                "action": "error",
                "error": str(e),
                "confidence": 0.0
            }
    
    def _has_data_potential(self, message: str) -> bool:
        """
        Verifica se mensagem tem potencial de conter dados.
        
        Args:
            message (str): Mensagem normalizada
            
        Returns:
            bool: True se tem potencial de dados
        """
        # Padrões que indicam dados
        data_patterns = [
            r'\b(meu nome|sou|chamo)\b',
            r'\b(telefone|celular|fone|whatsapp)\b',
            r'\b(consulta|médico|doutor|dr\.)\b',
            r'\b(amanhã|hoje|segunda|terça|quarta|quinta|sexta|sábado|domingo)\b',
            r'\b(\d{1,2}:\d{2}|\d{1,2}h|\d{1,2} horas)\b',
            r'\b(\d{1,2}/\d{1,2}|\d{1,2}-\d{1,2})\b'
        ]
        
        for pattern in data_patterns:
            if re.search(pattern, message):
                return True
        
        return False
    
    def _is_confirmation(self, message: str) -> bool:
        """
        Verifica se mensagem é uma confirmação.
        
        Args:
            message (str): Mensagem normalizada
            
        Returns:
            bool: True se é confirmação
        """
        confirmation_words = [
            'sim', 'certo', 'correto', 'perfeito', 'ok', 'tá bom',
            'confirmo', 'confirma', 'está certo', 'está correto',
            'pode ser', 'concordo', 'aceito'
        ]
        
        return any(word in message for word in confirmation_words)
    
    def _is_denial(self, message: str) -> bool:
        """
        Verifica se mensagem é uma negação.
        
        Args:
            message (str): Mensagem normalizada
            
        Returns:
            bool: True se é negação
        """
        denial_words = [
            'não', 'nao', 'errado', 'incorreto', 'não está certo',
            'não está correto', 'mude', 'corrige', 'corrija',
            'diferente', 'outro', 'outra'
        ]
        
        return any(word in message for word in denial_words)
    
    def _is_data_complete(self, data: Dict[str, Any]) -> bool:
        """
        Verifica se dados estão completos.
        
        Args:
            data (Dict[str, Any]): Dados extraídos
            
        Returns:
            bool: True se dados estão completos
        """
        required_fields = ["nome", "telefone", "data", "horario", "tipo_consulta"]
        return all(data.get(field) for field in required_fields)
    
    def _get_missing_fields(self, data: Dict[str, Any]) -> List[str]:
        """
        Identifica campos obrigatórios que estão faltando.
        
        Args:
            data (Dict[str, Any]): Dados atuais
            
        Returns:
            List[str]: Lista de campos faltantes
        """
        required_fields = ["nome", "telefone", "data", "horario", "tipo_consulta"]
        return [field for field in required_fields if not data.get(field)]
    
    def _get_field_question(self, field: str) -> str:
        """
        Gera pergunta para campo específico.
        
        Args:
            field (str): Campo para perguntar
            
        Returns:
            str: Pergunta formatada
        """
        field_questions = {
            "nome": "Qual é o seu nome completo?",
            "telefone": "Qual é o seu telefone para contato?",
            "data": "Para qual data você gostaria de agendar?",
            "horario": "Qual horário seria melhor para você?",
            "tipo_consulta": "Que tipo de consulta você precisa?"
        }
        
        return field_questions.get(field, f"Pode me informar o {field}?")
    
    def extract_simple_entities(self, message: str) -> Dict[str, Any]:
        """
        Extrai entidades simples usando regex (fallback para EntityExtractor).
        
        Args:
            message (str): Mensagem para extrair
            
        Returns:
            Dict: Entidades extraídas
        """
        entities = {}
        
        # Extrai nome (padrão simples)
        name_patterns = [
            r'\b(meu nome é|sou|chamo)\s+([A-Za-zÀ-ÿ\s]+)',
            r'\b([A-Z][a-zÀ-ÿ]+)\s+([A-Z][a-zÀ-ÿ]+)\b'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message)
            if match:
                if 'meu nome é' in pattern or 'sou' in pattern or 'chamo' in pattern:
                    entities["nome"] = match.group(2).strip()
                else:
                    entities["nome"] = f"{match.group(1)} {match.group(2)}"
                break
        
        # Extrai telefone
        phone_patterns = [
            r'\b(\d{2})\s*(\d{4,5})\s*-\s*(\d{4})\b',
            r'\b(\d{2})\s*(\d{8,9})\b'
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, message)
            if match:
                if len(match.groups()) == 3:
                    entities["telefone"] = f"({match.group(1)}) {match.group(2)}-{match.group(3)}"
                else:
                    entities["telefone"] = f"({match.group(1)}) {match.group(2)}"
                break
        
        # Extrai data
        date_patterns = [
            r'\b(amanhã|hoje)\b',
            r'\b(segunda|terça|quarta|quinta|sexta|sábado|domingo)\s+(feira)?\b',
            r'\b(\d{1,2})/(\d{1,2})\b',
            r'\b(\d{1,2})-(\d{1,2})\b'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, message)
            if match:
                if 'amanhã' in match.group():
                    tomorrow = datetime.now() + timedelta(days=1)
                    entities["data"] = tomorrow.strftime("%d/%m/%Y")
                elif 'hoje' in match.group():
                    entities["data"] = datetime.now().strftime("%d/%m/%Y")
                elif match.groups():
                    day, month = match.groups()
                    year = datetime.now().year
                    entities["data"] = f"{day}/{month}/{year}"
                break
        
        # Extrai horário
        time_patterns = [
            r'\b(\d{1,2}):(\d{2})\b',
            r'\b(\d{1,2})h\b',
            r'\b(\d{1,2})\s+horas?\b'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message)
            if match:
                if ':' in pattern:
                    hour, minute = match.groups()
                    entities["horario"] = f"{hour}:{minute}"
                else:
                    hour = match.group(1)
                    entities["horario"] = f"{hour}:00"
                break
        
        # Extrai tipo de consulta
        consulta_patterns = [
            r'\b(consulta|médico|doutor|dr\.)\b',
            r'\b(clínico|cardio|neuro|pediatra|gineco|ortopedista)\b'
        ]
        
        for pattern in consulta_patterns:
            match = re.search(pattern, message)
            if match:
                entities["tipo_consulta"] = match.group(1)
                break
        
        return entities
    
    def validate_simple_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida dados usando lógica simples (fallback para validators).
        
        Args:
            data (Dict[str, Any]): Dados para validar
            
        Returns:
            Dict: Resultado da validação
        """
        errors = []
        confidence = 0.8
        
        # Valida nome
        if "nome" in data:
            nome = data["nome"]
            if len(nome.split()) < 2:
                errors.append("Nome deve ter pelo menos nome e sobrenome")
                confidence -= 0.2
        
        # Valida telefone
        if "telefone" in data:
            telefone = data["telefone"]
            if not re.match(r'\(\d{2}\)\s*\d{4,5}-\d{4}', telefone):
                errors.append("Telefone deve estar no formato (11) 99999-9999")
                confidence -= 0.2
        
        # Valida data
        if "data" in data:
            data_str = data["data"]
            try:
                datetime.strptime(data_str, "%d/%m/%Y")
            except ValueError:
                errors.append("Data deve estar no formato DD/MM/AAAA")
                confidence -= 0.2
        
        # Valida horário
        if "horario" in data:
            horario = data["horario"]
            if not re.match(r'\d{1,2}:\d{2}', horario):
                errors.append("Horário deve estar no formato HH:MM")
                confidence -= 0.2
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "confidence": max(confidence, 0.1)
        } 