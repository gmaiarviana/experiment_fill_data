// Tipos para integração com backend
export interface ChatRequest {
  message: string;
  session_id: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  timestamp: string;
  action?: string;
  extracted_data?: Record<string, any>;
  confidence?: number;
  next_questions?: string[];
  consultation_id?: number;
  persistence_status?: string;
  reasoning_loop?: any;
  status?: 'processing' | 'completed' | 'error';
}

// Configuração da API
const API_BASE_URL = 'http://localhost:8000';
const API_TIMEOUT = 10000; // 10 segundos
const MAX_RETRIES = 3;

// Geração de session_id único
export function getSessionId(): string {
  let sessionId = localStorage.getItem('chat_session_id');
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('chat_session_id', sessionId);
  }
  return sessionId;
}

// Função para fazer request com timeout
async function fetchWithTimeout(url: string, options: RequestInit, timeout: number): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

// Função principal para enviar mensagem
export async function sendMessage(message: string, sessionId: string): Promise<ChatResponse> {
  const url = `${API_BASE_URL}/chat/message`;
  const body: ChatRequest = {
    message,
    session_id: sessionId,
  };

  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await fetchWithTimeout(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      }, API_TIMEOUT);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ChatResponse = await response.json();
      return data;
    } catch (error) {
      lastError = error as Error;
      console.warn(`Tentativa ${attempt}/${MAX_RETRIES} falhou:`, error);
      
      // Se não for a última tentativa, aguarda antes de tentar novamente
      if (attempt < MAX_RETRIES) {
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt)); // Backoff exponencial
      }
    }
  }

  // Se todas as tentativas falharam
  throw new Error(`Falha após ${MAX_RETRIES} tentativas. Último erro: ${lastError?.message}`);
}

// Função para verificar status da API
export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/system/health`, {
      method: 'GET',
    }, 5000);
    return response.ok;
  } catch (error) {
    console.error('API health check falhou:', error);
    return false;
  }
} 