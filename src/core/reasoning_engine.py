from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from src.core.entity_extraction import EntityExtractor
from src.core.data_normalizer import normalize_consulta_data
from src.core.question_generator import QuestionGenerator
from src.core.data_summarizer import DataSummarizer
from src.core.conversation_manager import ConversationManager
import random


class ReasoningEngine:
    """
    Motor de raciocínio que implementa o loop Think → Extract → Validate → Act
    para processamento inteligente de mensagens conversacionais.
    """
    
    def __init__(self):
        """
        Inicializa o motor de raciocínio com os componentes modulares.
        """
        self.entity_extractor = EntityExtractor()
        self.question_generator = QuestionGenerator()
        self.data_summarizer = DataSummarizer()
        self.conversation_manager = ConversationManager()
        
        logger.info("ReasoningEngine inicializado com componentes modulares")
    
    def _get_response_template(self, template_type: str, **kwargs) -> str:
        """
        Gera uma resposta usando templates para tornar o diálogo mais natural.
        
        Args:
            template_type (str): Tipo de template a usar
            **kwargs: Parâmetros para formatar o template
            
        Returns:
            str: Resposta formatada
        """
        return self.question_generator.generate_contextual_question(template_type, **kwargs)
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Processa uma mensagem através do loop Think → Extract → Validate → Act.
        
        Args:
            message (str): Mensagem do usuário para processar
            context (Dict[str, Any], optional): Contexto da sessão de conversa
            
        Returns:
            Dict: Resultado do processamento com ação, resposta e dados
        """
        try:
            logger.info(f"Iniciando processamento da mensagem: '{message[:50]}...'")
            
            # Inicializa contexto se não fornecido
            if context is None:
                context = self.conversation_manager.initialize_context()
            
            # THINK: Analisa mensagem e decide próximo passo
            think_result = await self._think(message, context)
            logger.debug(f"THINK: {think_result}")
            
            if think_result["action"] == "error":
                return self._create_error_response("Erro na análise da mensagem", think_result.get("error"))
            
            # EXTRACT: Extrai dados se necessário
            extract_result = None
            if think_result["action"] in ["extract", "extract_and_ask"]:
                extract_result = await self._extract(message, context)
                logger.debug(f"EXTRACT: {extract_result}")
                
                if extract_result["action"] == "error":
                    return self._create_error_response("Erro na extração de dados", extract_result.get("error"))
            
            # VALIDATE: Valida dados extraídos
            validate_result = None
            if extract_result and extract_result.get("extracted_data"):
                validate_result = await self._validate(extract_result["extracted_data"], context)
                logger.debug(f"VALIDATE: {validate_result}")
                
                if validate_result["action"] == "error":
                    return self._create_error_response("Erro na validação de dados", validate_result.get("error"))
            
            # ACT: Decide resposta final
            act_result = await self._act(think_result, extract_result, validate_result, context)
            logger.debug(f"ACT: {act_result}")
            
            # Atualiza contexto com dados extraídos e nova ação
            extracted_data = extract_result.get("extracted_data", {}) if extract_result else {}
            action = act_result["action"]
            response = act_result.get("response", "")
            confidence = act_result.get("confidence", 0.0)
            
            # Atualiza contexto usando ConversationManager
            context = self.conversation_manager.update_context(
                context, 
                extracted_data, 
                action, 
                response
            )
            
            # Atualiza confidence tracking
            context["total_confidence"] += confidence
            context["confidence_count"] += 1
            context["average_confidence"] = context["total_confidence"] / context["confidence_count"]
            
            # Adiciona mensagem ao histórico usando ConversationManager
            self.conversation_manager.add_to_history(
                context, 
                message, 
                action, 
                response, 
                confidence
            )
            
            logger.info(f"Processamento concluído. Ação: {act_result['action']}, Confidence: {confidence:.2f}")
            return act_result
            
        except Exception as e:
            logger.error(f"Erro no processamento da mensagem: {str(e)}")
            return self._create_error_response("Erro interno no processamento", str(e))
    
    async def _think(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        THINK: Analisa a mensagem e decide o próximo passo baseado no contexto e histórico.
        Usa ConversationManager para evitar loops e repetições.
        
        Args:
            message (str): Mensagem para analisar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da análise com ação decidida
        """
        try:
            logger.debug("Executando THINK...")
            
            # Análise baseada em palavras-chave, contexto e histórico
            message_lower = message.lower()
            existing_data = context.get("extracted_data", {})
            
            # Verifica se é uma confirmação (considera contexto)
            confirmation_words = ["sim", "confirmo", "correto", "certo", "ok", "perfeito", "confirma"]
            if any(word in message_lower for word in confirmation_words):
                # Se tem dados suficientes, confirma
                if self.data_summarizer.is_data_complete(existing_data):
                    return {
                        "action": "complete",
                        "reason": "Confirmação com dados completos",
                        "response": self.question_generator.generate_contextual_question("complete"),
                        "confidence": 0.95
                    }
                else:
                    return {
                        "action": "confirm",
                        "reason": "Confirmação com dados incompletos",
                        "response": "Tenho algumas informações, mas preciso completar. Posso confirmar o que tenho?",
                        "confidence": 0.8
                    }
            
            # Verifica se é uma negação/correção (considera histórico)
            negation_words = ["não", "não é", "errado", "incorreto", "mudar", "corrigir", "não é isso"]
            if any(word in message_lower for word in negation_words):
                return {
                    "action": "extract",
                    "reason": "Correção - nova extração",
                    "confidence": 0.7
                }
            
            # Verifica se é uma resposta específica a uma pergunta anterior
            conversation_history = context.get("conversation_history", [])
            if conversation_history and conversation_history[-1].get("action") == "ask":
                # Se a última ação foi perguntar, provavelmente é uma resposta
                return {
                    "action": "extract",
                    "reason": "Resposta a pergunta específica",
                    "confidence": 0.9
                }
            
            # Verifica se a mensagem tem potencial de dados (PRIORIDADE ALTA)
            if self._has_data_potential(message):
                return {
                    "action": "extract",
                    "reason": "Mensagem tem potencial de dados - extração prioritária",
                    "confidence": 0.9
                }
            
            # Verifica completude dos dados existentes
            if self.is_data_complete(existing_data):
                return {
                    "action": "confirm",
                    "reason": "Dados completos, solicitando confirmação",
                    "response": self._get_response_template("confirmation"),
                    "confidence": 0.9
                }
            
            # Verifica campos faltantes e cria resposta contextual
            missing_fields = self._get_missing_fields(existing_data)
            if missing_fields:
                # Cria resposta mais específica baseada no contexto
                if len(existing_data) == 0:
                    # Primeira interação
                    return {
                        "action": "ask",
                        "reason": "Primeira interação - coletando dados básicos",
                        "response": self._get_response_template("welcome"),
                        "next_questions": self.get_missing_fields_questions(missing_fields[:1]),
                        "confidence": 0.8
                    }
                elif len(existing_data) == 1:
                    # Temos um dado, vamos para o próximo
                    next_field = missing_fields[0]
                    field_name = self._get_field_display_name(next_field)
                    return {
                        "action": "ask",
                        "reason": f"Temos {len(existing_data)} dado(s), pedindo {next_field}",
                        "response": self._get_response_template("progress_single", field=field_name),
                        "next_questions": self.get_missing_fields_questions(missing_fields[:1]),
                        "confidence": 0.8
                    }
                else:
                    # Temos vários dados, mostrar progresso
                    missing_display = [self._get_field_display_name(field) for field in missing_fields[:2]]
                    return {
                        "action": "ask",
                        "reason": f"Progresso: {len(existing_data)} dados coletados",
                        "response": self._get_response_template("progress_multiple", 
                                                               count=len(existing_data), 
                                                               fields=", ".join(missing_display)),
                        "next_questions": self.get_missing_fields_questions(missing_fields[:2]),
                        "confidence": 0.8
                    }
            
            # Primeira mensagem ou dados insuficientes
            if len(existing_data) < 2 or not conversation_history:
                return {
                    "action": "extract",
                    "reason": "Primeira extração ou dados insuficientes",
                    "confidence": 0.9
                }
            
            # Fallback: extração geral
            return {
                "action": "extract",
                "reason": "Extração geral para dados adicionais",
                "confidence": 0.7
            }
            
        except Exception as e:
            logger.error(f"Erro no THINK: {str(e)}")
            return {
                "action": "error",
                "error": str(e)
            }
    
    def _has_data_potential(self, message: str) -> bool:
        """
        Verifica se a mensagem tem potencial de conter dados extraíveis.
        
        Args:
            message (str): Mensagem para analisar
            
        Returns:
            bool: True se a mensagem tem potencial de dados
        """
        message_lower = message.lower()
        
        # Palavras-chave que indicam dados específicos
        data_keywords = {
            "nome": ["nome", "chama", "sou", "meu nome", "paciente"],
            "telefone": ["telefone", "celular", "whatsapp", "contato", "número"],
            "data": ["data", "dia", "amanhã", "hoje", "próxima semana", "mês"],
            "horario": ["horário", "hora", "horas", "às", "para"],
            "tipo": ["consulta", "retorno", "primeira", "rotina", "urgente", "checkup"]
        }
        
        # Verifica se a mensagem contém palavras-chave de dados
        for field, keywords in data_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return True
        
        # Padrões que indicam dados
        import re
        data_patterns = [
            # Nomes (pelo menos duas palavras com 2+ letras)
            r'\b[a-z]{2,}\s+[a-z]{2,}\b',
            
            # Telefones (diferentes formatos)
            r'\b\d{10,11}\b',  # 10-11 dígitos
            r'\b\(\d{2}\)\s*\d{4,5}-\d{4}\b',  # (11) 99999-9999
            r'\b\d{2}\s*\d{4,5}-\d{4}\b',  # 11 99999-9999
            
            # Datas
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # DD/MM/YYYY
            r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
            r'\b(hoje|amanhã|depois de amanhã|próxima semana|próximo mês)\b',
            
            # Horários
            r'\b\d{1,2}:\d{2}\b',  # HH:MM
            r'\b\d{1,2}h\b',  # 14h
            r'\b\d{1,2}\s*horas?\b',  # 14 horas
            
            # Expressões temporais
            r'\b(às|para|no dia|na data)\b'
        ]
        
        import re
        for pattern in data_patterns:
            if re.search(pattern, message_lower):
                return True
        
        # Verifica se tem números (potencial telefone, data, etc.)
        if re.search(r'\d', message):
            return True
        
        # Verifica se tem palavras que indicam dados
        data_keywords = [
            'joão', 'maria', 'silva', 'santos', 'oliveira', 'souza',
            'telefone', 'celular', 'fone', 'contato',
            'data', 'dia', 'mês', 'ano',
            'horário', 'hora', 'horas',
            'consulta', 'agendamento', 'marcação'
        ]
        
        for keyword in data_keywords:
            if keyword in message_lower:
                return True
        
        return False
    
    async def _extract(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        EXTRACT: Extrai dados da mensagem usando EntityExtractor com contexto.
        
        Args:
            message (str): Mensagem para extrair dados
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da extração
        """
        try:
            logger.debug("Executando EXTRACT...")
            
            # Usa EntityExtractor para extrair dados com contexto
            extraction_result = await self.entity_extractor.extract_consulta_entities(message, context)
            
            if not extraction_result["success"]:
                return {
                    "action": "error",
                    "error": extraction_result.get("error", "Falha na extração")
                }
            
            # Dados já foram combinados no EntityExtractor
            extracted_data = extraction_result.get("extracted_data", {})
            
            return {
                "action": "extract_success",
                "extracted_data": extracted_data,
                "confidence_score": extraction_result.get("confidence_score", 0.0),
                "missing_fields": extraction_result.get("missing_fields", []),
                "suggested_questions": extraction_result.get("suggested_questions", [])
            }
            
        except Exception as e:
            logger.error(f"Erro no EXTRACT: {str(e)}")
            return {
                "action": "error",
                "error": str(e)
            }
    
    async def _validate(self, extracted_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        VALIDATE: Valida e normaliza dados extraídos.
        
        Args:
            extracted_data (Dict[str, Any]): Dados extraídos para validar
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da validação
        """
        try:
            logger.debug("Executando VALIDATE...")
            
            # Usa data_normalizer para validar e normalizar
            validation_result = normalize_consulta_data(extracted_data)
            
            return {
                "action": "validate_success",
                "normalized_data": validation_result.get("normalized_data", {}),
                "validation_errors": validation_result.get("validation_errors", []),
                "confidence_score": validation_result.get("confidence_score", 0.0),
                "original_data": validation_result.get("original_data", {})
            }
            
        except Exception as e:
            logger.error(f"Erro no VALIDATE: {str(e)}")
            return {
                "action": "error",
                "error": str(e)
            }
    
    async def _act(self, think_result: Dict[str, Any], extract_result: Optional[Dict[str, Any]], 
                   validate_result: Optional[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        ACT: Decide a resposta final baseada nos resultados anteriores.
        """
        try:
            logger.debug("Executando ACT...")
            if think_result["action"] == "error":
                return self._create_error_response("Erro na análise", think_result.get("error"))
            if extract_result and extract_result["action"] == "error":
                return self._create_error_response("Erro na extração", extract_result.get("error"))
            if validate_result and validate_result["action"] == "error":
                return self._create_error_response("Erro na validação", validate_result.get("error"))

            # Dados extraídos e campos faltantes
            extracted_data = None
            missing_fields = []
            confidence_score = 0.0
            if validate_result and validate_result.get("extracted_data"):
                extracted_data = validate_result["extracted_data"]
                missing_fields = validate_result.get("missing_fields", [])
                confidence_score = validate_result.get("confidence_score", 0.0)
            elif extract_result and extract_result.get("extracted_data"):
                extracted_data = extract_result["extracted_data"]
                missing_fields = extract_result.get("missing_fields", [])
                confidence_score = extract_result.get("confidence_score", 0.0)
            else:
                extracted_data = {}
                missing_fields = []

            # Remove campos já preenchidos dos missing_fields
            missing_fields = [f for f in missing_fields if not (extracted_data.get(f) and str(extracted_data[f]).strip())]

            # Se todos os campos obrigatórios preenchidos, mostra resumo antes de confirmar
            if not missing_fields and extracted_data and any(extracted_data.values()):
                response = self.question_generator.generate_summary_before_confirm(extracted_data)
                return {
                    "action": "confirm",
                    "response": response,
                    "data": extracted_data,
                    "confidence": confidence_score
                }

            # Se só falta um campo, pergunta progressiva
            if len(missing_fields) == 1:
                response = self.question_generator.generate_progress_question(extracted_data, missing_fields, context)
                return {
                    "action": "ask",
                    "response": response,
                    "next_questions": [self.question_generator.get_missing_fields_questions(missing_fields)[0]],
                    "data": extracted_data,
                    "confidence": confidence_score
                }

            # Se tem dados mas faltam campos, usa pergunta progressiva
            if extracted_data and missing_fields:
                response = self.question_generator.generate_progress_question(
                    extracted_data, missing_fields, context
                )
                return {
                    "action": "ask",
                    "response": response,
                    "next_questions": self.question_generator.get_missing_fields_questions(missing_fields)[:2],
                    "data": extracted_data,
                    "confidence": confidence_score
                }

            # Dados insuficientes mesmo após validação
            return {
                "action": "ask",
                "response": "Entendi! Pode me fornecer mais detalhes sobre o agendamento?",
                "next_questions": [
                    "Qual é o nome completo do paciente?",
                    "Qual é o telefone para contato?",
                    "Para qual data você gostaria de agendar?"
                ],
                "data": extracted_data,
                "confidence": confidence_score
            }
        except Exception as e:
            logger.error(f"Erro no ACT: {str(e)}")
            return self._create_error_response("Erro interno no ACT", str(e))
    
    def _create_error_response(self, message: str, error: str = None) -> Dict[str, Any]:
        """
        Cria resposta de erro padronizada.
        
        Args:
            message (str): Mensagem de erro
            error (str, optional): Detalhes do erro
            
        Returns:
            Dict: Resposta de erro padronizada
        """
        return {
            "action": "error",
            "response": message,
            "error": error,
            "data": {},
            "next_questions": []
        }
    
    def _initialize_context(self) -> Dict[str, Any]:
        """
        Inicializa um contexto de sessão padrão.
        
        Returns:
            Dict: Contexto inicializado
        """
        return {
            "session_data": {},
            "conversation_history": [],
            "extracted_data": {},
            "confidence_threshold": 0.7,
            "session_start": datetime.now().isoformat(),
            "total_confidence": 0.0,
            "confidence_count": 0
        }
    
    def update_context(self, context: Dict[str, Any], new_data: Dict[str, Any], action: str) -> Dict[str, Any]:
        """
        Atualiza o contexto com novos dados usando merge inteligente.
        
        Args:
            context (Dict[str, Any]): Contexto atual
            new_data (Dict[str, Any]): Novos dados extraídos
            action (str): Ação executada
            
        Returns:
            Dict: Contexto atualizado
        """
        try:
            # Merge inteligente de dados extraídos
            existing_data = context.get("extracted_data", {})
            merged_data = existing_data.copy()
            
            for field, value in new_data.items():
                if value:  # Só atualiza se o valor não for vazio
                    # Se o campo já existe, só sobrescreve se o novo valor for mais completo
                    if field in existing_data:
                        existing_value = existing_data[field]
                        # Prioriza valores mais longos/completos
                        if len(str(value)) > len(str(existing_value)):
                            merged_data[field] = value
                            logger.debug(f"Campo '{field}' atualizado: '{existing_value}' → '{value}'")
                    else:
                        # Campo novo, adiciona
                        merged_data[field] = value
                        logger.debug(f"Novo campo '{field}' adicionado: '{value}'")
            
            # Atualiza contexto
            context["extracted_data"] = merged_data
            context["last_action"] = action
            context["last_update"] = datetime.now().isoformat()
            
            # Calcula confidence médio (será atualizado quando process_message for chamado)
            context["total_confidence"] = context.get("total_confidence", 0.0)
            context["confidence_count"] = context.get("confidence_count", 0)
            if context["confidence_count"] > 0:
                context["average_confidence"] = context["total_confidence"] / context["confidence_count"]
            
            logger.debug(f"Contexto atualizado com {len(new_data)} campos. Total: {len(merged_data)}")
            return context
            
        except Exception as e:
            logger.error(f"Erro ao atualizar contexto: {str(e)}")
            return context
    

    
    def get_context_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retorna resumo detalhado do contexto atual.
        
        Args:
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resumo do contexto
        """
        extracted_data = context.get("extracted_data", {})
        history = context.get("conversation_history", [])
        
        # Calcula completude dos dados
        missing_fields = self.data_summarizer.get_missing_fields(extracted_data)
        total_possible = 5  # name, phone, consulta_date, horario, tipo_consulta
        completeness = (total_possible - len(missing_fields)) / total_possible
        
        # Analisa histórico de confiança
        confidences = [msg.get("confidence", 0.0) for msg in history if msg.get("confidence")]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Última ação e timestamp
        last_action = history[-1] if history else None
        last_timestamp = last_action.get("timestamp") if last_action else None
        
        return {
            "total_messages": len(history),
            "extracted_fields": list(extracted_data.keys()),
            "missing_fields": missing_fields,
            "data_completeness": completeness,
            "last_action": last_action.get("action") if last_action else None,
            "last_timestamp": last_timestamp,
            "average_confidence": avg_confidence,
            "session_duration": self._calculate_session_duration(context),
            "extracted_data_summary": self.data_summarizer.summarize_extracted_data(extracted_data)
        }
    
    def _calculate_session_duration(self, context: Dict[str, Any]) -> str:
        """
        Calcula a duração da sessão.
        
        Args:
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            str: Duração formatada
        """
        try:
            session_start = context.get("session_start")
            if not session_start:
                return "N/A"
            
            start_time = datetime.fromisoformat(session_start)
            current_time = datetime.now()
            duration = current_time - start_time
            
            # Formata duração
            if duration.total_seconds() < 60:
                return f"{int(duration.total_seconds())}s"
            elif duration.total_seconds() < 3600:
                minutes = int(duration.total_seconds() // 60)
                return f"{minutes}m"
            else:
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                return f"{hours}h {minutes}m"
                
        except Exception as e:
            logger.error(f"Erro ao calcular duração da sessão: {str(e)}")
            return "N/A"
    
    def _summarize_extracted_data(self, data: Dict[str, Any]) -> str:
        """
        Cria resumo dos dados extraídos em formato de texto amigável e contextual.
        
        Args:
            data (Dict[str, Any]): Dados extraídos
            
        Returns:
            str: Resumo dos dados em texto
        """
        extracted_items = []
        
        # Nome do paciente
        if data.get("name"):
            name = data['name']
            if len(name.split()) >= 2:
                extracted_items.append(f"nome do paciente: {name}")
            else:
                extracted_items.append(f"nome: {name}")
        
        # Telefone
        if data.get("phone"):
            phone = data['phone']
            # Formata telefone de forma mais amigável
            if len(phone) == 11:
                formatted_phone = f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
            elif len(phone) == 10:
                formatted_phone = f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
            else:
                formatted_phone = phone
            extracted_items.append(f"telefone: {formatted_phone}")
        
        # Data da consulta
        if data.get("consulta_date"):
            date = data['consulta_date']
            # Converte data para formato mais amigável
            try:
                from datetime import datetime
                if '-' in date:
                    date_obj = datetime.strptime(date, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%d/%m/%Y')
                else:
                    formatted_date = date
                extracted_items.append(f"data: {formatted_date}")
            except:
                extracted_items.append(f"data: {date}")
        
        # Horário
        if data.get("horario"):
            horario = data['horario']
            # Formata horário de forma mais amigável
            if ':' in horario:
                extracted_items.append(f"horário: {horario}")
            else:
                extracted_items.append(f"horário: {horario}")
        
        # Tipo de consulta
        if data.get("tipo_consulta"):
            tipo = data['tipo_consulta']
            extracted_items.append(f"tipo: {tipo}")
        
        # Gera resumo contextual baseado no número de itens
        if not extracted_items:
            return "ainda não tenho informações sobre o agendamento"
        elif len(extracted_items) == 1:
            return f"já tenho o {extracted_items[0]}"
        elif len(extracted_items) == 2:
            return f"já tenho: {extracted_items[0]} e {extracted_items[1]}"
        else:
            # Para 3 ou mais itens, agrupa de forma mais natural
            first_items = extracted_items[:-1]
            last_item = extracted_items[-1]
            return f"já tenho: {', '.join(first_items)} e {last_item}"
    
    def _get_field_display_name(self, field: str) -> str:
        """
        Retorna o nome de exibição de um campo para o usuário.
        
        Args:
            field (str): Nome do campo interno
            
        Returns:
            str: Nome de exibição do campo
        """
        field_names = {
            "name": "nome completo do paciente",
            "phone": "telefone para contato",
            "telefone": "telefone para contato",
            "consulta_date": "data do agendamento",
            "data": "data do agendamento",
            "horario": "horário",
            "tipo_consulta": "tipo de consulta",
            "email": "email",
            "cpf": "CPF",
            "cep": "CEP",
            "endereco": "endereço"
        }
        
        return field_names.get(field, field)
    
    def _format_validation_errors(self, errors: List[str]) -> str:
        """
        Formata erros de validação de forma mais amigável para o usuário.
        
        Args:
            errors (List[str]): Lista de erros de validação
            
        Returns:
            str: Erros formatados de forma amigável
        """
        if not errors:
            return ""
        
        # Mapeia erros técnicos para mensagens mais amigáveis
        error_mapping = {
            "Telefone inválido: Número deve ter 10 ou 11 dígitos (com DDD)": "o telefone precisa ter DDD (ex: 11 32210126)",
            "Data inválida: Expressão de data não reconhecida": "a data precisa estar em formato DD/MM/AAAA (ex: 21/07/2025)",
            "CPF inválido": "o CPF está em formato incorreto",
            "Email inválido": "o email está em formato incorreto"
        }
        
        formatted_errors = []
        for error in errors[:2]:  # Limita a 2 erros para não sobrecarregar
            friendly_error = error_mapping.get(error, error)
            formatted_errors.append(friendly_error)
        
        if len(formatted_errors) == 1:
            return formatted_errors[0]
        else:
            return f"{', '.join(formatted_errors[:-1])} e {formatted_errors[-1]}" 