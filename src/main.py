import asyncio
import json
import sys
from typing import Optional
from src.core.entity_extraction import EntityExtractor
from src.core.data_normalizer import normalize_consulta_data


async def extract_command(text: str) -> None:
    """
    Comando CLI para extrair entidades de texto natural.
    
    Args:
        text (str): Texto em linguagem natural para extração
    """
    extractor = EntityExtractor()
    
    print(f"📝 Extraindo entidades de: {text}")
    print("🔄 Processando...")
    
    try:
        result = await extractor.extract_consulta_entities(text)
        
        if result["success"]:
            print("✅ Extração bem-sucedida!")
            print(f"📊 Confidence Score: {result['confidence_score']}")
            print(f"📋 Dados Extraídos:")
            print(json.dumps(result["extracted_data"], indent=2, ensure_ascii=False))
            
            if result["missing_fields"]:
                print(f"❓ Campos faltantes: {', '.join(result['missing_fields'])}")
                if result.get("suggested_questions"):
                    print("💡 Perguntas sugeridas:")
                    for i, question in enumerate(result["suggested_questions"], 1):
                        print(f"   {i}. {question}")
            else:
                print("✅ Todos os campos foram preenchidos!")
        else:
            print("❌ Erro na extração:")
            print(f"   {result['error']}")
            if "raw_response" in result:
                print(f"   Resposta bruta: {result['raw_response']}")
                
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")


def validate_command(json_data: str) -> None:
    """
    Comando CLI para validar e normalizar dados JSON.
    
    Args:
        json_data (str): Dados JSON como string para validação
    """
    print(f"🔍 Validando dados: {json_data}")
    print("🔄 Processando...")
    
    try:
        # Parse JSON
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            print(f"❌ Erro: JSON inválido - {str(e)}")
            return
        
        # Check if data is empty
        if not data:
            print("❌ Erro: Dados vazios")
            return
        
        # Validate and normalize data
        result = normalize_consulta_data(data)
        
        # Display results
        print("\n" + "="*50)
        print("📋 RESULTADO DA VALIDAÇÃO")
        print("="*50)
        
        # Original data
        print(f"📥 Dados Originais:")
        print(json.dumps(result.get("original_data", {}), indent=2, ensure_ascii=False))
        
        # Normalized data
        print(f"\n📤 Dados Normalizados:")
        print(json.dumps(result.get("normalized_data", {}), indent=2, ensure_ascii=False))
        
        # Confidence score
        confidence = result.get("confidence_score", 0.0)
        print(f"\n📊 Confidence Score: {confidence:.2f}")
        
        # Validation errors
        errors = result.get("validation_errors", [])
        if errors:
            print(f"\n❌ Erros de Validação:")
            for i, error in enumerate(errors, 1):
                print(f"   {i}. {error}")
        else:
            print(f"\n✅ Nenhum erro de validação encontrado!")
        
        # Success summary
        if confidence > 0.0 and not errors:
            print(f"\n🎉 Validação bem-sucedida!")
        else:
            print(f"\n⚠️  Validação com problemas detectados")
        
        print("="*50)
        
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")


def print_help():
    """Exibe ajuda dos comandos disponíveis."""
    print("🎯 Data Structuring Agent - CLI Tools")
    print("")
    print("Comandos disponíveis:")
    print("  extract <texto>  - Extrai entidades de texto natural")
    print("  validate <json>  - Valida e normaliza dados JSON")
    print("")
    print("Exemplos:")
    print('  python -m src.main extract "Quero agendar consulta para João Silva"')
    print('  python -m src.main extract "João quer consulta amanhã às 14h, telefone 11999887766"')
    print('  python -m src.main validate \'{"nome": "joao", "telefone": "11999887766"}\'')
    print('  python -m src.main validate \'{"nome": "Maria Silva", "email": "maria@email.com", "data": "amanhã"}\'')


async def main():
    """Função principal do CLI."""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "extract":
        if len(sys.argv) < 3:
            print("❌ Erro: Texto para extração é obrigatório")
            print('Uso: python -m src.main extract "seu texto aqui"')
            return
        
        text = " ".join(sys.argv[2:])
        await extract_command(text)
    
    elif command == "validate":
        if len(sys.argv) < 3:
            print("❌ Erro: Dados JSON para validação são obrigatórios")
            print('Uso: python -m src.main validate \'{"campo": "valor"}\'')
            return
        
        json_data = " ".join(sys.argv[2:])
        validate_command(json_data)
    
    elif command in ["help", "-h", "--help"]:
        print_help()
    
    else:
        print(f"❌ Comando desconhecido: {command}")
        print_help()


if __name__ == "__main__":
    asyncio.run(main())