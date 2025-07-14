import asyncio
import json
import sys
from typing import Optional
from src.core.entity_extraction import EntityExtractor


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


def print_help():
    """Exibe ajuda dos comandos disponíveis."""
    print("🎯 Data Structuring Agent - Entity Extraction")
    print("")
    print("Comandos disponíveis:")
    print("  extract <texto>  - Extrai entidades de texto natural")
    print("")
    print("Exemplos:")
    print('  python -m src.main extract "Quero agendar consulta para João Silva"')
    print('  python -m src.main extract "João quer consulta amanhã às 14h, telefone 11999887766"')


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
    
    elif command in ["help", "-h", "--help"]:
        print_help()
    
    else:
        print(f"❌ Comando desconhecido: {command}")
        print_help()


if __name__ == "__main__":
    asyncio.run(main())