# FOCO: List e Validate workflows
# Para updates: usar N8NClient diretamente ou comandos via Claude

"""
Gerenciador de Workflows N8N.

Este módulo fornece uma interface de alto nível para gerenciar workflows do N8N,
incluindo listagem e validação de workflows.
"""

import os
import json
from typing import Dict, List, Optional, Any
from src.n8n.n8n_client import N8NClient
from src.core.logging import setup_logging

logger = setup_logging()


class WorkflowManager:
    """
    Gerenciador de workflows do N8N.
    
    Fornece métodos para listagem e validação de workflows
    de forma simplificada.
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa o gerenciador de workflows.
        
        Args:
            api_key: Chave de API do N8N
        """
        self.client = N8NClient(api_key)
        logger.info("WorkflowManager inicializado")
    
    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """
        Lista todos os workflows ativos.
        
        Returns:
            Lista de workflows ativos
        """
        try:
            logger.info("Listando workflows ativos")
            workflows = self.client.list_workflows()
            active_workflows = [wf for wf in workflows if wf.get('active', False)]
            
            result = []
            for workflow in active_workflows:
                workflow_info = {
                    'id': workflow.get('id'),
                    'name': workflow.get('name'),
                    'active': workflow.get('active', False),
                    'created_at': workflow.get('createdAt'),
                    'updated_at': workflow.get('updatedAt')
                }
                result.append(workflow_info)
            
            logger.info(f"Encontrados {len(result)} workflows ativos")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao listar workflows ativos: {str(e)}")
            raise
    
    def validate_workflow(self, json_path: str) -> Dict[str, Any]:
        """
        Valida se um arquivo JSON de workflow é válido.
        
        Args:
            json_path: Caminho para o arquivo JSON do workflow
            
        Returns:
            Dicionário com resultado da validação
        """
        try:
            logger.info(f"Validando workflow: {json_path}")
            
            # Verifica se o arquivo existe
            if not os.path.exists(json_path):
                return {
                    'valid': False,
                    'error': f'Arquivo não encontrado: {json_path}'
                }
            
            # Tenta fazer parse do JSON
            with open(json_path, 'r', encoding='utf-8') as file:
                workflow_data = json.load(file)
            
            # Validações básicas
            validation_result = {
                'valid': True,
                'workflow_name': workflow_data.get('name', 'Unnamed Workflow'),
                'nodes_count': len(workflow_data.get('nodes', [])),
                'connections_count': len(workflow_data.get('connections', {})),
                'has_webhook': self._has_webhook_node(workflow_data),
                'webhook_url': self._extract_webhook_url(workflow_data) if self._has_webhook_node(workflow_data) else None
            }
            
            logger.info(f"Workflow validado com sucesso: {validation_result}")
            return validation_result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON inválido em {json_path}: {str(e)}")
            return {
                'valid': False,
                'error': f'JSON inválido: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Erro ao validar workflow {json_path}: {str(e)}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _has_webhook_node(self, workflow_data: Dict) -> bool:
        """
        Verifica se o workflow tem um nó webhook.
        
        Args:
            workflow_data: Dados do workflow
            
        Returns:
            True se tem nó webhook, False caso contrário
        """
        nodes = workflow_data.get('nodes', [])
        for node in nodes:
            node_type = node.get('type', '')
            if 'webhook' in node_type.lower():
                return True
        return False
    
    def _extract_webhook_url(self, workflow_data: Dict) -> Optional[str]:
        """
        Extrai a URL do webhook do workflow.
        
        Args:
            workflow_data: Dados do workflow
            
        Returns:
            URL do webhook ou None se não encontrado
        """
        nodes = workflow_data.get('nodes', [])
        for node in nodes:
            node_type = node.get('type', '')
            if 'webhook' in node_type.lower():
                # Tenta extrair a URL do webhook dos parâmetros do nó
                parameters = node.get('parameters', {})
                webhook_url = parameters.get('httpMethod') or parameters.get('path') or parameters.get('url')
                if webhook_url:
                    return webhook_url
        return None 