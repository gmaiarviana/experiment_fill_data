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
            "consecutive_asks": 0
        }
    
    def update_context(self, context: Dict[str, Any], new_data: Dict[str, Any], action: str, response: str) -> Dict[str, Any]:
        """
        Atualiza o contexto da conversa com novos dados.
        
        Args:
            context: Contexto atual
            new_data: Novos dados extraídos
            action: Ação realizada
            response: Resposta gerada
            
        Returns:
            Contexto atualizado
        """
        # Atualiza dados extraídos
        if new_data:
            context["extracted_data"].update(new_data)
        
        # Verifica se é repetição
        if self._is_repetition(context, response):
            context["repetition_count"] += 1
            logger.warning(f"Repetição detectada. Contador: {context['repetition_count']}")
        else:
            context["repetition_count"] = 0
        
        # Atualiza contador de perguntas consecutivas
        if action == "ask":
            context["consecutive_asks"] = context.get("consecutive_asks", 0) + 1
        else:
            context["consecutive_asks"] = 0
        
        # Atualiza histórico
        context["last_response"] = response
        context["last_action"] = action
        
        return context
    
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
        Gera uma resposta alternativa quando a abordagem normal não está funcionando.
        
        Args:
            context: Contexto da conversa
            missing_fields: Campos que ainda faltam
            
        Returns:
            Resposta alternativa
        """
        extracted_data = context.get("extracted_data", {})
        
        if context.get("repetition_count", 0) >= self.max_repetitions:
            # Abordagem mais direta
            if len(missing_fields) == 1:
                return f"Vou ser mais direto: preciso do {self.data_summarizer.get_field_display_name(missing_fields[0])}. Pode me informar?"
            else:
                return f"Vou simplificar: preciso de {self.data_summarizer.format_missing_fields_for_display(missing_fields)}. Pode me passar essas informações?"
        
        elif context.get("consecutive_asks", 0) >= 3:
            # Abordagem mais amigável
            summary = self.data_summarizer.summarize_extracted_data(extracted_data)
            return f"Vejo que já temos {summary}. Para completar o agendamento, preciso apenas de {self.data_summarizer.format_missing_fields_for_display(missing_fields)}. Pode me ajudar?"
        
        else:
            # Abordagem contextual
            return self.question_generator.generate_data_summary_question(extracted_data, missing_fields)
    
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
        
        # Fluxo normal
        if missing_fields:
            return {
                "action": "ask",
                "approach": "normal",
                "response": self.question_generator.generate_data_summary_question(extracted_data, missing_fields),
                "reason": "Fluxo normal - solicitando campos faltantes"
            }
        else:
            return {
                "action": "confirm",
                "approach": "normal",
                "response": self.question_generator.generate_contextual_question("confirmation"),
                "reason": "Dados completos - solicitando confirmação"
            }
    
    def add_to_history(self, context: Dict[str, Any], message: str, action: str, response: str, confidence: float = 0.0):
        """
        Adiciona uma interação ao histórico da conversa.
        
        Args:
            context: Contexto da conversa
            message: Mensagem do usuário
            action: Ação realizada
            response: Resposta do sistema
            confidence: Score de confiança
        """
        interaction = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "response": response,
            "confidence": confidence
        }
        
        context["conversation_history"].append(interaction)
        
        # Limita o histórico para evitar crescimento excessivo
        if len(context["conversation_history"]) > 20:
            context["conversation_history"] = context["conversation_history"][-20:]
    
    def get_conversation_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera um resumo da conversa atual.
        
        Args:
            context: Contexto da conversa
            
        Returns:
            Resumo da conversa
        """
        extracted_data = context.get("extracted_data", {})
        missing_fields = self.data_summarizer.get_missing_fields(extracted_data)
        
        return {
            "session_duration": self._calculate_session_duration(context),
            "total_interactions": len(context.get("conversation_history", [])),
            "extracted_fields": len([v for v in extracted_data.values() if v]),
            "missing_fields": len(missing_fields),
            "completeness_percentage": self.data_summarizer.get_data_completeness_percentage(extracted_data),
            "average_confidence": context.get("average_confidence", 0.0),
            "repetition_count": context.get("repetition_count", 0),
            "consecutive_asks": context.get("consecutive_asks", 0)
        }
    
    def _calculate_session_duration(self, context: Dict[str, Any]) -> str:
        """
        Calcula a duração da sessão.
        
        Args:
            context: Contexto da conversa
            
        Returns:
            Duração formatada
        """
        session_start = context.get("session_start")
        if not session_start:
            return "desconhecida"
        
        try:
            start_time = datetime.fromisoformat(session_start)
            duration = datetime.now() - start_time
            
            if duration.total_seconds() < 60:
                return f"{int(duration.total_seconds())}s"
            elif duration.total_seconds() < 3600:
                return f"{int(duration.total_seconds() // 60)}m"
            else:
                return f"{int(duration.total_seconds() // 3600)}h {int((duration.total_seconds() % 3600) // 60)}m"
        except Exception as e:
            logger.warning(f"Erro ao calcular duração da sessão: {e}")
            return "desconhecida" 