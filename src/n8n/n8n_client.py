"""
Cliente N8N para interação com a API REST do N8N.

Este módulo fornece uma classe cliente para gerenciar workflows do N8N
programaticamente através da API REST.
"""

import json
import requests
from typing import Dict, List, Optional, Any
from src.core.logging import setup_logging

logger = setup_logging()


class N8NClient:
    """
    Cliente para interação com a API REST do N8N.
    
    Permite gerenciar workflows do N8N programaticamente através de
    operações CRUD e controle de ativação/desativação.
    """
    
    def __init__(self, api_key: str, base_url: str = "http://n8n:5678/api/v1"):
        """
        Inicializa o cliente N8N.
        
        Args:
            api_key: Chave de API do N8N
            base_url: URL base da API do N8N (padrão: localhost:5678)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "X-N8N-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        logger.info(f"N8NClient inicializado com base_url: {self.base_url}")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Faz uma requisição HTTP para a API do N8N.
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API
            data: Dados para enviar (opcional)
            
        Returns:
            Resposta da API como dicionário
            
        Raises:
            requests.RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.debug(f"Fazendo requisição {method} para {url}")
            
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            response.raise_for_status()
            
            # Tenta fazer parse do JSON, retorna string vazia se não for JSON
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"message": response.text}
                
        except requests.RequestException as e:
            logger.error(f"Erro na requisição {method} para {url}: {str(e)}")
            raise
    
    def list_workflows(self) -> List[Dict]:
        """
        Lista todos os workflows disponíveis.
        
        Returns:
            Lista de workflows
        """
        try:
            logger.info("Listando workflows")
            response = self._make_request("GET", "workflows")
            workflows = response.get("data", [])
            logger.info(f"Encontrados {len(workflows)} workflows")
            return workflows
        except Exception as e:
            logger.error(f"Erro ao listar workflows: {str(e)}")
            raise
    
    def get_workflow(self, workflow_id: str) -> Dict:
        """
        Obtém um workflow específico pelo ID.
        
        Args:
            workflow_id: ID do workflow
            
        Returns:
            Dados do workflow
        """
        try:
            logger.info(f"Obtendo workflow {workflow_id}")
            response = self._make_request("GET", f"workflows/{workflow_id}")
            logger.info(f"Workflow {workflow_id} obtido com sucesso")
            return response
        except Exception as e:
            logger.error(f"Erro ao obter workflow {workflow_id}: {str(e)}")
            raise
    
    def create_workflow(self, workflow_data: Dict) -> Dict:
        """
        Cria um novo workflow.
        
        Args:
            workflow_data: Dados do workflow a ser criado
            
        Returns:
            Dados do workflow criado
        """
        try:
            logger.info("Criando novo workflow")
            response = self._make_request("POST", "workflows", workflow_data)
            workflow_id = response.get("id")
            logger.info(f"Workflow criado com ID: {workflow_id}")
            return response
        except Exception as e:
            logger.error(f"Erro ao criar workflow: {str(e)}")
            raise
    
    def update_workflow(self, workflow_id: str, workflow_data: Dict) -> Dict:
        """
        Atualiza um workflow existente.
        
        Args:
            workflow_id: ID do workflow
            workflow_data: Novos dados do workflow
            
        Returns:
            Dados do workflow atualizado
        """
        try:
            logger.info(f"Atualizando workflow {workflow_id}")
            response = self._make_request("PUT", f"workflows/{workflow_id}", workflow_data)
            logger.info(f"Workflow {workflow_id} atualizado com sucesso")
            return response
        except Exception as e:
            logger.error(f"Erro ao atualizar workflow {workflow_id}: {str(e)}")
            raise
    
    def delete_workflow(self, workflow_id: str) -> Dict:
        """
        Remove um workflow.
        
        Args:
            workflow_id: ID do workflow a ser removido
            
        Returns:
            Confirmação da remoção
        """
        try:
            logger.info(f"Removendo workflow {workflow_id}")
            response = self._make_request("DELETE", f"workflows/{workflow_id}")
            logger.info(f"Workflow {workflow_id} removido com sucesso")
            return response
        except Exception as e:
            logger.error(f"Erro ao remover workflow {workflow_id}: {str(e)}")
            raise
    
    def activate_workflow(self, workflow_id: str) -> Dict:
        """
        Ativa um workflow.
        
        Args:
            workflow_id: ID do workflow a ser ativado
            
        Returns:
            Confirmação da ativação
        """
        try:
            logger.info(f"Ativando workflow {workflow_id}")
            response = self._make_request("POST", f"workflows/{workflow_id}/activate")
            logger.info(f"Workflow {workflow_id} ativado com sucesso")
            return response
        except Exception as e:
            logger.error(f"Erro ao ativar workflow {workflow_id}: {str(e)}")
            raise
    
    def deactivate_workflow(self, workflow_id: str) -> Dict:
        """
        Desativa um workflow.
        
        Args:
            workflow_id: ID do workflow a ser desativado
            
        Returns:
            Confirmação da desativação
        """
        try:
            logger.info(f"Desativando workflow {workflow_id}")
            response = self._make_request("POST", f"workflows/{workflow_id}/deactivate")
            logger.info(f"Workflow {workflow_id} desativado com sucesso")
            return response
        except Exception as e:
            logger.error(f"Erro ao desativar workflow {workflow_id}: {str(e)}")
            raise
    
    def import_workflow_from_file(self, json_path: str) -> Dict:
        """
        Importa um workflow a partir de um arquivo JSON.
        
        Args:
            json_path: Caminho para o arquivo JSON do workflow
            
        Returns:
            Dados do workflow importado
        """
        try:
            logger.info(f"Importando workflow do arquivo: {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as file:
                workflow_data = json.load(file)
            
            # Cria o workflow usando os dados do arquivo
            response = self.create_workflow(workflow_data)
            logger.info(f"Workflow importado com sucesso do arquivo {json_path}")
            return response
            
        except FileNotFoundError:
            logger.error(f"Arquivo não encontrado: {json_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao fazer parse do JSON em {json_path}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erro ao importar workflow do arquivo {json_path}: {str(e)}")
            raise 