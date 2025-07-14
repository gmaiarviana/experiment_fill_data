# N8N Workflows - Context for Claude

## Working Commands for Claude to Use

### List Active Workflows
```python
from src.n8n.n8n_client import N8NClient
import os
client = N8NClient(os.environ['N8N_API_KEY'])
workflows = client.list_workflows()
for w in workflows:
    print(f"- {w['name']} (ID: {w['id'][:8]}..., Active: {w['active']})")
```

### Update Workflow Directly
```python
# Get existing workflow
workflow = client.get_workflow('WORKFLOW_ID')

# Modify workflow (nodes, connections, etc.)
# ... modifications ...

# Update via PUT
import requests
headers = {'X-N8N-API-KEY': os.environ['N8N_API_KEY'], 'Content-Type': 'application/json'}
response = requests.put(f'http://n8n:5678/api/v1/workflows/{workflow_id}', 
                       headers=headers, json=update_data)
```

## Available Workflows

- **chat_interface.json**: Complete chat workflow with webhook
- **chat_basic.json**: Basic manual trigger workflow

## Working Docker Commands

```bash
# Check workflows
docker exec -it api python -c "from src.n8n.workflow_manager import WorkflowManager; import os; mgr = WorkflowManager(os.environ['N8N_API_KEY']); print(mgr.list_active_workflows())"

# Validate JSON
docker exec -it api python -c "from src.n8n.workflow_manager import WorkflowManager; import os; mgr = WorkflowManager(os.environ['N8N_API_KEY']); print(mgr.validate_workflow('n8n_workflows/chat_interface.json'))"
``` 