from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from src.core.question_generator import QuestionGenerator
from src.core.data_summarizer import DataSummarizer


class ConversationManager:
    """
    Gerenciador de conversa para evitar loops, repetições e manter contexto.
    """
    
    def __init__(self):
        """
        Inicializa o gerenciador de conversa.
        """
        self.question_generator = QuestionGenerator()
        self.data_summarizer = DataSummarizer()
        
        # Configurações para evitar repetições
        self.max_repetitions = 2
        self.repetition_threshold = 0.8  # Similaridade para considerar repetição
        
        logger.info("ConversationManager inicializado")
    
    def initialize_context(self) -> Dict[str, Any]:
        """
        Inicializa um novo contexto de conversa.
        
        Returns:
            Contexto inicial da conversa
        """
        return {
            "session_start": datetime.utcnow().isoformat(),
            "conversation_history": [],
            "extracted_data": {},
            "total_confidence": 0.0,
            "confidence_count": 0,
            "average_confidence": 0.0,
            "repetition_count": 0,
            "last_response": None,
            "last_action": None,
            "consecutive_asks": 0,
            "data_progress": {
                "nome": False,
                "telefone": False,
                "data": False,
                "horario": False,
                "tipo_consulta": False
            }
        }
    
    def update_context(self, context: Dict[str, Any], extracted_data: Dict[str, Any], 
                      action: str, response: str) -> Dict[str, Any]:
        """
        Atualiza o contexto com novos dados e informações.
        
        Args:
            context: Contexto atual
            extracted_data: Dados extraídos
            action: Ação realizada
            response: Resposta gerada
            
        Returns:
            Contexto atualizado
        """
        # Atualiza dados extraídos
        if extracted_data:
            context["extracted_data"] = {**context.get("extracted_data", {}), **extracted_data}
            
            # Atualiza progresso dos dados
            data_progress = context.get("data_progress", {})
            for field, value in extracted_data.items():
                if value and str(value).strip():
                    data_progress[field] = True
            context["data_progress"] = data_progress
        
        # Atualiza contadores de ação
        if action == "ask":
            context["consecutive_asks"] = context.get("consecutive_asks", 0) + 1
        else:
            context["consecutive_asks"] = 0
        
        # Verifica repetição
        if self._is_repetition(context, response):
            context["repetition_count"] = context.get("repetition_count", 0) + 1
            logger.warning(f"Repetição detectada. Contador: {context['repetition_count']}")
        else:
            context["repetition_count"] = 0
        
        # Atualiza última resposta e ação
        context["last_response"] = response
        context["last_action"] = action
        
        return context
    
    def add_to_history(self, context: Dict[str, Any], message: str, action: str, 
                      response: str, confidence: float):
        """
        Adiciona interação ao histórico da conversa.
        
        Args:
            context: Contexto da conversa
            message: Mensagem do usuário
            action: Ação realizada
            response: Resposta do agente
            confidence: Confidence score
        """
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_message": message,
            "action": action,
            "response": response,
            "confidence": confidence,
            "extracted_data": context.get("extracted_data", {}).copy()
        }
        
        # Garante que conversation_history existe
        if "conversation_history" not in context:
            context["conversation_history"] = []
            
        context["conversation_history"].append(history_entry)
        
        # Mantém apenas as últimas 10 interações para evitar crescimento excessivo
        if len(context["conversation_history"]) > 10:
            context["conversation_history"] = context["conversation_history"][-10:]
    
    def _is_repetition(self, context: Dict[str, Any], new_response: str) -> bool:
        """
        Verifica se a nova resposta é uma repetição.
        
        Args:
            context: Contexto da conversa
            new_response: Nova resposta
            
        Returns:
            True se é uma repetição
        """
        last_response = context.get("last_response")
        if not last_response:
            return False
        
        # Comparação simples de similaridade
        last_words = set(last_response.lower().split())
        new_words = set(new_response.lower().split())
        
        if not last_words or not new_words:
            return False
        
        intersection = last_words.intersection(new_words)
        union = last_words.union(new_words)
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity > self.repetition_threshold
    
    def should_change_approach(self, context: Dict[str, Any]) -> bool:
        """
        Determina se deve mudar a abordagem da conversa.
        
        Args:
            context: Contexto da conversa
            
        Returns:
            True se deve mudar abordagem
        """
        # Muitas repetições
        if context.get("repetition_count", 0) >= self.max_repetitions:
            return True
        
        # Muitas perguntas consecutivas
        if context.get("consecutive_asks", 0) >= 3:
            return True
        
        # Dados estagnados por muito tempo
        conversation_history = context.get("conversation_history", [])
        if len(conversation_history) > 5:
            recent_actions = [h.get("action") for h in conversation_history[-5:]]
            if all(action == "ask" for action in recent_actions):
                return True
        
        return False
    
    def generate_alternative_response(self, context: Dict[str, Any], missing_fields: List[str]) -> str:
        """
        Gera uma resposta alternativa quando deve mudar abordagem.
        
        Args:
            context: Contexto da conversa
            missing_fields: Campos faltantes
            
        Returns:
            Resposta alternativa
        """
        if not missing_fields:
            return "Perfeito! Tenho todas as informações necessárias. Posso confirmar o agendamento?"
        
        # Abordagem mais direta
        if len(missing_fields) == 1:
            field = missing_fields[0]
            field_names = {
                "nome": "nome completo",
                "telefone": "telefone",
                "data": "data",
                "horario": "horário",
                "tipo_consulta": "tipo de consulta"
            }
            field_name = field_names.get(field, field)
            return f"Para finalizar, preciso apenas do {field_name}."
        
        # Abordagem mais específica
        field_names = {
            "nome": "nome",
            "telefone": "telefone", 
            "data": "data",
            "horario": "horário",
            "tipo_consulta": "tipo de consulta"
        }
        
        missing_text = ", ".join([field_names.get(f, f) for f in missing_fields[:2]])
        return f"Falta apenas: {missing_text}."
    
    def get_conversation_flow_suggestion(self, context: Dict[str, Any], message: str) -> Dict[str, Any]:
        """
        Sugere o fluxo da conversa baseado no contexto atual.
        
        Args:
            context: Contexto da conversa
            message: Mensagem do usuário
            
        Returns:
            Sugestão de fluxo com ação e abordagem
        """
        extracted_data = context.get("extracted_data", {})
        missing_fields = self.data_summarizer.get_missing_fields(extracted_data)
        
        # Se deve mudar abordagem
        if self.should_change_approach(context):
            return {
                "action": "ask",
                "approach": "alternative",
                "response": self.generate_alternative_response(context, missing_fields),
                "reason": "Mudança de abordagem devido a repetições ou loops"
            }
        
        # Se o usuário está pedindo detalhes específicos
        if self.question_generator.should_ask_specific_question(message, context):
            if missing_fields:
                return {
                    "action": "ask",
                    "approach": "specific",
                    "response": f"Claro! Preciso especificamente de: {', '.join(missing_fields[:2])}",
                    "reason": "Usuário pedindo detalhes específicos"
                }
        
        # Fluxo normal baseado no progresso
        if missing_fields:
            # Verifica se tem dados suficientes para ser mais específico
            data_progress = context.get("data_progress", {})
            completed_fields = sum(1 for v in data_progress.values() if v)
            
            if completed_fields >= 2:
                # Já tem alguns dados, pode ser mais específico
                return {
                    "action": "ask",
                    "approach": "progress",
                    "response": self.question_generator.generate_data_summary_question(extracted_data, missing_fields),
                    "reason": "Fluxo normal - solicitando campos faltantes com progresso"
                }
            else:
                # Ainda no início, pergunta mais genérica
                return {
                    "action": "ask",
                    "approach": "welcome",
                    "response": self.question_generator.generate_contextual_question("welcome"),
                    "reason": "Início da conversa - pergunta genérica"
                }
        else:
            return {
                "action": "confirm",
                "approach": "normal",
                "response": self.question_generator.generate_contextual_question("confirmation"),
                "reason": "Dados completos - solicitando confirmação"
            }
    
    def get_conversation_progress(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retorna o progresso atual da conversa.
        
        Args:
            context: Contexto da conversa
            
        Returns:
            Informações de progresso
        """
        data_progress = context.get("data_progress", {})
        completed_fields = sum(1 for v in data_progress.values() if v)
        total_fields = len(data_progress)
        
        return {
            "completed_fields": completed_fields,
            "total_fields": total_fields,
            "progress_percentage": (completed_fields / total_fields) * 100 if total_fields > 0 else 0,
            "missing_fields": self.data_summarizer.get_missing_fields(context.get("extracted_data", {})),
            "conversation_length": len(context.get("conversation_history", [])),
            "repetition_count": context.get("repetition_count", 0),
            "consecutive_asks": context.get("consecutive_asks", 0)
        } 