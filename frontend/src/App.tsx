import React, { useState, useEffect, useRef } from 'react'
import ReasoningDebugPanel from './components/ReasoningDebugPanel'
import StructuredDataPanel from './components/StructuredDataPanel'
import { sendMessage, getSessionId, checkApiHealth, ChatResponse } from './services/api'
import './App.css'

interface ChatMessage {
  id: string
  text: string
  isUser: boolean
  timestamp: Date
}

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [sessionId, setSessionId] = useState<string>('')
  const [lastResponse, setLastResponse] = useState<ChatResponse | undefined>(undefined)
  const [apiHealth, setApiHealth] = useState<boolean>(true)
  const pollingIntervalRef = useRef<number | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Inicializar session_id
  useEffect(() => {
    const session = getSessionId()
    setSessionId(session)
  }, [])

  // Verificar saúde da API periodicamente
  useEffect(() => {
    const checkHealth = async () => {
      const health = await checkApiHealth()
      setApiHealth(health)
    }
    
    checkHealth()
    const healthInterval = setInterval(checkHealth, 30000) // Verificar a cada 30s
    
    return () => clearInterval(healthInterval)
  }, [])

  // Função para iniciar polling
  const startPolling = (response: ChatResponse) => {
    if (response.status === 'processing') {
      setIsPolling(true)
      setLastResponse(response)
      
      // Polling inteligente: 500ms durante processamento
      pollingIntervalRef.current = setInterval(async () => {
        try {
          const updatedResponse = await sendMessage('', sessionId) // Polling com mensagem vazia
          setLastResponse(updatedResponse)
          
          if (updatedResponse.status === 'completed' || updatedResponse.status === 'error') {
            stopPolling()
            
            // Adicionar resposta final ao chat
            const botMessage: ChatMessage = {
              id: Date.now().toString(),
              text: updatedResponse.response,
              isUser: false,
              timestamp: new Date()
            }
            setMessages((prev: ChatMessage[]) => [...prev, botMessage])
          }
        } catch (error) {
          console.error('Erro no polling:', error)
          stopPolling()
        }
      }, 500)
    } else {
      // Resposta imediata, não precisa de polling
      setLastResponse(response)
      const botMessage: ChatMessage = {
        id: Date.now().toString(),
        text: response.response,
        isUser: false,
        timestamp: new Date()
      }
      setMessages((prev: ChatMessage[]) => [...prev, botMessage])
    }
  }

  // Função para parar polling
  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
    setIsPolling(false)
    setIsLoading(false)
  }

  // Função para enviar mensagem
  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading || !apiHealth) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      text: inputMessage,
      isUser: true,
      timestamp: new Date()
    }

          setMessages((prev: ChatMessage[]) => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await sendMessage(inputMessage, sessionId)
      startPolling(response)
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.',
        isUser: false,
        timestamp: new Date()
      }
      setMessages((prev: ChatMessage[]) => [...prev, errorMessage])
      setIsLoading(false)
    }
  }

  // Função para lidar com tecla Enter
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // Scroll automático para o final
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Cleanup do polling ao desmontar
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Data Structuring Agent
          </h1>
          <p className="text-gray-600">
            Sistema conversacional que transforma conversas naturais em dados estruturados
          </p>
          {/* Status da API */}
          <div className="mt-2">
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
              apiHealth ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              <span className={`w-2 h-2 rounded-full mr-2 ${
                apiHealth ? 'bg-green-400' : 'bg-red-400'
              }`}></span>
              {apiHealth ? 'API Online' : 'API Offline'}
            </span>
          </div>
        </header>
        
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Chat Area (2/4) */}
          <div className="md:col-span-2">
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              {/* Chat Header */}
              <div className="bg-blue-600 text-white px-6 py-4">
                <h2 className="text-xl font-semibold">Chat Conversacional</h2>
                <p className="text-blue-100 text-sm">
                  Converse naturalmente e veja os dados sendo extraídos automaticamente
                </p>
              </div>

              {/* Messages Area */}
              <div className="h-96 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                  <div className="text-center text-gray-500 py-8">
                    <p>Digite uma mensagem para começar a conversar!</p>
                    <p className="text-sm mt-2">
                      Exemplo: "Olá, quero marcar uma consulta para João Silva amanhã às 14h"
                    </p>
                  </div>
                )}
                
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.isUser
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-800'
                      }`}
                    >
                      <p className="text-sm">{message.text}</p>
                      <p className={`text-xs mt-1 ${
                        message.isUser ? 'text-blue-100' : 'text-gray-500'
                      }`}>
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
                
                {(isLoading || isPolling) && (
                  <div className="flex justify-start">
                    <div className="bg-gray-200 text-gray-800 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                        <span className="text-sm">
                          {isPolling ? 'Processando dados...' : 'Enviando mensagem...'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="border-t border-gray-200 p-4">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Digite sua mensagem..."
                    disabled={isLoading || isPolling || !apiHealth}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isLoading || isPolling || !apiHealth}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                  >
                    Enviar
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          {/* Reasoning Panel (1/4) */}
          <div className="hidden md:block">
            <ReasoningDebugPanel
              isVisible={true}
              isLoading={isLoading || isPolling}
              lastResponse={lastResponse}
            />
          </div>
          
          {/* Structured Data Panel (1/4) */}
          <div className="hidden md:block">
            <StructuredDataPanel
              isVisible={true}
              isLoading={isLoading || isPolling}
              lastResponse={lastResponse}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App 