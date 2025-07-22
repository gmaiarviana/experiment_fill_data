"""
Mapeador de campos para padronização de nomenclatura.

Centraliza o mapeamento entre nomes de campos em português/inglês
e diferentes convenções de nomenclatura usadas no sistema.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class FieldMapping:
    """
    Configuração de mapeamento de um campo.
    
    Attributes:
        source_field: Nome do campo de origem
        target_field: Nome do campo de destino
        aliases: Lista de nomes alternativos aceitos
        required: Se o campo é obrigatório
        description: Descrição do campo
    """
    source_field: str
    target_field: str
    aliases: List[str] = None
    required: bool = False
    description: str = ""
    
    def __post_init__(self):
        """Inicializa aliases como lista vazia se None."""
        if self.aliases is None:
            self.aliases = []


class FieldMapper:
    """
    Gerenciador de mapeamento de campos.
    
    Centraliza a conversão entre diferentes convenções de nomenclatura
    usadas no sistema, especialmente entre português e inglês.
    """
    
    def __init__(self):
        """Inicializa o mapeador com configurações padrão."""
        self._mappings: Dict[str, FieldMapping] = {}
        self._reverse_mappings: Dict[str, str] = {}
        self._setup_default_mappings()
    
    def register_mapping(self, mapping: FieldMapping) -> None:
        """
        Registra um novo mapeamento de campo.
        
        Args:
            mapping: Configuração do mapeamento
        """
        # Registra mapeamento principal
        self._mappings[mapping.source_field] = mapping
        self._reverse_mappings[mapping.target_field] = mapping.source_field
        
        # Registra aliases
        for alias in mapping.aliases:
            self._mappings[alias] = mapping
    
    def map_field_name(self, source_field: str) -> Optional[str]:
        """
        Mapeia nome de campo de origem para destino.
        
        Args:
            source_field: Nome do campo de origem
            
        Returns:
            Nome do campo de destino ou None se não mapeado
        """
        mapping = self._mappings.get(source_field.lower())
        return mapping.target_field if mapping else None
    
    def reverse_map_field_name(self, target_field: str) -> Optional[str]:
        """
        Mapeia nome de campo de destino para origem.
        
        Args:
            target_field: Nome do campo de destino
            
        Returns:
            Nome do campo de origem ou None se não mapeado
        """
        return self._reverse_mappings.get(target_field)
    
    def map_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mapeia todos os campos de um dicionário de dados.
        
        Args:
            data: Dicionário com dados de origem
            
        Returns:
            Dicionário com campos mapeados
        """
        if not data:
            return {}
        
        mapped_data = {}
        unmapped_fields = []
        
        for source_field, value in data.items():
            target_field = self.map_field_name(source_field)
            
            if target_field:
                mapped_data[target_field] = value
            else:
                # Mantém campo não mapeado com nome original
                mapped_data[source_field] = value
                unmapped_fields.append(source_field)
        
        # Adiciona metadados sobre campos não mapeados
        if unmapped_fields:
            mapped_data["_unmapped_fields"] = unmapped_fields
        
        return mapped_data
    
    def reverse_map_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mapeia dados de volta para nomenclatura original.
        
        Args:
            data: Dicionário com dados mapeados
            
        Returns:
            Dicionário com nomenclatura original
        """
        if not data:
            return {}
        
        reverse_mapped = {}
        
        for target_field, value in data.items():
            # Ignora metadados
            if target_field.startswith("_"):
                continue
                
            source_field = self.reverse_map_field_name(target_field)
            
            if source_field:
                reverse_mapped[source_field] = value
            else:
                # Mantém campo não mapeado
                reverse_mapped[target_field] = value
        
        return reverse_mapped
    
    def get_required_fields(self) -> List[str]:
        """
        Retorna lista de campos obrigatórios (nomes de destino).
        
        Returns:
            Lista de nomes de campos obrigatórios
        """
        required_fields = []
        processed_targets = set()
        
        for mapping in self._mappings.values():
            if mapping.required and mapping.target_field not in processed_targets:
                required_fields.append(mapping.target_field)
                processed_targets.add(mapping.target_field)
        
        return required_fields
    
    def get_field_aliases(self, target_field: str) -> List[str]:
        """
        Retorna todos os aliases para um campo de destino.
        
        Args:
            target_field: Nome do campo de destino
            
        Returns:
            Lista de aliases aceitos para o campo
        """
        aliases = []
        
        for source_field, mapping in self._mappings.items():
            if mapping.target_field == target_field:
                aliases.append(source_field)
        
        return aliases
    
    def validate_field_names(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Valida nomes de campos em dados de entrada.
        
        Args:
            data: Dicionário com dados a serem validados
            
        Returns:
            Dicionário com listas de campos por categoria:
            - mapped: campos reconhecidos e mapeados
            - unmapped: campos não reconhecidos
            - missing_required: campos obrigatórios ausentes
        """
        result = {
            "mapped": [],
            "unmapped": [],
            "missing_required": []
        }
        
        if not data:
            result["missing_required"] = self.get_required_fields()
            return result
        
        # Analisa campos presentes
        for field_name in data.keys():
            if self.map_field_name(field_name):
                result["mapped"].append(field_name)
            else:
                result["unmapped"].append(field_name)
        
        # Verifica campos obrigatórios
        mapped_data = self.map_data(data)
        required_fields = self.get_required_fields()
        
        for required_field in required_fields:
            if required_field not in mapped_data or not mapped_data[required_field]:
                result["missing_required"].append(required_field)
        
        return result
    
    def get_mapping_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna informações completas sobre mapeamentos registrados.
        
        Returns:
            Dicionário com informações dos mapeamentos
        """
        info = {}
        processed_targets = set()
        
        for mapping in self._mappings.values():
            if mapping.target_field not in processed_targets:
                info[mapping.target_field] = {
                    "source_field": mapping.source_field,
                    "aliases": mapping.aliases,
                    "required": mapping.required,
                    "description": mapping.description,
                    "all_accepted_names": self.get_field_aliases(mapping.target_field)
                }
                processed_targets.add(mapping.target_field)
        
        return info
    
    def _setup_default_mappings(self) -> None:
        """Configura mapeamentos padrão do sistema."""
        
        # Mapeamentos para consulta médica
        default_mappings = [
            FieldMapping(
                source_field="nome",
                target_field="name",
                aliases=["nome_completo", "nome_paciente", "paciente"],
                required=True,
                description="Nome completo do paciente"
            ),
            FieldMapping(
                source_field="telefone",
                target_field="phone",
                aliases=["tel", "celular", "fone", "telefone_contato"],
                required=True,
                description="Número de telefone para contato"
            ),
            FieldMapping(
                source_field="data",
                target_field="consultation_date",
                aliases=["data_consulta", "data_agendamento", "quando"],
                required=True,
                description="Data da consulta médica"
            ),
            FieldMapping(
                source_field="horario",
                target_field="consultation_time",
                aliases=["hora", "horario_consulta", "que_horas"],
                required=False,
                description="Horário da consulta"
            ),
            FieldMapping(
                source_field="email",
                target_field="email",
                aliases=["e-mail", "email_contato"],
                required=False,
                description="Email para contato"
            ),
            FieldMapping(
                source_field="cpf",
                target_field="cpf",
                aliases=["documento", "cpf_paciente"],
                required=False,
                description="CPF do paciente"
            ),
            FieldMapping(
                source_field="cep",
                target_field="postal_code",
                aliases=["codigo_postal", "cep_residencia"],
                required=False,
                description="CEP do endereço"
            ),
            FieldMapping(
                source_field="tipo_consulta",
                target_field="consultation_type",
                aliases=["tipo", "especialidade", "motivo_consulta"],
                required=False,
                description="Tipo ou especialidade da consulta"
            ),
            FieldMapping(
                source_field="observacoes",
                target_field="notes",
                aliases=["obs", "comentarios", "detalhes"],
                required=False,
                description="Observações adicionais"
            )
        ]
        
        # Registra todos os mapeamentos padrão
        for mapping in default_mappings:
            self.register_mapping(mapping)