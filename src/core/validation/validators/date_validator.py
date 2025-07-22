"""
Validador especializado para datas e horários em português brasileiro.

Migrado de src/core/validators.py para eliminar duplicação de lógica.
Implementa parsing de expressões relativas, validação de datas futuras,
e normalização de horários comerciais.
"""

import re
from datetime import datetime, timedelta, date
from typing import Any, List, Dict

from .base_validator import BaseValidator, ValidationResult


class DateValidator(BaseValidator):
    """
    Validador para datas e horários em português brasileiro.
    
    Suporta:
    - Expressões relativas: "amanhã", "próxima segunda", "semana que vem"
    - Formatos absolutos: "DD/MM/AAAA", "YYYY-MM-DD"
    - Dias da semana: "segunda", "terça-feira", etc.
    - Validação de datas futuras
    - Sugestões de datas válidas
    """
    
    def __init__(self, allow_past_dates: bool = False, max_future_months: int = 6):
        """
        Inicializa o validador de datas.
        
        Args:
            allow_past_dates: Se True, permite datas passadas
            max_future_months: Máximo de meses no futuro permitidos
        """
        self.allow_past_dates = allow_past_dates
        self.max_future_months = max_future_months
        
        # Mapeamento de dias da semana
        self.weekdays = {
            "segunda": 0, "segunda-feira": 0, "segunda feira": 0,
            "terça": 1, "terça-feira": 1, "terca": 1, "terca-feira": 1, "terça feira": 1, "terca feira": 1,
            "quarta": 2, "quarta-feira": 2, "quarta feira": 2,
            "quinta": 3, "quinta-feira": 3, "quinta feira": 3,
            "sexta": 4, "sexta-feira": 4, "sexta feira": 4,
            "sábado": 5, "sabado": 5,
            "domingo": 6
        }
        
        # Mapeamento de expressões relativas
        self.relative_expressions = {
            "hoje": 0,
            "amanhã": 1,
            "amanha": 1,
            "depois de amanhã": 2,
            "depois de amanha": 2,
            "ontem": -1,
            "anteontem": -2,
            "próximo dia": 1,
            "proximo dia": 1,
            "dia seguinte": 1,
            "semana que vem": 7,
            "próxima semana": 7,
            "proxima semana": 7,
            "semana passada": -7,
            "mês que vem": 30,
            "mes que vem": 30,
            "próximo mês": 30,
            "proximo mes": 30,
            "mês passado": -30,
            "mes passado": -30,
            "próximo ano": 365,
            "proximo ano": 365,
            "ano que vem": 365,
            "ano passado": -365,
            "próximos dias": 3,
            "proximos dias": 3,
            "próximas semanas": 14,
            "proximas semanas": 14
        }
    
    def validate(self, value: Any, **kwargs) -> ValidationResult:
        """
        Valida expressão de data em português.
        
        Args:
            value: Expressão de data a ser validada
            **kwargs: Parâmetros adicionais
                     - allow_past: sobrescreve allow_past_dates
                     
        Returns:
            ValidationResult com resultado da validação
        """
        if not value:
            return self._create_error_result(
                value,
                ["Data não pode ser vazia"],
                suggestions=self._generate_date_suggestions()
            )
        
        try:
            date_str = str(value).strip().lower()
            
            # Tenta diferentes estratégias de parsing
            result = None
            
            # 1. Expressões de dias da semana
            result = self._parse_weekday_expressions(date_str)
            if result:
                return self._validate_parsed_date(value, result, **kwargs)
            
            # 2. Expressões relativas
            result = self._parse_relative_expressions(date_str)
            if result:
                return self._validate_parsed_date(value, result, **kwargs)
            
            # 3. Formatos absolutos
            result = self._parse_absolute_date(date_str)
            if result:
                return self._validate_parsed_date(value, result, **kwargs)
            
            # 4. Padrões complexos
            result = self._parse_complex_patterns(date_str)
            if result:
                return self._validate_parsed_date(value, result, **kwargs)
            
            # Se nenhum padrão funcionou
            return self._create_error_result(
                value,
                ["Expressão de data não reconhecida"],
                suggestions=self._generate_date_suggestions()
            )
            
        except Exception as e:
            return self._create_error_result(
                value,
                [f"Erro no parsing: {str(e)}"],
                suggestions=self._generate_date_suggestions()
            )
    
    def normalize(self, value: Any, **kwargs) -> str:
        """
        Normaliza expressão de data para formato ISO (YYYY-MM-DD).
        
        Args:
            value: Expressão de data a ser normalizada
            **kwargs: Parâmetros adicionais
            
        Returns:
            Data normalizada em formato ISO ou string vazia se inválida
        """
        result = self.validate(value, **kwargs)
        return result.value if result.is_valid else ""
    
    def suggest(self, value: Any, **kwargs) -> List[str]:
        """
        Gera sugestões de datas válidas.
        
        Args:
            value: Data que falhou na validação
            **kwargs: Parâmetros adicionais
            
        Returns:
            Lista de sugestões de datas
        """
        return self._generate_date_suggestions()
    
    def get_validation_rules(self) -> dict:
        """
        Retorna regras de validação aplicadas.
        
        Returns:
            Dicionário com regras de validação
        """
        return {
            "allow_past_dates": self.allow_past_dates,
            "max_future_months": self.max_future_months,
            "supported_formats": [
                "DD/MM/AAAA", "YYYY-MM-DD",
                "hoje", "amanhã", "próxima segunda",
                "semana que vem", "mês que vem"
            ],
            "weekdays_supported": list(self.weekdays.keys()),
            "relative_expressions": list(self.relative_expressions.keys())
        }
    
    def _parse_weekday_expressions(self, date_str: str) -> Dict[str, Any]:
        """
        Processa expressões de dias da semana.
        
        Args:
            date_str: String com expressão de dia da semana
            
        Returns:
            Dict com resultado do parsing ou None se não reconhecido
        """
        patterns = [
            (r"próxima (\w+)", "next"),
            (r"proxima (\w+)", "next"),
            (r"(\w+) que vem", "next"),
            (r"(\w+) próxima", "next"),
            (r"(\w+) proxima", "next"),
            (r"(\w+)", "current")  # Dia da semana simples
        ]
        
        today = datetime.now()
        
        for pattern, modifier in patterns:
            match = re.match(pattern, date_str)
            if match:
                weekday_name = match.group(1)
                
                if weekday_name in self.weekdays:
                    target_weekday = self.weekdays[weekday_name]
                    current_weekday = today.weekday()
                    
                    if modifier == "next":
                        # Próxima ocorrência do dia da semana
                        days_ahead = (target_weekday - current_weekday) % 7
                        if days_ahead == 0:  # Se for hoje, vai para próxima semana
                            days_ahead = 7
                        target_date = today + timedelta(days=days_ahead)
                    else:
                        # Próxima ocorrência (se for hoje, mantém hoje)
                        days_ahead = (target_weekday - current_weekday) % 7
                        target_date = today + timedelta(days=days_ahead)
                    
                    return {
                        "date": target_date,
                        "iso_date": target_date.strftime("%Y-%m-%d"),
                        "type": "weekday",
                        "original": date_str
                    }
        
        return None
    
    def _parse_relative_expressions(self, date_str: str) -> Dict[str, Any]:
        """
        Processa expressões relativas.
        
        Args:
            date_str: String com expressão relativa
            
        Returns:
            Dict com resultado do parsing ou None se não reconhecido
        """
        today = datetime.now()
        
        # Verifica se é uma expressão conhecida
        if date_str in self.relative_expressions:
            days_offset = self.relative_expressions[date_str]
            target_date = today + timedelta(days=days_offset)
            
            return {
                "date": target_date,
                "iso_date": target_date.strftime("%Y-%m-%d"),
                "type": "relative",
                "original": date_str,
                "offset_days": days_offset
            }
        
        return None
    
    def _parse_absolute_date(self, date_str: str) -> Dict[str, Any]:
        """
        Processa formatos de data absolutos.
        
        Args:
            date_str: String com data absoluta
            
        Returns:
            Dict com resultado do parsing ou None se não reconhecido
        """
        # Formatos suportados
        formats = [
            ("%d/%m/%Y", "DD/MM/AAAA"),
            ("%Y-%m-%d", "YYYY-MM-DD"),
            ("%d-%m-%Y", "DD-MM-AAAA"),
            ("%d.%m.%Y", "DD.MM.AAAA")
        ]
        
        for fmt, description in formats:
            try:
                target_date = datetime.strptime(date_str, fmt)
                
                return {
                    "date": target_date,
                    "iso_date": target_date.strftime("%Y-%m-%d"),
                    "type": "absolute",
                    "original": date_str,
                    "format": description
                }
            except ValueError:
                continue
        
        return None
    
    def _parse_complex_patterns(self, date_str: str) -> Dict[str, Any]:
        """
        Processa padrões complexos com números.
        
        Args:
            date_str: String com padrão complexo
            
        Returns:
            Dict com resultado do parsing ou None se não reconhecido
        """
        today = datetime.now()
        
        patterns = {
            r"em (\d+) dias?": lambda m: int(m.group(1)),
            r"(\d+) dias? atrás": lambda m: -int(m.group(1)),
            r"(\d+) dias? depois": lambda m: int(m.group(1)),
            r"daqui a (\d+) dias?": lambda m: int(m.group(1)),
            r"em (\d+) semanas?": lambda m: int(m.group(1)) * 7,
            r"(\d+) semanas? atrás": lambda m: -int(m.group(1)) * 7,
            r"daqui a (\d+) semanas?": lambda m: int(m.group(1)) * 7,
            r"em (\d+) meses?": lambda m: int(m.group(1)) * 30,
            r"(\d+) meses? atrás": lambda m: -int(m.group(1)) * 30,
            r"daqui a (\d+) meses?": lambda m: int(m.group(1)) * 30
        }
        
        for pattern, func in patterns.items():
            match = re.match(pattern, date_str)
            if match:
                try:
                    days_offset = func(match)
                    target_date = today + timedelta(days=days_offset)
                    
                    return {
                        "date": target_date,
                        "iso_date": target_date.strftime("%Y-%m-%d"),
                        "type": "complex_pattern",
                        "original": date_str,
                        "offset_days": days_offset
                    }
                except (ValueError, OverflowError):
                    continue
        
        return None
    
    def _validate_parsed_date(
        self, 
        original_value: Any, 
        parsed_result: Dict[str, Any], 
        **kwargs
    ) -> ValidationResult:
        """
        Valida uma data já parseada.
        
        Args:
            original_value: Valor original fornecido
            parsed_result: Resultado do parsing
            **kwargs: Parâmetros adicionais
            
        Returns:
            ValidationResult validado
        """
        target_date = parsed_result["date"]
        target_date_only = target_date.date()
        today = datetime.now().date()
        
        # Verifica configuração de datas passadas
        allow_past = kwargs.get("allow_past", self.allow_past_dates)
        
        warnings = []
        errors = []
        
        # Valida datas passadas
        if target_date_only < today and not allow_past:
            errors.append("Não é possível agendar para datas passadas")
            return self._create_error_result(
                original_value,
                errors,
                suggestions=self._generate_date_suggestions()
            )
        elif target_date_only < today:
            warnings.append("Data está no passado")
        
        # Valida datas muito distantes
        max_future_date = today + timedelta(days=self.max_future_months * 30)
        if target_date_only > max_future_date:
            errors.append(f"Data muito distante. Máximo: {self.max_future_months} meses")
            return self._create_error_result(
                original_value,
                errors,
                suggestions=self._generate_date_suggestions()
            )
        
        # Calcula confiança
        confidence = 1.0
        if warnings:
            confidence = 0.8
        if parsed_result["type"] == "complex_pattern":
            confidence = 0.9
        
        return self._create_success_result(
            original_value=original_value,
            normalized_value=parsed_result["iso_date"],
            warnings=warnings,
            confidence=confidence,
            metadata={
                "parsed_date": target_date,
                "parsing_type": parsed_result["type"],
                "is_future": target_date_only >= today,
                "days_from_now": (target_date_only - today).days,
                **{k: v for k, v in parsed_result.items() if k not in ["date", "iso_date"]}
            }
        )
    
    def _generate_date_suggestions(self) -> List[str]:
        """
        Gera sugestões de datas válidas.
        
        Returns:
            Lista de datas de exemplo
        """
        today = datetime.now()
        suggestions = []
        
        # Sugestões relativas
        suggestions.extend([
            "amanhã",
            "próxima segunda",
            "semana que vem"
        ])
        
        # Sugestões absolutas (próximos dias)
        for i in range(1, 4):
            future_date = today + timedelta(days=i)
            suggestions.append(future_date.strftime("%d/%m/%Y"))
        
        return suggestions