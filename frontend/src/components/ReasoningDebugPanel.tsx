import React from 'react'

interface ReasoningStep {
  type: 'think' | 'extract' | 'validate' | 'act'
  status: 'running' | 'completed' | 'error' | 'idle'
  timestamp?: string
  details?: string
  data?: Record<string, any>
}

interface ReasoningDebugPanelProps {
  isVisible: boolean
  isLoading: boolean
  lastResponse?: {
    action?: string
    extracted_data?: Record<string, any>
    confidence?: number
    next_questions?: string[]
    persistence_status?: string
  }
}

const ReasoningDebugPanel: React.FC<ReasoningDebugPanelProps> = ({
  isVisible,
  isLoading,
  lastResponse
}: ReasoningDebugPanelProps) => {
  if (!isVisible) return null

  // Determina os passos do reasoning baseado na resposta
  const getReasoningSteps = (): ReasoningStep[] => {
    if (!lastResponse) {
      return [
        { type: 'think', status: 'idle' },
        { type: 'extract', status: 'idle' },
        { type: 'validate', status: 'idle' },
        { type: 'act', status: 'idle' }
      ]
    }

    const steps: ReasoningStep[] = []
    const action = lastResponse.action || 'unknown'
    const hasExtractedData = lastResponse.extracted_data && Object.keys(lastResponse.extracted_data).length > 0

    // THINK - Sempre executado
    steps.push({
      type: 'think',
      status: 'completed',
      timestamp: new Date().toLocaleTimeString(),
      details: `Decidiu ação: ${action}`,
      data: { action }
    })

    // EXTRACT - Executado se há dados extraídos ou ação é extract
    if (hasExtractedData || action === 'extract' || action === 'extract_success') {
      steps.push({
        type: 'extract',
        status: 'completed',
        timestamp: new Date().toLocaleTimeString(),
        details: hasExtractedData 
          ? `Extraiu ${Object.keys(lastResponse.extracted_data || {}).length} campos`
          : 'Tentativa de extração',
        data: lastResponse.extracted_data
      })
    } else {
      steps.push({
        type: 'extract',
        status: 'idle',
        details: 'Não necessário para esta ação'
      })
    }

    // VALIDATE - Executado se há dados extraídos
    if (hasExtractedData) {
      steps.push({
        type: 'validate',
        status: 'completed',
        timestamp: new Date().toLocaleTimeString(),
        details: 'Dados validados e normalizados',
        data: lastResponse.extracted_data
      })
    } else {
      steps.push({
        type: 'validate',
        status: 'idle',
        details: 'Nenhum dado para validar'
      })
    }

    // ACT - Sempre executado
    steps.push({
      type: 'act',
      status: 'completed',
      timestamp: new Date().toLocaleTimeString(),
      details: `Ação final: ${action}`,
      data: {
        action,
        confidence: lastResponse.confidence,
        next_questions: lastResponse.next_questions,
        persistence_status: lastResponse.persistence_status
      }
    })

    return steps
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-500 animate-pulse'
      case 'completed':
        return 'bg-green-500'
      case 'error':
        return 'bg-red-500'
      case 'idle':
        return 'bg-gray-300'
      default:
        return 'bg-gray-300'
    }
  }

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'think':
        return '🧠'
      case 'extract':
        return '🔍'
      case 'validate':
        return '✅'
      case 'act':
        return '⚡'
      default:
        return '❓'
    }
  }

  const getStepTitle = (type: string) => {
    switch (type) {
      case 'think':
        return 'THINK'
      case 'extract':
        return 'EXTRACT'
      case 'validate':
        return 'VALIDATE'
      case 'act':
        return 'ACT'
      default:
        return 'UNKNOWN'
    }
  }

  const reasoningSteps = getReasoningSteps()

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 h-full overflow-y-auto">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">
          🔍 Reasoning Loop Debug
        </h3>
        <p className="text-sm text-gray-600">
          Processo interno do agente em tempo real
        </p>
      </div>

      {isLoading && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            <span className="text-sm text-blue-700 font-medium">Processando...</span>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {reasoningSteps.map((step, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-3">
            <div className="flex items-center space-x-3 mb-2">
              <div className={`w-3 h-3 rounded-full ${getStatusColor(step.status)}`}></div>
              <span className="text-2xl">{getStepIcon(step.type)}</span>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-800">{getStepTitle(step.type)}</h4>
                {step.timestamp && (
                  <p className="text-xs text-gray-500">{step.timestamp}</p>
                )}
              </div>
            </div>
            
            <div className="ml-8">
              <p className="text-sm text-gray-700 mb-2">{step.details}</p>
              
              {step.data && Object.keys(step.data).length > 0 && (
                <div className="bg-gray-50 rounded p-2 text-xs">
                  <details>
                    <summary className="cursor-pointer text-gray-600 font-medium">
                      Ver detalhes
                    </summary>
                    <pre className="mt-2 text-gray-700 whitespace-pre-wrap">
                      {JSON.stringify(step.data, null, 2)}
                    </pre>
                  </details>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {lastResponse && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="font-semibold text-gray-800 mb-2">📊 Resumo da Execução</h4>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Ação:</span>
              <span className="font-medium">{lastResponse.action || 'N/A'}</span>
            </div>
            {lastResponse.confidence !== undefined && (
              <div className="flex justify-between">
                <span className="text-gray-600">Confiança:</span>
                <span className="font-medium">{(lastResponse.confidence * 100).toFixed(1)}%</span>
              </div>
            )}
            {lastResponse.extracted_data && (
              <div className="flex justify-between">
                <span className="text-gray-600">Campos extraídos:</span>
                <span className="font-medium">{Object.keys(lastResponse.extracted_data).length}</span>
              </div>
            )}
            {lastResponse.persistence_status && (
              <div className="flex justify-between">
                <span className="text-gray-600">Persistência:</span>
                <span className={`font-medium ${
                  lastResponse.persistence_status === 'success' ? 'text-green-600' :
                  lastResponse.persistence_status === 'failed' ? 'text-red-600' :
                  'text-gray-600'
                }`}>
                  {lastResponse.persistence_status}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default ReasoningDebugPanel 