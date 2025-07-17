from typing import Dict, Any, List
from loguru import logger


class DataSummarizer:
    """
    Sumarizador de dados para criar resumos contextuais e informativos.
    """
    
    def __init__(self):
        """
        Inicializa o sumarizador de dados.
        """
        # Mapeamento de campos para nomes de exibição
        self.field_display_names = {
            "nome": "nome",
            "telefone": "telefone", 
            "data": "data do agendamento",
            "horario": "horário",
            "tipo_consulta": "tipo de consulta",
            "observacoes": "observações"
        }
        
        logger.info("DataSummarizer inicializado")
    
    def summarize_extracted_data(self, data: Dict[str, Any]) -> str:
        """
        Cria um resumo legível dos dados extraídos.
        
        Args:
            data: Dados extraídos para resumir
            
        Returns:
            Resumo formatado dos dados
        """
        if not data:
            return "nenhuma informação"
        
        summary_parts = []
        
        # Adiciona cada campo com valor
        for field, value in data.items():
            if value:  # Só inclui campos com valor
                display_name = self.field_display_names.get(field, field)
                summary_parts.append(f"{display_name}: {value}")
        
        if summary_parts:
            return ", ".join(summary_parts)
        else:
            return "nenhuma informação"
    
    def get_missing_fields(self, data: Dict[str, Any], required_fields: List[str] = None) -> List[str]:
        """
        Identifica campos que ainda precisam ser preenchidos.
        
        Args:
            data: Dados já extraídos
            required_fields: Lista de campos obrigatórios (opcional)
            
        Returns:
            Lista de campos faltantes
        """
        if required_fields is None:
            required_fields = ["nome", "telefone", "data", "horario"]
        
        missing_fields = []
        
        for field in required_fields:
            if not data.get(field):
                missing_fields.append(field)
        
        return missing_fields
    
    def format_missing_fields_for_display(self, missing_fields: List[str]) -> str:
        """
        Formata campos faltantes para exibição amigável.
        
        Args:
            missing_fields: Lista de campos faltantes
            
        Returns:
            Texto formatado dos campos faltantes
        """
        if not missing_fields:
            return "todos os dados necessários"
        
        display_names = []
        for field in missing_fields:
            display_name = self.field_display_names.get(field, field)
            display_names.append(display_name)
        
        if len(display_names) == 1:
            return display_names[0]
        elif len(display_names) == 2:
            return f"{display_names[0]} e {display_names[1]}"
        else:
            return f"{', '.join(display_names[:-1])} e {display_names[-1]}"
    
    def is_data_complete(self, data: Dict[str, Any], required_fields: List[str] = None) -> bool:
        """
        Verifica se os dados estão completos.
        
        Args:
            data: Dados para verificar
            required_fields: Lista de campos obrigatórios (opcional)
            
        Returns:
            True se os dados estão completos
        """
        missing_fields = self.get_missing_fields(data, required_fields)
        return len(missing_fields) == 0
    
    def get_data_completeness_percentage(self, data: Dict[str, Any], required_fields: List[str] = None) -> float:
        """
        Calcula a porcentagem de completude dos dados.
        
        Args:
            data: Dados para calcular
            required_fields: Lista de campos obrigatórios (opcional)
            
        Returns:
            Porcentagem de completude (0.0 a 1.0)
        """
        if required_fields is None:
            required_fields = ["nome", "telefone", "data", "horario"]
        
        filled_fields = sum(1 for field in required_fields if data.get(field))
        total_fields = len(required_fields)
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
    
    def get_field_display_name(self, field: str) -> str:
        """
        Obtém o nome de exibição para um campo.
        
        Args:
            field: Nome do campo
            
        Returns:
            Nome de exibição do campo
        """
        return self.field_display_names.get(field, field)
    
    def format_validation_errors(self, errors: List[str]) -> str:
        """
        Formata erros de validação para exibição.
        
        Args:
            errors: Lista de erros de validação
            
        Returns:
            Texto formatado dos erros
        """
        if not errors:
            return ""
        
        if len(errors) == 1:
            return f"Erro: {errors[0]}"
        else:
            return f"Erros: {', '.join(errors)}"
    
    def create_progress_summary(self, data: Dict[str, Any], missing_fields: List[str]) -> str:
        """
        Cria um resumo do progresso da coleta de dados.
        
        Args:
            data: Dados já coletados
            missing_fields: Campos que ainda faltam
            
        Returns:
            Resumo do progresso
        """
        total_required = len(self.get_missing_fields({}, ["nome", "telefone", "data", "horario"]))
        collected = total_required - len(missing_fields)
        
        if collected == 0:
            return "Ainda não temos nenhuma informação"
        elif collected == total_required:
            return "Temos todas as informações necessárias"
        else:
            return f"Já temos {collected} de {total_required} informações" 