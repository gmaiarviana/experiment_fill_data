"""
ARQUIVO DEPRECIADO - Technical Debt #1 RESOLVIDO

Este arquivo foi substituído pelo novo sistema modular de validação em:
src/core/validation/

NOVO SISTEMA:
- src/core/validation/validators/phone_validator.py
- src/core/validation/validators/date_validator.py  
- src/core/validation/validators/name_validator.py
- src/core/validation/validators/document_validator.py
- src/core/validation/normalizers/data_normalizer.py

MANTIDO TEMPORARIAMENTE para compatibilidade com módulos legados.
TODO: Migrar módulos restantes e remover este arquivo.
"""

from datetime import datetime, timedelta, date
import re
import time
from typing import Dict, Any, Optional, List


def validate_brazilian_phone(phone: str) -> Dict[str, Any]:
    """
    Valida e formata número de telefone brasileiro.
    
    Args:
        phone: String com o número de telefone
        
    Returns:
        Dict com formato {"valid": bool, "formatted": str, "error": str}
    """
    try:
        # Remove todos os caracteres não numéricos
        digits_only = re.sub(r'\D', '', phone)
        
        # Valida se tem 10 ou 11 dígitos (com DDD)
        if len(digits_only) not in [10, 11]:
            return {
                "valid": False,
                "formatted": "",
                "error": "Número deve ter 10 ou 11 dígitos (com DDD)"
            }
        
        # Valida DDD (deve estar entre 11 e 99)
        ddd = int(digits_only[:2])
        if ddd < 11 or ddd > 99:
            return {
                "valid": False,
                "formatted": "",
                "error": "DDD inválido"
            }
        
        # Formata o número
        if len(digits_only) == 11:
            # Celular: (11) 99999-9999
            formatted = f"({digits_only[:2]}) {digits_only[2:7]}-{digits_only[7:]}"
        else:
            # Fixo: (11) 3333-3333
            formatted = f"({digits_only[:2]}) {digits_only[2:6]}-{digits_only[6:]}"
        
        return {
            "valid": True,
            "formatted": formatted,
            "error": ""
        }
        
    except Exception as e:
        return {
            "valid": False,
            "formatted": "",
            "error": f"Erro na validação: {str(e)}"
        }


def parse_weekday_expressions(date_str: str) -> Dict[str, Any]:
    """
    Processa expressões de dias da semana em português.
    
    Args:
        date_str: String com expressão de dia da semana
        
    Returns:
        Dict com formato {"valid": bool, "iso_date": str, "suggestions": List[str], "error": str}
    """
    try:
        date_str = date_str.lower().strip()
        today = datetime.now()
        
        # Mapeamento de dias da semana
        weekdays = {
            "segunda": 0, "segunda-feira": 0, "segunda feira": 0,
            "terça": 1, "terça-feira": 1, "terca": 1, "terca-feira": 1, "terça feira": 1, "terca feira": 1,
            "quarta": 2, "quarta-feira": 2, "quarta feira": 2,
            "quinta": 3, "quinta-feira": 3, "quinta feira": 3,
            "sexta": 4, "sexta-feira": 4, "sexta feira": 4,
            "sábado": 5, "sabado": 5,
            "domingo": 6
        }
        
        # Padrões para expressões de dias da semana
        patterns = [
            (r"próxima (\w+)", "next"),
            (r"proxima (\w+)", "next"),
            (r"(\w+) que vem", "next"),
            (r"(\w+) próxima", "next"),
            (r"(\w+) proxima", "next"),
            (r"(\w+)", "current")  # Dia da semana simples
        ]
        
        for pattern, modifier in patterns:
            match = re.match(pattern, date_str)
            if match:
                weekday_name = match.group(1)
                
                if weekday_name in weekdays:
                    target_weekday = weekdays[weekday_name]
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
                    
                    iso_date = target_date.strftime("%Y-%m-%d")
                    
                    # Verifica se é uma data futura válida
                    future_validation = validate_future_date(target_date)
                    if not future_validation["valid"]:
                        return {
                            "valid": False,
                            "iso_date": "",
                            "suggestions": future_validation.get("suggestions", []),
                            "error": future_validation["error"]
                        }
                    
                    return {
                        "valid": True,
                        "iso_date": iso_date,
                        "original": date_str,
                        "suggestions": [],
                        "error": ""
                    }
        
        return {
            "valid": False,
            "iso_date": "",
            "original": date_str,
            "suggestions": [],
            "error": "Expressão de dia da semana não reconhecida"
        }
        
    except Exception as e:
        return {
            "valid": False,
            "iso_date": "",
            "original": date_str,
            "suggestions": [],
            "error": f"Erro no parsing: {str(e)}"
        }


def validate_future_date(target_date: datetime) -> Dict[str, Any]:
    """
    Valida se uma data é futura e contextualmente apropriada.
    
    Args:
        target_date: Data a ser validada
        
    Returns:
        Dict com formato {"valid": bool, "error": str, "suggestions": List[str]}
    """
    try:
        today = datetime.now().date()
        target_date_only = target_date.date()
        
        # Se a data é passada
        if target_date_only < today:
            # Calcula próximas sugestões
            suggestions = []
            for i in range(1, 4):  # Próximos 3 dias
                suggestion_date = today + timedelta(days=i)
                suggestions.append(suggestion_date.strftime("%Y-%m-%d"))
            
            return {
                "valid": False,
                "error": "Não é possível agendar para datas passadas",
                "suggestions": suggestions
            }
        
        # Se a data é muito distante (mais de 6 meses)
        six_months_later = today + timedelta(days=180)
        if target_date_only > six_months_later:
            return {
                "valid": False,
                "error": "Data muito distante. Considere uma data mais próxima",
                "suggestions": []
            }
        
        return {
            "valid": True,
            "error": "",
            "suggestions": []
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": f"Erro na validação: {str(e)}",
            "suggestions": []
        }


def parse_relative_date(date_str: str) -> Dict[str, Any]:
    """
    Converte expressões de data relativa para formato ISO.
    
    Args:
        date_str: String com expressão de data relativa
        
    Returns:
        Dict com formato {"valid": bool, "iso_date": str, "suggestions": List[str], "error": str}
    """
    try:
        date_str = date_str.lower().strip()
        today = datetime.now()
        
        # Primeiro, tenta processar expressões de dias da semana
        weekday_result = parse_weekday_expressions(date_str)
        if weekday_result["valid"]:
            return weekday_result
        
        # Mapeamento de expressões relativas expandido
        relative_dates = {
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
            # Novas expressões de período
            "próximo ano": 365,
            "proximo ano": 365,
            "ano que vem": 365,
            "ano passado": -365,
            "próximos dias": 3,
            "proximos dias": 3,
            "próximas semanas": 14,
            "proximas semanas": 14
        }
        
        # Verifica se é uma expressão conhecida
        if date_str in relative_dates:
            days_offset = relative_dates[date_str]
            target_date = today + timedelta(days=days_offset)
            
            # Valida se é uma data futura apropriada
            future_validation = validate_future_date(target_date)
            if not future_validation["valid"]:
                return {
                    "valid": False,
                    "iso_date": "",
                    "original": date_str,
                    "suggestions": future_validation.get("suggestions", []),
                    "error": future_validation["error"]
                }
            
            iso_date = target_date.strftime("%Y-%m-%d")
            
            return {
                "valid": True,
                "iso_date": iso_date,
                "original": date_str,
                "suggestions": [],
                "error": ""
            }
        
        # Tenta padrões específicos expandidos
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
                days_offset = func(match)
                target_date = today + timedelta(days=days_offset)
                
                # Valida se é uma data futura apropriada
                future_validation = validate_future_date(target_date)
                if not future_validation["valid"]:
                    return {
                        "valid": False,
                        "iso_date": "",
                        "original": date_str,
                        "suggestions": future_validation.get("suggestions", []),
                        "error": future_validation["error"]
                    }
                
                iso_date = target_date.strftime("%Y-%m-%d")
                
                return {
                    "valid": True,
                    "iso_date": iso_date,
                    "original": date_str,
                    "suggestions": [],
                    "error": ""
                }
        
        # Se não encontrou padrão, retorna erro com sugestões
        suggestions = [
            (today + timedelta(days=1)).strftime("%Y-%m-%d"),  # amanhã
            (today + timedelta(days=7)).strftime("%Y-%m-%d"),  # semana que vem
            (today + timedelta(days=30)).strftime("%Y-%m-%d")  # mês que vem
        ]
        
        return {
            "valid": False,
            "iso_date": "",
            "original": date_str,
            "suggestions": suggestions,
            "error": "Expressão de data não reconhecida. Tente: 'amanhã', 'próxima segunda', 'semana que vem'"
        }
        
    except Exception as e:
        return {
            "valid": False,
            "iso_date": "",
            "original": date_str,
            "suggestions": [],
            "error": f"Erro no parsing: {str(e)}"
        }


def normalize_name(name: str) -> str:
    """
    Normaliza nome próprio com capitalização adequada.
    
    Args:
        name: String com o nome a ser normalizado
        
    Returns:
        String com o nome normalizado
    """
    try:
        if not name or not name.strip():
            return ""
        
        # Lista de preposições e artigos que devem ficar em minúsculo
        lowercase_words = {
            'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'nas', 'nos',
            'para', 'por', 'com', 'sem', 'sob', 'sobre', 'entre', 'contra',
            'desde', 'até', 'até', 'ante', 'após', 'perante', 'segundo',
            'conforme', 'mediante', 'salvo', 'exceto', 'menos', 'fora'
        }
        
        # Remove espaços extras e divide em palavras
        words = name.strip().split()
        normalized_words = []
        
        for i, word in enumerate(words):
            word = word.lower()
            
            # Primeira palavra sempre capitalizada
            if i == 0:
                normalized_words.append(word.capitalize())
            # Última palavra sempre capitalizada
            elif i == len(words) - 1:
                normalized_words.append(word.capitalize())
            # Palavras do meio: capitaliza se não for preposição/artigo
            elif word not in lowercase_words:
                normalized_words.append(word.capitalize())
            else:
                normalized_words.append(word)
        
        return " ".join(normalized_words)
        
    except Exception as e:
        # Em caso de erro, retorna o nome original
        return name


def calculate_validation_confidence(data: Dict[str, Any]) -> float:
    """
    Calcula nível de confiança baseado na qualidade dos dados.
    
    Args:
        data: Dicionário com os dados a serem avaliados
        
    Returns:
        Float entre 0.0 e 1.0 representando o nível de confiança
    """
    try:
        if not data:
            return 0.0
        
        confidence_score = 0.0
        total_checks = 0
        
        # Verifica completude dos campos obrigatórios
        required_fields = ['name', 'phone', 'email']
        for field in required_fields:
            total_checks += 1
            if field in data and data[field]:
                value = str(data[field]).strip()
                if value:
                    confidence_score += 1.0
        
        # Verifica qualidade do telefone
        if 'phone' in data and data['phone']:
            phone_result = validate_brazilian_phone(str(data['phone']))
            total_checks += 1
            if phone_result['valid']:
                confidence_score += 1.0
        
        # Verifica formato de email
        if 'email' in data and data['email']:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            total_checks += 1
            if re.match(email_pattern, str(data['email'])):
                confidence_score += 1.0
        
        # Verifica normalização do nome
        if 'name' in data and data['name']:
            normalized = normalize_name(str(data['name']))
            total_checks += 1
            if normalized and len(normalized.split()) >= 2:
                confidence_score += 1.0
        
        # Verifica consistência de dados
        if len(data) >= 3:
            total_checks += 1
            confidence_score += 1.0
        
        # Calcula confiança final
        if total_checks == 0:
            return 0.0
        
        confidence = confidence_score / total_checks
        
        # Ajusta para escala 0.0-1.0
        return min(max(confidence, 0.0), 1.0)
        
    except Exception as e:
        return 0.0


def validate_brazilian_cpf(cpf: str) -> Dict[str, Any]:
    """
    Valida CPF brasileiro.
    
    Args:
        cpf: String com o CPF
        
    Returns:
        Dict com formato {"valid": bool, "formatted": str, "error": str}
    """
    try:
        # Remove caracteres não numéricos
        digits = re.sub(r'\D', '', cpf)
        
        # Verifica se tem 11 dígitos
        if len(digits) != 11:
            return {
                "valid": False,
                "formatted": "",
                "error": "CPF deve ter 11 dígitos"
            }
        
        # Verifica se todos os dígitos são iguais
        if len(set(digits)) == 1:
            return {
                "valid": False,
                "formatted": "",
                "error": "CPF inválido (todos os dígitos iguais)"
            }
        
        # Calcula primeiro dígito verificador
        sum1 = sum(int(digits[i]) * (10 - i) for i in range(9))
        remainder1 = sum1 % 11
        digit1 = 0 if remainder1 < 2 else 11 - remainder1
        
        # Calcula segundo dígito verificador
        sum2 = sum(int(digits[i]) * (11 - i) for i in range(10))
        remainder2 = sum2 % 11
        digit2 = 0 if remainder2 < 2 else 11 - remainder2
        
        # Verifica se os dígitos verificadores estão corretos
        if int(digits[9]) == digit1 and int(digits[10]) == digit2:
            formatted = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
            return {
                "valid": True,
                "formatted": formatted,
                "error": ""
            }
        else:
            return {
                "valid": False,
                "formatted": "",
                "error": "CPF inválido"
            }
            
    except Exception as e:
        return {
            "valid": False,
            "formatted": "",
            "error": f"Erro na validação: {str(e)}"
        }


def validate_brazilian_cep(cep: str) -> Dict[str, Any]:
    """
    Valida CEP brasileiro.
    
    Args:
        cep: String com o CEP
        
    Returns:
        Dict com formato {"valid": bool, "formatted": str, "error": str}
    """
    try:
        # Remove caracteres não numéricos
        digits = re.sub(r'\D', '', cep)
        
        # Verifica se tem 8 dígitos
        if len(digits) != 8:
            return {
                "valid": False,
                "formatted": "",
                "error": "CEP deve ter 8 dígitos"
            }
        
        # Formata o CEP
        formatted = f"{digits[:5]}-{digits[5:]}"
        
        return {
            "valid": True,
            "formatted": formatted,
            "error": ""
        }
        
    except Exception as e:
        return {
            "valid": False,
            "formatted": "",
            "error": f"Erro na validação: {str(e)}"
        }


def validate_business_hours(time_str: str) -> Dict[str, Any]:
    """
    Valida se um horário está dentro do horário comercial (7h-22h).
    
    Args:
        time_str: String com o horário no formato HH:MM ou HH
        
    Returns:
        Dict com formato {"valid": bool, "error": str, "suggestions": List[str]}
    """
    try:
        # Remove espaços e converte para minúsculo
        time_str = time_str.strip().lower()
        
        # Padrões para extrair hora e minuto
        patterns = [
            r'(\d{1,2}):(\d{2})',  # HH:MM
            r'(\d{1,2})h',         # HHh
            r'(\d{1,2})',          # HH
        ]
        
        hour = None
        minute = 0
        
        for pattern in patterns:
            match = re.match(pattern, time_str)
            if match:
                hour = int(match.group(1))
                if len(match.groups()) > 1:
                    minute = int(match.group(2))
                break
        
        if hour is None:
            return {
                "valid": False,
                "error": "Formato de horário não reconhecido",
                "suggestions": ["8:00", "9:00", "10:00", "14:00", "15:00", "16:00"]
            }
        
        # Valida hora e minuto
        if hour < 0 or hour > 23:
            return {
                "valid": False,
                "error": "Hora deve estar entre 0 e 23",
                "suggestions": ["8:00", "9:00", "10:00", "14:00", "15:00", "16:00"]
            }
        
        if minute < 0 or minute > 59:
            return {
                "valid": False,
                "error": "Minuto deve estar entre 0 e 59",
                "suggestions": ["8:00", "9:00", "10:00", "14:00", "15:00", "16:00"]
            }
        
        # Converte para minutos desde meia-noite
        total_minutes = hour * 60 + minute
        
        # Horário comercial: 7h (420 min) até 22h (1320 min)
        business_start = 7 * 60  # 7:00
        business_end = 22 * 60   # 22:00
        
        if total_minutes < business_start or total_minutes > business_end:
            suggestions = suggest_time_slots("manhã") + suggest_time_slots("tarde")
            return {
                "valid": False,
                "error": "Horário fora do horário comercial (7h-22h)",
                "suggestions": suggestions
            }
        
        return {
            "valid": True,
            "error": "",
            "suggestions": []
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": f"Erro na validação: {str(e)}",
            "suggestions": ["8:00", "9:00", "10:00", "14:00", "15:00", "16:00"]
        }


def suggest_time_slots(period: str) -> List[str]:
    """
    Sugere horários específicos para um período do dia.
    
    Args:
        period: String com o período ("manhã", "tarde", "noite")
        
    Returns:
        Lista de strings com horários sugeridos
    """
    try:
        period = period.lower().strip()
        
        if period in ["manhã", "manha", "de manhã", "de manha", "pela manhã", "pela manha"]:
            return ["8:00", "8:30", "9:00", "9:30", "10:00", "10:30", "11:00"]
        elif period in ["tarde", "à tarde", "a tarde", "pela tarde", "final da tarde"]:
            return ["13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"]
        elif period in ["noite", "à noite", "a noite", "pela noite"]:
            return ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"]
        else:
            # Sugestões gerais para horário comercial
            return ["8:00", "9:00", "10:00", "14:00", "15:00", "16:00", "17:00"]
            
    except Exception as e:
        return ["8:00", "9:00", "10:00", "14:00", "15:00", "16:00"]


def parse_relative_time(time_str: str) -> Dict[str, Any]:
    """
    Processa expressões de horário relativo em português.
    
    Args:
        time_str: String com expressão de horário
        
    Returns:
        Dict com formato {"valid": bool, "time": str, "suggestions": List[str], "period": str, "error": str}
    """
    try:
        time_str = time_str.lower().strip()
        
        # Mapeamento de períodos do dia
        periods = {
            "manhã": {"start": 8, "end": 11, "suggestions": ["8:00", "8:30", "9:00", "9:30", "10:00", "10:30", "11:00"]},
            "manha": {"start": 8, "end": 11, "suggestions": ["8:00", "8:30", "9:00", "9:30", "10:00", "10:30", "11:00"]},
            "tarde": {"start": 13, "end": 17, "suggestions": ["13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"]},
            "noite": {"start": 18, "end": 21, "suggestions": ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"]}
        }
        
        # Padrões para expressões de período
        period_patterns = [
            (r"de manhã", "manhã"),
            (r"de manha", "manhã"),
            (r"à tarde", "tarde"),
            (r"a tarde", "tarde"),
            (r"pela manhã", "manhã"),
            (r"pela manha", "manhã"),
            (r"pela tarde", "tarde"),
            (r"final da tarde", "tarde"),
            (r"à noite", "noite"),
            (r"a noite", "noite"),
            (r"pela noite", "noite"),
            (r"manhã", "manhã"),
            (r"manha", "manhã"),
            (r"tarde", "tarde"),
            (r"noite", "noite")
        ]
        
        # Verifica se é uma expressão de período
        for pattern, period in period_patterns:
            if re.match(pattern, time_str):
                period_info = periods.get(period, {})
                suggestions = period_info.get("suggestions", ["8:00", "9:00", "10:00", "14:00", "15:00", "16:00"])
                
                return {
                    "valid": True,
                    "time": f"{period_info.get('start', 9)}:00",
                    "suggestions": suggestions,
                    "period": period,
                    "error": ""
                }
        
        # Padrões para horários específicos
        specific_patterns = [
            (r"(\d{1,2}):(\d{2})", lambda m: f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"),  # HH:MM
            (r"(\d{1,2})h", lambda m: f"{int(m.group(1)):02d}:00"),  # HHh
            (r"(\d{1,2})", lambda m: f"{int(m.group(1)):02d}:00"),   # HH
            (r"meio-dia", lambda m: "12:00"),
            (r"meio dia", lambda m: "12:00"),
            (r"meia-noite", lambda m: "00:00"),
            (r"meia noite", lambda m: "00:00"),
            (r"meio dia", lambda m: "12:00"),
            (r"meia noite", lambda m: "00:00")
        ]
        
        for pattern, formatter in specific_patterns:
            match = re.match(pattern, time_str)
            if match:
                try:
                    time_formatted = formatter(match)
                    
                    # Valida o horário comercial
                    business_validation = validate_business_hours(time_formatted)
                    if not business_validation["valid"]:
                        return {
                            "valid": False,
                            "time": time_formatted,
                            "suggestions": business_validation.get("suggestions", []),
                            "period": "",
                            "error": business_validation["error"]
                        }
                    
                    # Determina o período
                    hour = int(time_formatted.split(":")[0])
                    if 6 <= hour <= 11:
                        period = "manhã"
                    elif 12 <= hour <= 17:
                        period = "tarde"
                    elif 18 <= hour <= 21:
                        period = "noite"
                    else:
                        period = ""
                    
                    return {
                        "valid": True,
                        "time": time_formatted,
                        "suggestions": [],
                        "period": period,
                        "error": ""
                    }
                    
                except (ValueError, IndexError):
                    continue
        
        # Se não encontrou padrão, retorna erro com sugestões
        suggestions = ["8:00", "9:00", "10:00", "14:00", "15:00", "16:00"]
        
        return {
            "valid": False,
            "time": "",
            "suggestions": suggestions,
            "period": "",
            "error": "Expressão de horário não reconhecida. Tente: '9h', '14:30', 'manhã', 'tarde'"
        }
        
    except Exception as e:
        return {
            "valid": False,
            "time": "",
            "suggestions": ["8:00", "9:00", "10:00", "14:00", "15:00", "16:00"],
            "period": "",
            "error": f"Erro no parsing: {str(e)}"
        }


def validate_consulta_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida dados de consulta médica.
    
    Args:
        data: Dicionário com dados da consulta
        
    Returns:
        Dict com formato {"is_valid": bool, "errors": List[str], "confidence": float}
    """
    try:
        errors = []
        confidence = 0.8
        
        # Valida nome
        if "nome" in data and data["nome"]:
            nome = str(data["nome"]).strip()
            if len(nome.split()) < 2:
                errors.append("Nome deve ter pelo menos nome e sobrenome")
                confidence -= 0.2
        
        # Valida telefone
        if "telefone" in data and data["telefone"]:
            telefone = str(data["telefone"])
            phone_result = validate_brazilian_phone(telefone)
            if not phone_result["valid"]:
                errors.append(f"Telefone inválido: {phone_result['error']}")
                confidence -= 0.2
        
        # Valida data
        if "data" in data and data["data"]:
            data_str = str(data["data"])
            # Tenta parsear data em diferentes formatos
            try:
                # Formato DD/MM/YYYY
                if '/' in data_str:
                    datetime.strptime(data_str, "%d/%m/%Y")
                # Formato YYYY-MM-DD
                elif '-' in data_str:
                    datetime.strptime(data_str, "%Y-%m-%d")
                else:
                    # Tenta expressões relativas
                    date_result = parse_relative_date(data_str)
                    if not date_result["valid"]:
                        errors.append("Data deve estar no formato DD/MM/AAAA ou ser uma expressão válida")
                        confidence -= 0.2
            except ValueError:
                errors.append("Data deve estar no formato DD/MM/AAAA")
                confidence -= 0.2
        
        # Valida horário
        if "horario" in data and data["horario"]:
            horario = str(data["horario"])
            if not re.match(r'\d{1,2}:\d{2}', horario):
                errors.append("Horário deve estar no formato HH:MM")
                confidence -= 0.2
        
        # Valida tipo de consulta
        if "tipo_consulta" in data and data["tipo_consulta"]:
            tipo = str(data["tipo_consulta"]).strip()
            if len(tipo) < 3:
                errors.append("Tipo de consulta deve ter pelo menos 3 caracteres")
                confidence -= 0.1
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "confidence": max(confidence, 0.1)
        }
        
    except Exception as e:
        return {
            "is_valid": False,
            "errors": [f"Erro na validação: {str(e)}"],
            "confidence": 0.0
        } 