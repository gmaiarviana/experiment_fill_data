from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from src.core.entity_extraction import EntityExtractor
from src.core.data_normalizer import normalize_consulta_data


class ReasoningEngine:
    """
    Motor de raciocínio que implementa o loop Think → Extract → Validate → Act
    para processamento inteligente de mensagens conversacionais.
    """
    
    def __init__(self):
        """
        Inicializa o motor de raciocínio com o extrator de entidades.
        """
        self.entity_extractor = EntityExtractor()
        logger.info("ReasoningEngine inicializado com EntityExtractor")
    
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
                context = self._initialize_context()
            
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
            if extract_result and extract_result.get("extracted_data"):
                context = self.update_context(
                    context, 
                    extract_result["extracted_data"], 
                    act_result["action"]
                )
            
            # Atualiza confidence tracking
            confidence = act_result.get("confidence", 0.0)
            context["total_confidence"] += confidence
            context["confidence_count"] += 1
            context["average_confidence"] = context["total_confidence"] / context["confidence_count"]
            
            # Adiciona mensagem ao histórico com timestamp real
            context["conversation_history"].append({
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "action": act_result["action"],
                "confidence": confidence
            })
            
            logger.info(f"Processamento concluído. Ação: {act_result['action']}, Confidence: {confidence:.2f}")
            return act_result
            
        except Exception as e:
            logger.error(f"Erro no processamento da mensagem: {str(e)}")
            return self._create_error_response("Erro interno no processamento", str(e))
    
    async def _think(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        THINK: Analisa a mensagem e decide o próximo passo baseado no contexto e histórico.
        Prioriza EXTRACT quando há potencial de dados na mensagem.
        
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
            conversation_history = context.get("conversation_history", [])
            existing_data = context.get("extracted_data", {})
            
            # Verifica se é uma confirmação (considera contexto)
            confirmation_words = ["sim", "confirmo", "correto", "certo", "ok", "perfeito", "confirma"]
            if any(word in message_lower for word in confirmation_words):
                # Se tem dados suficientes, confirma
                if self.is_data_complete(existing_data):
                    return {
                        "action": "complete",
                        "reason": "Confirmação com dados completos",
                        "response": "Perfeito! Agendamento confirmado com sucesso.",
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
                # Analisa qual campo precisa ser corrigido baseado no histórico
                last_action = conversation_history[-1]["action"] if conversation_history else None
                if last_action == "ask":
                    return {
                        "action": "ask",
                        "reason": "Correção após pergunta específica",
                        "response": "Entendi, vou corrigir. Pode me informar novamente os dados corretos?",
                        "next_questions": self.get_missing_fields_questions(list(existing_data.keys())),
                        "confidence": 0.8
                    }
                else:
                    return {
                        "action": "extract",
                        "reason": "Correção geral - nova extração",
                        "confidence": 0.7
                    }
            
            # Verifica se é uma resposta específica a uma pergunta anterior
            if conversation_history and conversation_history[-1]["action"] == "ask":
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
                    "response": "Perfeito! Tenho todas as informações. Posso confirmar o agendamento?",
                    "confidence": 0.9
                }
            
            # Verifica campos faltantes
            missing_fields = self._get_missing_fields(existing_data)
            if missing_fields:
                return {
                    "action": "ask",
                    "reason": f"Faltam campos: {missing_fields}",
                    "response": "Preciso de mais algumas informações para completar o agendamento.",
                    "next_questions": self.get_missing_fields_questions(missing_fields),
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
        
        # Padrões que indicam dados
        data_patterns = [
            # Nomes
            r'\b[a-z]{2,}\s+[a-z]{2,}\b',  # Duas palavras (nome completo)
            
            # Telefones
            r'\b\d{10,11}\b',  # 10-11 dígitos
            r'\b\(\d{2}\)\s*\d{4,5}-\d{4}\b',  # Formato (11) 99999-9999
            
            # Datas
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # DD/MM/YYYY
            r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
            r'\b(hoje|amanhã|depois de amanhã|próxima semana|próximo mês)\b',
            
            # Horários
            r'\b\d{1,2}:\d{2}\b',  # HH:MM
            r'\b\d{1,2}h\b',  # 14h
            
            # Tipos de consulta
            r'\b(consulta|retorno|primeira consulta|rotina|urgente)\b',
            
            # Palavras-chave que indicam dados
            r'\b(nome|telefone|data|horário|consulta|agendar|marcar)\b'
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
        EXTRACT: Extrai dados da mensagem usando EntityExtractor.
        
        Args:
            message (str): Mensagem para extrair dados
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resultado da extração
        """
        try:
            logger.debug("Executando EXTRACT...")
            
            # Usa EntityExtractor para extrair dados
            extraction_result = await self.entity_extractor.extract_consulta_entities(message)
            
            if not extraction_result["success"]:
                return {
                    "action": "error",
                    "error": extraction_result.get("error", "Falha na extração")
                }
            
            # Combina com dados existentes do contexto
            existing_data = context.get("extracted_data", {})
            new_data = extraction_result.get("extracted_data", {})
            
            # Atualiza dados existentes com novos dados
            combined_data = {**existing_data, **new_data}
            
            return {
                "action": "extract_success",
                "extracted_data": combined_data,
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
        
        Args:
            think_result (Dict[str, Any]): Resultado do THINK
            extract_result (Optional[Dict[str, Any]]): Resultado do EXTRACT
            validate_result (Optional[Dict[str, Any]]): Resultado do VALIDATE
            context (Dict[str, Any]): Contexto da sessão
            
        Returns:
            Dict: Resposta final com ação e dados
        """
        try:
            logger.debug("Executando ACT...")
            
            # Se houve erro em qualquer etapa anterior
            if think_result["action"] == "error":
                return self._create_error_response("Erro na análise", think_result.get("error"))
            
            if extract_result and extract_result["action"] == "error":
                return self._create_error_response("Erro na extração", extract_result.get("error"))
            
            if validate_result and validate_result["action"] == "error":
                return self._create_error_response("Erro na validação", validate_result.get("error"))
            
            # Decide ação baseada no resultado do THINK
            if think_result["action"] == "ask":
                return {
                    "action": "ask",
                    "response": think_result.get("response", "Preciso de mais informações."),
                    "next_questions": think_result.get("next_questions", []),
                    "data": context.get("extracted_data", {}),
                    "confidence": think_result.get("confidence", 0.0)
                }
            
            elif think_result["action"] == "confirm":
                return {
                    "action": "confirm",
                    "response": think_result.get("response", "Posso confirmar os dados?"),
                    "data": context.get("extracted_data", {}),
                    "confidence": think_result.get("confidence", 0.0)
                }
            
            elif think_result["action"] == "extract":
                # Se extraiu dados, analisa resultado usando EXTRACT + VALIDATE
                if extract_result and extract_result["action"] == "extract_success":
                    # Usa dados validados se disponível, senão usa dados extraídos
                    if validate_result and validate_result["action"] == "validate_success":
                        final_data = validate_result.get("normalized_data", {})
                        validation_confidence = validate_result.get("confidence_score", 0.0)
                        validation_errors = validate_result.get("validation_errors", [])
                        
                        # Combina confidence da extração e validação
                        extract_confidence = extract_result.get("confidence_score", 0.0)
                        combined_confidence = (extract_confidence + validation_confidence) / 2
                        
                        logger.debug(f"Dados validados: {final_data}, Confidence: {combined_confidence}")
                        
                        # Se tem erros de validação, pergunta para corrigir
                        if validation_errors:
                            return {
                                "action": "ask",
                                "response": "Encontrei alguns problemas nos dados. Pode corrigir?",
                                "next_questions": [f"Corrija: {error}" for error in validation_errors[:2]],
                                "data": final_data,
                                "confidence": combined_confidence,
                                "validation_errors": validation_errors
                            }
                        
                        # Verifica se dados estão completos após validação
                        if self.is_data_complete(final_data):
                            return {
                                "action": "complete",
                                "response": "Perfeito! Agendamento confirmado com sucesso.",
                                "data": final_data,
                                "confidence": combined_confidence
                            }
                        
                        # Se não está completo, pergunta pelos campos faltantes
                        missing_fields = self._get_missing_fields(final_data)
                        if missing_fields:
                            return {
                                "action": "ask",
                                "response": "Ótimo! Agora preciso de mais algumas informações.",
                                "next_questions": self.get_missing_fields_questions(missing_fields),
                                "data": final_data,
                                "confidence": combined_confidence
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
                            "data": final_data,
                            "confidence": combined_confidence
                        }
                    
                    else:
                        # Usa dados extraídos sem validação
                        extracted_data = extract_result["extracted_data"]
                        confidence_score = extract_result.get("confidence_score", 0.0)
                        missing_fields = extract_result.get("missing_fields", [])
                        
                        # Verifica se dados estão completos
                        if self.is_data_complete(extracted_data):
                            return {
                                "action": "confirm",
                                "response": "Tenho as informações! Posso confirmar o agendamento?",
                                "data": extracted_data,
                                "confidence": confidence_score
                            }
                        
                        # Se tem dados mas faltam campos
                        if extracted_data and missing_fields:
                            return {
                                "action": "ask",
                                "response": "Ótimo! Agora preciso de mais algumas informações.",
                                "next_questions": extract_result.get("suggested_questions", [])[:2],
                                "data": extracted_data,
                                "confidence": confidence_score
                            }
                        
                        # Se extração foi bem-sucedida mas dados insuficientes
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
                
                # Se extração falhou
                else:
                    return {
                        "action": "ask",
                        "response": "Não consegui entender completamente. Pode reformular?",
                        "next_questions": [
                            "Qual é o nome do paciente?",
                            "Qual é o telefone?",
                            "Para quando é o agendamento?"
                        ],
                        "data": {},
                        "confidence": 0.0
                    }
            
            # Ação padrão
            return {
                "action": "ask",
                "response": "Como posso ajudar com o agendamento?",
                "next_questions": ["Qual é o nome do paciente?"],
                "data": {},
                "confidence": 0.0
            }
            
        except Exception as e:
            logger.error(f"Erro no ACT: {str(e)}")
            return self._create_error_response("Erro na decisão final", str(e))
    
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
    
    def is_data_complete(self, data: Dict[str, Any]) -> bool:
        """
        Verifica se os dados estão completos para um agendamento.
        Considera 3+ campos como completo.
        
        Args:
            data (Dict[str, Any]): Dados para verificar
            
        Returns:
            bool: True se os dados estão completos (3+ campos válidos)
        """
        # Campos principais para agendamento
        main_fields = ["name", "phone", "consulta_date", "horario", "tipo_consulta"]
        
        # Conta campos válidos (presentes e não vazios)
        valid_fields = 0
        for field in main_fields:
            value = data.get(field, "")
            if value and str(value).strip() != "":
                valid_fields += 1
        
        # Considera completo se tem 3+ campos válidos
        return valid_fields >= 3
    
    def get_missing_fields_questions(self, missing_fields: List[str]) -> List[str]:
        """
        Gera perguntas específicas para campos faltantes.
        
        Args:
            missing_fields (List[str]): Lista de campos faltantes
            
        Returns:
            List[str]: Lista de perguntas para os campos faltantes
        """
        field_questions = {
            "name": "Qual é o nome completo do paciente?",
            "phone": "Qual é o telefone para contato?",
            "telefone": "Qual é o telefone para contato?",
            "consulta_date": "Para qual data você gostaria de agendar?",
            "data": "Para qual data você gostaria de agendar?",
            "horario": "Qual horário prefere?",
            "tipo_consulta": "Que tipo de consulta é esta?",
            "email": "Qual é o email para contato?",
            "cpf": "Qual é o CPF do paciente?",
            "cep": "Qual é o CEP do endereço?",
            "endereco": "Qual é o endereço completo?"
        }
        
        questions = []
        for field in missing_fields[:3]:  # Limita a 3 perguntas por vez
            if field in field_questions:
                questions.append(field_questions[field])
            else:
                questions.append(f"Qual é o {field}?")
        
        return questions
    
    def _get_missing_fields(self, data: Dict[str, Any]) -> List[str]:
        """
        Identifica campos faltantes nos dados.
        Considera campos principais para completude.
        
        Args:
            data (Dict[str, Any]): Dados para verificar
            
        Returns:
            List[str]: Lista de campos faltantes
        """
        main_fields = ["name", "phone", "consulta_date", "horario", "tipo_consulta"]
        missing = []
        
        for field in main_fields:
            value = data.get(field, "")
            if not value or str(value).strip() == "":
                missing.append(field)
        
        return missing
    
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
        missing_fields = self._get_missing_fields(extracted_data)
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
            "extracted_data_summary": self._summarize_extracted_data(extracted_data)
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
    
    def _summarize_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria resumo dos dados extraídos.
        
        Args:
            data (Dict[str, Any]): Dados extraídos
            
        Returns:
            Dict[str, Any]: Resumo dos dados
        """
        summary = {}
        
        # Resumo por tipo de campo
        if data.get("name"):
            summary["patient_name"] = data["name"][:20] + "..." if len(data["name"]) > 20 else data["name"]
        
        if data.get("phone"):
            summary["phone"] = data["phone"]
        
        if data.get("consulta_date"):
            summary["appointment_date"] = data["consulta_date"]
        
        if data.get("horario"):
            summary["appointment_time"] = data["horario"]
        
        if data.get("tipo_consulta"):
            summary["consultation_type"] = data["tipo_consulta"]
        
        # Conta campos preenchidos
        summary["total_fields"] = len([v for v in data.values() if v])
        summary["total_possible"] = 5  # Campos principais
        
        return summary 