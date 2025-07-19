from typing import Dict, Any, Optional
import logging
from datetime import datetime

from src.core.validators import (
    validate_brazilian_phone, 
    parse_relative_date, 
    normalize_name, 
    calculate_validation_confidence,
    validate_brazilian_cpf,
    validate_brazilian_cep
)

logger = logging.getLogger(__name__)


def normalize_consulta_data(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza dados de consulta aplicando validadores específicos.
    
    Args:
        extracted_data: Dicionário com dados extraídos da consulta
        
    Returns:
        Dicionário com dados normalizados e metadados de validação
    """
    try:
        if not extracted_data:
            return {
                "normalized_data": {},
                "original_data": {},
                "validation_errors": ["Dados vazios"],
                "confidence_score": 0.0
            }
        
        # Preserva dados originais
        original_data = extracted_data.copy()
        normalized_data = {}
        validation_errors = []
        validation_scores = []
        
        # Mapeamento de campos em português para inglês
        field_mapping = {
            'nome': 'name',
            'telefone': 'phone',
            'data': 'consulta_date',
            'data_consulta': 'consulta_date',
            'email': 'email',
            'cpf': 'cpf',
            'cep': 'cep',
            'endereco': 'endereco',
            'observacoes': 'observacoes',
            'motivo_consulta': 'motivo_consulta',
            'especialidade': 'especialidade',
            'tipo_consulta': 'tipo_consulta',
            'horario': 'horario'
        }
        
        # Normaliza nome (aceita 'name' ou 'nome')
        name_fields = ['name', 'nome']
        name_value = None
        for field in name_fields:
            if field in extracted_data and extracted_data[field]:
                name_value = extracted_data[field]
                break
        
        if name_value:
            try:
                normalized_name = normalize_name(str(name_value))
                if normalized_name:
                    normalized_data['name'] = normalized_name
                    validation_scores.append(1.0)
                else:
                    validation_errors.append("Nome inválido ou vazio")
                    validation_scores.append(0.0)
            except Exception as e:
                validation_errors.append(f"Erro na normalização do nome: {str(e)}")
                validation_scores.append(0.0)
        
        # Normaliza telefone (aceita 'phone' ou 'telefone')
        phone_fields = ['phone', 'telefone']
        phone_value = None
        for field in phone_fields:
            if field in extracted_data and extracted_data[field]:
                phone_value = extracted_data[field]
                break
        
        if phone_value:
            try:
                phone_result = validate_brazilian_phone(str(phone_value))
                if phone_result['valid']:
                    normalized_data['phone'] = phone_result['formatted']
                    validation_scores.append(1.0)
                else:
                    validation_errors.append(f"Telefone inválido: {phone_result['error']}")
                    validation_scores.append(0.0)
            except Exception as e:
                validation_errors.append(f"Erro na validação do telefone: {str(e)}")
                validation_scores.append(0.0)
        
        # Normaliza email
        if 'email' in extracted_data and extracted_data['email']:
            try:
                email = str(extracted_data['email']).strip().lower()
                if '@' in email and '.' in email.split('@')[1]:
                    normalized_data['email'] = email
                    validation_scores.append(1.0)
                else:
                    validation_errors.append("Email em formato inválido")
                    validation_scores.append(0.0)
            except Exception as e:
                validation_errors.append(f"Erro na validação do email: {str(e)}")
                validation_scores.append(0.0)
        
        # Normaliza CPF
        if 'cpf' in extracted_data and extracted_data['cpf']:
            try:
                cpf_result = validate_brazilian_cpf(str(extracted_data['cpf']))
                if cpf_result['valid']:
                    normalized_data['cpf'] = cpf_result['formatted']
                    validation_scores.append(1.0)
                else:
                    validation_errors.append(f"CPF inválido: {cpf_result['error']}")
                    validation_scores.append(0.0)
            except Exception as e:
                validation_errors.append(f"Erro na validação do CPF: {str(e)}")
                validation_scores.append(0.0)
        
        # Normaliza CEP
        if 'cep' in extracted_data and extracted_data['cep']:
            try:
                cep_result = validate_brazilian_cep(str(extracted_data['cep']))
                if cep_result['valid']:
                    normalized_data['cep'] = cep_result['formatted']
                    validation_scores.append(1.0)
                else:
                    validation_errors.append(f"CEP inválido: {cep_result['error']}")
                    validation_scores.append(0.0)
            except Exception as e:
                validation_errors.append(f"Erro na validação do CEP: {str(e)}")
                validation_scores.append(0.0)
        
        # Normaliza data de consulta (aceita 'consulta_date', 'data', 'data_consulta')
        date_fields = ['consulta_date', 'data', 'data_consulta']
        date_value = None
        for field in date_fields:
            if field in extracted_data and extracted_data[field]:
                date_value = extracted_data[field]
                break
        
        if date_value:
            try:
                # Verifica se já é uma data ISO válida (YYYY-MM-DD)
                import re
                iso_date_pattern = r'^\d{4}-\d{2}-\d{2}$'
                
                if re.match(iso_date_pattern, str(date_value)):
                    # Já é uma data ISO válida
                    normalized_data['consulta_date'] = str(date_value)
                    validation_scores.append(1.0)
                else:
                    # Tenta processar como expressão relativa
                    date_result = parse_relative_date(str(date_value))
                    if date_result['valid']:
                        normalized_data['consulta_date'] = date_result['iso_date']
                        validation_scores.append(1.0)
                    else:
                        validation_errors.append(f"Data inválida: {date_result['error']}")
                        validation_scores.append(0.0)
            except Exception as e:
                validation_errors.append(f"Erro na validação da data: {str(e)}")
                validation_scores.append(0.0)
        
        # Normaliza outros campos de texto
        text_fields = ['endereco', 'observacoes', 'motivo_consulta', 'especialidade', 'tipo_consulta', 'horario']
        for field in text_fields:
            if field in extracted_data and extracted_data[field]:
                try:
                    text_value = str(extracted_data[field]).strip()
                    if text_value:
                        normalized_data[field] = text_value
                        validation_scores.append(0.8)  # Score menor para campos de texto livre
                except Exception as e:
                    validation_errors.append(f"Erro na normalização do campo {field}: {str(e)}")
                    validation_scores.append(0.0)
        
        # Calcula confidence score ajustado
        confidence_score = calculate_adjusted_confidence(
            normalized_data, 
            validation_scores, 
            validation_errors
        )
        
        return {
            "normalized_data": normalized_data,
            "original_data": original_data,
            "validation_errors": validation_errors,
            "confidence_score": confidence_score,
            "normalization_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na normalização de dados de consulta: {str(e)}")
        return {
            "normalized_data": {},
            "original_data": extracted_data,
            "validation_errors": [f"Erro geral na normalização: {str(e)}"],
            "confidence_score": 0.0,
            "normalization_timestamp": datetime.now().isoformat()
        }


def normalize_extracted_entities(data: Dict[str, Any], domain: str = "consulta") -> Dict[str, Any]:
    """
    Função genérica para normalizar entidades extraídas de diferentes domínios.
    
    Args:
        data: Dicionário com entidades extraídas
        domain: Domínio dos dados ("consulta", "cadastro", "agendamento", etc.)
        
    Returns:
        Dicionário com entidades normalizadas e metadados
    """
    try:
        if not data:
            return {
                "normalized_entities": {},
                "original_entities": {},
                "domain": domain,
                "validation_errors": ["Dados vazios"],
                "confidence_score": 0.0
            }
        
        # Preserva dados originais
        original_entities = data.copy()
        normalized_entities = {}
        validation_errors = []
        validation_scores = []
        
        # Mapeamento de campos por domínio
        domain_field_mapping = {
            "consulta": {
                "name": "nome",
                "phone": "telefone", 
                "email": "email",
                "cpf": "cpf",
                "consulta_date": "data_consulta",
                "specialty": "especialidade"
            },
            "cadastro": {
                "name": "nome_completo",
                "phone": "telefone",
                "email": "email",
                "cpf": "cpf",
                "cep": "cep",
                "address": "endereco"
            },
            "agendamento": {
                "name": "nome_paciente",
                "phone": "telefone",
                "appointment_date": "data_agendamento",
                "specialty": "especialidade",
                "doctor": "medico"
            }
        }
        
        field_mapping = domain_field_mapping.get(domain, {})
        
        # Normaliza cada entidade encontrada
        for entity_type, entity_value in data.items():
            try:
                # Mapeia o tipo de entidade para o campo correspondente
                mapped_field = field_mapping.get(entity_type, entity_type)
                
                if entity_type in ['name', 'nome', 'nome_completo', 'nome_paciente']:
                    normalized_value = normalize_name(str(entity_value))
                    if normalized_value:
                        normalized_entities[mapped_field] = normalized_value
                        validation_scores.append(1.0)
                    else:
                        validation_errors.append(f"Nome inválido: {entity_value}")
                        validation_scores.append(0.0)
                
                elif entity_type in ['phone', 'telefone']:
                    phone_result = validate_brazilian_phone(str(entity_value))
                    if phone_result['valid']:
                        normalized_entities[mapped_field] = phone_result['formatted']
                        validation_scores.append(1.0)
                    else:
                        validation_errors.append(f"Telefone inválido: {phone_result['error']}")
                        validation_scores.append(0.0)
                
                elif entity_type in ['email']:
                    email = str(entity_value).strip().lower()
                    if '@' in email and '.' in email.split('@')[1]:
                        normalized_entities[mapped_field] = email
                        validation_scores.append(1.0)
                    else:
                        validation_errors.append(f"Email inválido: {entity_value}")
                        validation_scores.append(0.0)
                
                elif entity_type in ['cpf']:
                    cpf_result = validate_brazilian_cpf(str(entity_value))
                    if cpf_result['valid']:
                        normalized_entities[mapped_field] = cpf_result['formatted']
                        validation_scores.append(1.0)
                    else:
                        validation_errors.append(f"CPF inválido: {cpf_result['error']}")
                        validation_scores.append(0.0)
                
                elif entity_type in ['cep']:
                    cep_result = validate_brazilian_cep(str(entity_value))
                    if cep_result['valid']:
                        normalized_entities[mapped_field] = cep_result['formatted']
                        validation_scores.append(1.0)
                    else:
                        validation_errors.append(f"CEP inválido: {cep_result['error']}")
                        validation_scores.append(0.0)
                
                elif entity_type in ['consulta_date', 'data_consulta', 'appointment_date', 'data_agendamento']:
                    date_result = parse_relative_date(str(entity_value))
                    if date_result['valid']:
                        normalized_entities[mapped_field] = date_result['iso_date']
                        validation_scores.append(1.0)
                    else:
                        validation_errors.append(f"Data inválida: {date_result['error']}")
                        validation_scores.append(0.0)
                
                else:
                    # Para outros tipos de entidade, mantém o valor original
                    normalized_entities[mapped_field] = str(entity_value).strip()
                    validation_scores.append(0.7)  # Score moderado para entidades não validadas
                    
            except Exception as e:
                validation_errors.append(f"Erro na normalização da entidade {entity_type}: {str(e)}")
                validation_scores.append(0.0)
        
        # Calcula confidence score ajustado
        confidence_score = calculate_adjusted_confidence(
            normalized_entities,
            validation_scores,
            validation_errors
        )
        
        return {
            "normalized_entities": normalized_entities,
            "original_entities": original_entities,
            "domain": domain,
            "validation_errors": validation_errors,
            "confidence_score": confidence_score,
            "normalization_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro na normalização de entidades para domínio {domain}: {str(e)}")
        return {
            "normalized_entities": {},
            "original_entities": data,
            "domain": domain,
            "validation_errors": [f"Erro geral na normalização: {str(e)}"],
            "confidence_score": 0.0,
            "normalization_timestamp": datetime.now().isoformat()
        }


def calculate_adjusted_confidence(
    normalized_data: Dict[str, Any], 
    validation_scores: list, 
    validation_errors: list
) -> float:
    """
    Calcula confidence score ajustado baseado na qualidade pós-normalização.
    
    Args:
        normalized_data: Dados normalizados
        validation_scores: Lista de scores de validação (0.0-1.0)
        validation_errors: Lista de erros de validação
        
    Returns:
        Float entre 0.0 e 1.0 representando o confidence score ajustado
    """
    try:
        if not normalized_data:
            return 0.0
        
        # Score base da validação
        base_confidence = 0.0
        if validation_scores:
            base_confidence = sum(validation_scores) / len(validation_scores)
        
        # Penalização por erros
        error_penalty = min(len(validation_errors) * 0.1, 0.5)
        
        # Bônus por completude
        completeness_bonus = 0.0
        if len(normalized_data) >= 3:
            completeness_bonus = 0.1
        if len(normalized_data) >= 5:
            completeness_bonus = 0.2
        
        # Bônus por qualidade dos dados
        quality_bonus = 0.0
        if base_confidence >= 0.8:
            quality_bonus = 0.1
        if base_confidence >= 0.9:
            quality_bonus = 0.2
        
        # Calcula confidence final
        final_confidence = base_confidence - error_penalty + completeness_bonus + quality_bonus
        
        # Garante que está entre 0.0 e 1.0
        return max(0.0, min(1.0, final_confidence))
        
    except Exception as e:
        logger.error(f"Erro no cálculo do confidence score: {str(e)}")
        return 0.0


def get_normalization_summary(normalization_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gera resumo da normalização para análise e debug.
    
    Args:
        normalization_result: Resultado da normalização
        
    Returns:
        Dicionário com resumo da normalização
    """
    try:
        normalized_data = normalization_result.get("normalized_data", {})
        original_data = normalization_result.get("original_data", {})
        validation_errors = normalization_result.get("validation_errors", [])
        confidence_score = normalization_result.get("confidence_score", 0.0)
        
        return {
            "total_fields_original": len(original_data),
            "total_fields_normalized": len(normalized_data),
            "validation_errors_count": len(validation_errors),
            "confidence_score": confidence_score,
            "success_rate": len(normalized_data) / max(len(original_data), 1),
            "has_errors": len(validation_errors) > 0,
            "quality_level": "high" if confidence_score >= 0.8 else "medium" if confidence_score >= 0.5 else "low"
        }
        
    except Exception as e:
        logger.error(f"Erro na geração do resumo de normalização: {str(e)}")
        return {
            "error": f"Erro na geração do resumo: {str(e)}"
        } 