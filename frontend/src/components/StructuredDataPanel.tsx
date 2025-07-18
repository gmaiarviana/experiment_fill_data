interface ChatResponse {
  response: string
  session_id: string
  timestamp: string
  action?: string
  extracted_data?: Record<string, any>
  confidence?: number
  next_questions?: string[]
  consultation_id?: number
  persistence_status?: string
}

interface StructuredDataPanelProps {
  isVisible: boolean
  isLoading: boolean
  lastResponse?: ChatResponse
}

interface FieldInfo {
  label: string
  value: any
  required: boolean
  status: 'valid' | 'invalid' | 'pending' | 'empty'
  confidence?: number
}

const StructuredDataPanel = ({
  isVisible,
  isLoading,
  lastResponse
}: StructuredDataPanelProps) => {
  if (!isVisible) {
    return null
  }

  const getFieldInfo = (): FieldInfo[] => {
    if (!lastResponse?.extracted_data) {
      return []
    }

    const data = lastResponse.extracted_data
    const confidence = lastResponse.confidence || 0

    // Mapeamento de campos com informações de validação
    const fieldMappings = [
      {
        key: 'nome',
        label: 'Nome do Paciente',
        required: true,
        validator: (value: any) => {
          if (!value || !String(value).trim()) return 'empty'
          const name = String(value).trim()
          if (name.length < 2) return 'invalid'
          if (name.split(' ').length < 2) return 'invalid'
          return 'valid'
        }
      },
      {
        key: 'telefone',
        label: 'Telefone',
        required: true,
        validator: (value: any) => {
          if (!value || !String(value).trim()) return 'empty'
          const phone = String(value).replace(/\D/g, '')
          if (phone.length < 10 || phone.length > 11) return 'invalid'
          return 'valid'
        }
      },
      {
        key: 'data',
        label: 'Data da Consulta',
        required: true,
        validator: (value: any) => {
          if (!value || !String(value).trim()) return 'empty'
          // Validação básica de data
          const dateStr = String(value)
          if (!/^\d{4}-\d{2}-\d{2}/.test(dateStr)) return 'invalid'
          return 'valid'
        }
      },
      {
        key: 'horario',
        label: 'Horário',
        required: true,
        validator: (value: any) => {
          if (!value || !String(value).trim()) return 'empty'
          const time = String(value)
          if (!/^\d{1,2}:\d{2}/.test(time)) return 'invalid'
          return 'valid'
        }
      },
      {
        key: 'tipo_consulta',
        label: 'Tipo de Consulta',
        required: false,
        validator: (value: any) => {
          if (!value || !String(value).trim()) return 'empty'
          return 'valid'
        }
      }
    ]

    return fieldMappings.map(field => {
      const value = data[field.key] || data[field.key.replace('nome', 'name')] || data[field.key.replace('telefone', 'phone')] || data[field.key.replace('data', 'consulta_date')]
      const status = field.validator(value)
      
      return {
        label: field.label,
        value: value,
        required: field.required,
        status,
        confidence: confidence
      }
    })
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'valid':
        return '✓'
      case 'invalid':
        return '❌'
      case 'pending':
        return '⏳'
      case 'empty':
        return '○'
      default:
        return '○'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'valid':
        return 'text-green-600'
      case 'invalid':
        return 'text-red-600'
      case 'pending':
        return 'text-yellow-600'
      case 'empty':
        return 'text-gray-400'
      default:
        return 'text-gray-400'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    if (confidence >= 0.4) return 'text-orange-600'
    return 'text-red-600'
  }

  const getConfidenceBarColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-500'
    if (confidence >= 0.6) return 'bg-yellow-500'
    if (confidence >= 0.4) return 'bg-orange-500'
    return 'bg-red-500'
  }

  const fields = getFieldInfo()
  const hasData = fields.length > 0
  const overallConfidence = lastResponse?.confidence || 0

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-green-600 text-white px-6 py-4">
        <h2 className="text-xl font-semibold">📊 Dados Estruturados</h2>
        <p className="text-green-100 text-sm">
          Dados extraídos e validados em tempo real
        </p>
      </div>

      {/* Content */}
      <div className="p-6">
        {isLoading && (
          <div className="text-center py-8">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
            <p className="text-gray-600">Extraindo dados...</p>
          </div>
        )}

        {!isLoading && !hasData && (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">📋</div>
            <p className="text-gray-600 mb-2">Nenhum dado extraído ainda</p>
            <p className="text-sm text-gray-500">
              Converse naturalmente para ver os dados sendo extraídos automaticamente
            </p>
          </div>
        )}

        {!isLoading && hasData && (
          <div className="space-y-6">
            {/* Overall Confidence */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="font-semibold text-gray-800">Confiança Geral</span>
                <span className={`font-bold ${getConfidenceColor(overallConfidence)}`}>
                  {(overallConfidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${getConfidenceBarColor(overallConfidence)}`}
                  style={{ width: `${overallConfidence * 100}%` }}
                ></div>
              </div>
            </div>

            {/* Fields */}
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-800 mb-3">Campos Extraídos</h3>
              
              {fields.map((field, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className={`text-lg ${getStatusColor(field.status)}`}>
                        {getStatusIcon(field.status)}
                      </span>
                      <span className="font-medium text-gray-800">
                        {field.label}
                      </span>
                      {field.required && (
                        <span className="text-xs bg-red-100 text-red-600 px-2 py-1 rounded">
                          Obrigatório
                        </span>
                      )}
                    </div>
                    {field.confidence !== undefined && (
                      <span className={`text-sm font-medium ${getConfidenceColor(field.confidence)}`}>
                        {(field.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  
                  <div className="ml-8">
                    {field.status === 'empty' ? (
                      <span className="text-gray-400 italic">Não informado</span>
                    ) : (
                      <div className="space-y-1">
                        <span className="text-gray-900 font-mono text-sm">
                          {String(field.value)}
                        </span>
                        {field.status === 'invalid' && (
                          <span className="text-xs text-red-600">
                            Formato inválido
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Summary */}
            <div className="bg-blue-50 rounded-lg p-4">
              <h4 className="font-semibold text-blue-800 mb-2">📈 Resumo</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Campos preenchidos:</span>
                  <span className="font-medium ml-2">
                    {fields.filter(f => f.status === 'valid').length}/{fields.length}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Campos obrigatórios:</span>
                  <span className="font-medium ml-2">
                    {fields.filter(f => f.required && f.status === 'valid').length}/{fields.filter(f => f.required).length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default StructuredDataPanel 