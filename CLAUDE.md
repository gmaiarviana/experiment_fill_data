# Claude Code Configuration

## Project: experiment_fill_data
Stack: Python + FastAPI + OpenAI + Docker

## Quick Commands
```bash
# Dev
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Test
python -m pytest tests/ -v

# Lint/Format
python -m flake8 src/
python -m black src/

# Docker
docker-compose up --build
docker-compose down

# Health check
curl http://localhost:8000/health
```

## Project Structure
- `src/api/` - FastAPI application
- `src/core/` - Core utilities (logging, OpenAI client)
- `tests/` - Test suite
- Key files: main.py, openai_client.py, logging.py

## Cursor + Claude Code Workflow

**Token Optimization:**
- Claude Code: análise/busca (`grep`, `find`) 
- Cursor: edição visual + AI completion
- Claude Code: validação (`tests`, `lint`)

**Commands for Efficiency:**
- `cursor .` - Open project in Cursor
- Use Cursor tasks: Ctrl+Shift+P > "Tasks: Run Task"
- Claude Code for file operations: `read src/api/main.py:25-50`

## Recent Context
- OpenAI chat integration implemented
- Structured JSON logging added
- Health check endpoint active
- Cursor integration configured