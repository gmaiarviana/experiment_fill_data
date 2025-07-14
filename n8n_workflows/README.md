# N8N Workflows - Context for Claude

## Working Commands for Claude to Use

### PowerShell-Compatible N8N API Commands

**IMPORTANTE**: PowerShell tem problemas com aspas aninhadas. Use sempre este padrão:

#### List Active Workflows
```bash
docker exec -it api python -c "
import requests
import json
headers = {
    'X-N8N-API-KEY': 'SUA_API_KEY_AQUI',
    'Content-Type': 'application/json'
}
url = 'http://n8n:5678/api/v1/workflows'
res = requests.get(url, headers=headers)
res.raise_for_status()
workflows = res.json()
print('=== WORKFLOWS DISPONIVEIS ===')
for w in workflows['data']:
    nome = w['name']
    wid = w['id']
    ativo = w['active']
    print('Nome:', nome, '| ID:', wid, '| Ativo:', ativo)
"
```

#### Get Workflow Details and Webhook URL
```bash
docker exec -it api python -c "
import requests
import json
headers = {
    'X-N8N-API-KEY': 'SUA_API_KEY_AQUI',
    'Content-Type': 'application/json'
}
url = 'http://n8n:5678/api/v1/workflows/WORKFLOW_ID_AQUI'
res = requests.get(url, headers=headers)
res.raise_for_status()
workflow = res.json()
print('=== WORKFLOW DETALHES ===')
print('Nome:', workflow['name'])
print('Nodes:')
webhook_url = None
for node in workflow['nodes']:
    print('  -', node['name'], '(' + node['type'] + ')')
    if 'webhook' in node['type'].lower():
        path = node['parameters'].get('path', 'N/A')
        webhook_url = 'http://localhost:5678/webhook/' + path
        print('    Webhook path:', path)
        print('    URL completa:', webhook_url)
"
```

#### Update Workflow (Safe Pattern)
```bash
docker exec -it api python -c "
import requests
import json
headers = {
    'X-N8N-API-KEY': 'SUA_API_KEY_AQUI',
    'Content-Type': 'application/json'
}
url = 'http://n8n:5678/api/v1/workflows/WORKFLOW_ID'
res = requests.get(url, headers=headers)
workflow = res.json()

# Fazer modificações no workflow aqui
# Exemplo: workflow['name'] = 'novo nome'

update_data = {
    'name': workflow['name'],
    'nodes': workflow['nodes'],
    'connections': workflow['connections'],
    'settings': workflow.get('settings', {'executionOrder': 'v1'})
}
res = requests.put(url, headers=headers, json=update_data)
res.raise_for_status()
print('Workflow atualizado com sucesso!')
"
```

#### Connect Nodes (Example: Chat Trigger to Extract Entities)
```bash
docker exec -it api python -c "
import requests
import json
headers = {
    'X-N8N-API-KEY': 'SUA_API_KEY_AQUI',
    'Content-Type': 'application/json'
}
url = 'http://n8n:5678/api/v1/workflows/WORKFLOW_ID'
res = requests.get(url, headers=headers)
workflow = res.json()

# Encontrar node de origem
source_node_id = None
for node in workflow['nodes']:
    if 'chatTrigger' in node['type']:
        source_node_id = node['id']
        break

if source_node_id:
    # Conectar ao node de destino
    workflow['connections'][source_node_id] = {
        'main': [
            [
                {
                    'node': 'Extract Entities',
                    'type': 'main',
                    'index': 0
                }
            ]
        ]
    }
    
    update_data = {
        'name': workflow['name'],
        'nodes': workflow['nodes'],
        'connections': workflow['connections'],
        'settings': workflow.get('settings', {})
    }
    res = requests.put(url, headers=headers, json=update_data)
    res.raise_for_status()
    print('Nodes conectados com sucesso!')
"
```

## Available Workflows

### Funcionalidade 3.1 - Entity Extraction Demo
- **Arquivo**: `entity_extraction_demo.json` 
- **Webhook URL**: `http://localhost:5678/webhook/extract-demo`
- **Chat Interface**: Disponível em `http://localhost:5678` quando workflow ativo
- **Funcionalidade**: Extração de entidades + chat conversacional
- **Nodes**: Webhook Input → Extract Entities + Chat Response → Respond Combined + Chat Trigger

### Legacy Workflows
- **chat_interface.json**: Complete chat workflow with webhook (funcionalidade 2.2)
- **chat_basic.json**: Basic manual trigger workflow (funcionalidade 2.1)

## Chat Trigger vs Webhook

### Webhook Interface
- **Acesso**: Via HTTP POST para URL específica
- **Uso**: Integração com sistemas externos, testes automatizados
- **Exemplo**: `POST http://localhost:5678/webhook/extract-demo`
- **Vantagem**: Programático, automatizável

### Chat Trigger Interface  
- **Acesso**: Interface visual no N8N (`http://localhost:5678`)
- **Uso**: Demonstrações, testes interativos, prototipagem
- **Vantagem**: Visual, conversacional, histórico de mensagens
- **Limitação**: Apenas para usuários com acesso ao N8N

## Troubleshooting PowerShell

### Problema: Aspas Aninhadas
❌ **Não Funciona:**
```bash
docker exec -it api python -c "print(f'ID: {w["id"]}')"  # Erro de sintaxe
```

✅ **Funciona:**
```bash
docker exec -it api python -c "print('ID:', w['id'])"    # Sem f-strings
```

### Problema: Comandos Truncados
❌ **Não Funciona:**
```bash
# Comandos muito longos são truncados pelo PowerShell
```

✅ **Funciona:**
```bash
# Quebrar em múltiplas linhas ou usar arquivos temporários
docker exec -it api bash -c 'cat > /tmp/script.py << EOF
# código aqui
EOF'
docker exec -it api python /tmp/script.py
```

## Working Docker Commands

```bash
# Check workflows
docker exec -it api python -c "from src.n8n.workflow_manager import WorkflowManager; import os; mgr = WorkflowManager(os.environ['N8N_API_KEY']); print(mgr.list_active_workflows())"

# Validate JSON
docker exec -it api python -c "from src.n8n.workflow_manager import WorkflowManager; import os; mgr = WorkflowManager(os.environ['N8N_API_KEY']); print(mgr.validate_workflow('n8n_workflows/chat_interface.json'))"
```

## PowerShell-Compatible N8N API Commands

**IMPORTANTE**: PowerShell tem problemas com aspas aninhadas. Use sempre este padrão:

### List Active Workflows
```bash
docker exec -it api python -c "
import requests
import json
headers = {
    'X-N8N-API-KEY': 'SUA_API_KEY_AQUI',
    'Content-Type': 'application/json'
}
url = 'http://n8n:5678/api/v1/workflows'
res = requests.get(url, headers=headers)
workflows = res.json()
for w in workflows['data']:
    print('Nome:', w['name'], '| ID:', w['id'], '| Ativo:', w['active'])
"

Update Workflow Response Body
bashdocker exec -it api python -c "
import requests
import json
headers = {
    'X-N8N-API-KEY': 'SUA_API_KEY_AQUI',
    'Content-Type': 'application/json'
}
url = 'http://n8n:5678/api/v1/workflows/WORKFLOW_ID'
res = requests.get(url, headers=headers)
workflow = res.json()

# Encontrar e modificar node específico
for node in workflow['nodes']:
    if node['name'] == 'Respond Combined':
        node['parameters']['responseBody'] = '={{ \$(\\'Extract Entities\\').first().json }}'
        break

update_data = {
    'name': workflow['name'],
    'nodes': workflow['nodes'],
    'connections': workflow['connections'],
    'settings': workflow.get('settings', {})
}
res = requests.put(url, headers=headers, json=update_data)
print('Workflow atualizado!')
"