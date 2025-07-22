"""
Testes específicos para Technical Debt #4 - TIME EXTRACTION FALHA CONSISTENTEMENTE

Este arquivo reproduz os casos identificados no TECHNICAL_DEBT.md onde o sistema
extrai datas mas ignora horários consistentemente.

Casos de teste baseados nos exemplos falhando:
- "Ana Lima 11987654321 proxima terca 15:30" → extrai data mas não horário 15:30
- "dia 15/08/2025 as 10h" → extrai data mas não horário 10h
"""
import pytest
from unittest.mock import Mock, AsyncMock
from src.core.entity_extraction import EntityExtractor
from src.core.openai_client import OpenAIClient


class TestTimeExtractionTD4:
    """
    Testa casos específicos de falha na extração de horários identificados no TD #4.
    """

    @pytest.fixture
    def mock_openai_client(self):
        """Mock do OpenAI client para testes controlados."""
        client = Mock(spec=OpenAIClient)
        client.extract_entities = AsyncMock()
        return client

    @pytest.fixture  
    def entity_extractor(self, mock_openai_client):
        """Instância do EntityExtractor com client mockado."""
        return EntityExtractor(openai_client=mock_openai_client)

    @pytest.mark.asyncio
    async def test_case_1_ana_lima_proxima_terca_1530(self, entity_extractor, mock_openai_client):
        """
        Testa caso: "Ana Lima 11987654321 proxima terca 15:30"
        Deve extrair: nome, telefone, data E horário 15:30
        """
        message = "Ana Lima 11987654321 proxima terca 15:30"
        
        # Mock da resposta do OpenAI
        mock_openai_client.extract_entities.return_value = {
            "success": True,
            "extracted_data": {
                "nome": "Ana Lima",
                "telefone": "11987654321",
                "data": "proxima terca",
                "horario": "15:30"  # OpenAI deveria extrair isso
            }
        }
        
        result = await entity_extractor.extract_consulta_entities(message)
        
        # Verifica se todos os dados foram extraídos
        assert result["success"] is True
        extracted = result["extracted_data"]
        
        assert "nome" in extracted or "name" in extracted, "Nome deve ser extraído"
        assert "telefone" in extracted or "phone" in extracted, "Telefone deve ser extraído"
        assert "data" in extracted or "consultation_date" in extracted, "Data deve ser extraída"
        
        # TESTE PRINCIPAL: horário deve estar presente após normalização
        assert "horario" in extracted or "consultation_time" in extracted, f"Horário 15:30 deve ser extraído e persistido. Dados atuais: {extracted}"
        
        # Se horário foi extraído, deve estar no formato correto
        horario = extracted.get("horario") or extracted.get("consultation_time")
        if horario:
            assert "15:30" in str(horario) or "15h30" in str(horario), f"Horário deve conter 15:30, obtido: {horario}"

    @pytest.mark.asyncio
    async def test_case_2_dia_15_08_2025_as_10h(self, entity_extractor, mock_openai_client):
        """
        Testa caso: "dia 15/08/2025 as 10h"
        Deve extrair: data 15/08/2025 E horário 10h
        """
        message = "dia 15/08/2025 as 10h"
        
        # Mock da resposta do OpenAI
        mock_openai_client.extract_entities.return_value = {
            "success": True,
            "extracted_data": {
                "data": "15/08/2025",
                "horario": "10h"  # OpenAI deveria extrair isso
            }
        }
        
        result = await entity_extractor.extract_consulta_entities(message)
        
        assert result["success"] is True
        extracted = result["extracted_data"]
        
        # Deve extrair a data
        assert "data" in extracted or "consultation_date" in extracted, "Data deve ser extraída"
        
        # TESTE PRINCIPAL: horário deve estar presente após normalização
        assert "horario" in extracted or "consultation_time" in extracted, f"Horário 10h deve ser extraído e persistido. Dados atuais: {extracted}"
        
        # Se horário foi extraído, deve estar no formato correto
        horario = extracted.get("horario") or extracted.get("consultation_time")
        if horario:
            assert "10" in str(horario), f"Horário deve conter 10, obtido: {horario}"

    @pytest.mark.asyncio
    async def test_case_3_combined_expressions_detection(self, entity_extractor, mock_openai_client):
        """
        Testa detecção de expressões temporais combinadas.
        """
        message = "Joao Silva amanha 14h"
        
        # Mock da resposta do OpenAI
        mock_openai_client.extract_entities.return_value = {
            "success": True,
            "extracted_data": {
                "nome": "Joao Silva", 
                "data": "amanha",
                "horario": "14h"
            }
        }
        
        result = await entity_extractor.extract_consulta_entities(message)
        
        # Verifica se método de detecção temporal está funcionando
        temporal_info = entity_extractor._detect_temporal_expressions(message)
        
        assert temporal_info["has_date_expression"] is True, "Deve detectar expressão de data 'amanha'"
        assert temporal_info["has_time_expression"] is True, "Deve detectar expressão de horário '14h'"
        
        # Verifica resultado final
        assert result["success"] is True
        extracted = result["extracted_data"]
        
        assert "horario" in extracted or "consultation_time" in extracted, f"Horário deve ser extraído. Dados: {extracted}"

    @pytest.mark.asyncio
    async def test_case_4_time_processing_debug(self, entity_extractor, mock_openai_client):
        """
        Testa processamento temporal detalhado para debug.
        """
        message = "Maria Santos 85999887766 hoje 16:45"
        
        mock_openai_client.extract_entities.return_value = {
            "success": True,
            "extracted_data": {
                "nome": "Maria Santos",
                "telefone": "85999887766", 
                "data": "hoje",
                "horario": "16:45"
            }
        }
        
        # Testa detecção temporal isoladamente
        temporal_info = entity_extractor._detect_temporal_expressions(message)
        print(f"DEBUG - Temporal info detectado: {temporal_info}")
        
        # Testa processamento temporal
        mock_data = {
            "nome": "Maria Santos",
            "telefone": "85999887766",
            "data": "hoje", 
            "horario": "16:45"
        }
        processed = entity_extractor._process_temporal_data(mock_data, message)
        print(f"DEBUG - Dados processados: {processed}")
        
        # Executa extração completa
        result = await entity_extractor.extract_consulta_entities(message)
        print(f"DEBUG - Resultado final: {result}")
        
        assert result["success"] is True
        extracted = result["extracted_data"]
        
        # Verifica se horário foi mantido através do pipeline
        assert "horario" in extracted or "consultation_time" in extracted, f"Horário deve ser mantido no pipeline. Dados: {extracted}"

    def test_temporal_patterns_recognition(self, entity_extractor):
        """
        Testa se padrões de horário estão sendo reconhecidos corretamente.
        """
        test_messages = [
            "15:30",
            "10h", 
            "14h30",
            "meio-dia",
            "tarde",
            "manhã"
        ]
        
        for message in test_messages:
            temporal_info = entity_extractor._detect_temporal_expressions(message)
            
            assert temporal_info["has_time_expression"] is True, f"Deve detectar expressão de tempo em '{message}'"
            assert temporal_info["time_expression"] != "", f"Deve capturar expressão de tempo em '{message}'"
            
            print(f"Padrão '{message}' detectado como: {temporal_info['time_expression']}")

    @pytest.mark.asyncio 
    async def test_schema_includes_horario_field(self, entity_extractor):
        """
        Verifica se o schema da função inclui campo horário corretamente.
        """
        schema = entity_extractor.consulta_schema
        
        # Verifica estrutura do schema
        assert "parameters" in schema
        assert "properties" in schema["parameters"]
        assert "horario" in schema["parameters"]["properties"]
        
        # Verifica descrição do campo horário
        horario_field = schema["parameters"]["properties"]["horario"]
        assert "type" in horario_field
        assert horario_field["type"] == "string"
        assert "description" in horario_field
        
        print(f"Schema do campo horário: {horario_field}")

    @pytest.mark.asyncio
    async def test_missing_fields_detection(self, entity_extractor, mock_openai_client):
        """
        Verifica se campos faltantes incluem horário quando não extraído.
        """
        message = "Ana Lima proxima segunda"  # Sem horário explícito
        
        mock_openai_client.extract_entities.return_value = {
            "success": True,
            "extracted_data": {
                "nome": "Ana Lima",
                "data": "proxima segunda"
                # horario ausente propositalmente
            }
        }
        
        result = await entity_extractor.extract_consulta_entities(message)
        
        # Deve identificar horário como campo faltante
        missing_fields = result.get("missing_fields", [])
        assert "horario" in missing_fields, f"Horário deve estar em campos faltantes: {missing_fields}"