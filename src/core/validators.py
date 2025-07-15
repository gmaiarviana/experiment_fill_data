from datetime import datetime, timedelta
import re
from typing import Dict, Any, Optional


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


def parse_relative_date(date_str: str) -> Dict[str, Any]:
    """
    Converte expressões de data relativa para formato ISO.
    
    Args:
        date_str: String com expressão de data relativa
        
    Returns:
        Dict com formato {"valid": bool, "iso_date": str, "error": str}
    """
    try:
        date_str = date_str.lower().strip()
        today = datetime.now()
        
        # Mapeamento de expressões relativas
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
            "mes passado": -30
        }
        
        # Verifica se é uma expressão conhecida
        if date_str in relative_dates:
            days_offset = relative_dates[date_str]
            target_date = today + timedelta(days=days_offset)
            iso_date = target_date.strftime("%Y-%m-%d")
            
            return {
                "valid": True,
                "iso_date": iso_date,
                "original": date_str,
                "error": ""
            }
        
        # Tenta padrões específicos
        patterns = {
            r"em (\d+) dias?": lambda m: int(m.group(1)),
            r"(\d+) dias? atrás": lambda m: -int(m.group(1)),
            r"(\d+) dias? depois": lambda m: int(m.group(1)),
            r"daqui a (\d+) dias?": lambda m: int(m.group(1))
        }
        
        for pattern, func in patterns.items():
            match = re.match(pattern, date_str)
            if match:
                days_offset = func(match)
                target_date = today + timedelta(days=days_offset)
                iso_date = target_date.strftime("%Y-%m-%d")
                
                return {
                    "valid": True,
                    "iso_date": iso_date,
                    "original": date_str,
                    "error": ""
                }
        
        return {
            "valid": False,
            "iso_date": "",
            "original": date_str,
            "error": "Expressão de data não reconhecida"
        }
        
    except Exception as e:
        return {
            "valid": False,
            "iso_date": "",
            "original": date_str,
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