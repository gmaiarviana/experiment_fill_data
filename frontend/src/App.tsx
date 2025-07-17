import ChatInterface from './components/ChatInterface'
import './App.css'

function App() {
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
        </header>
        
        <ChatInterface />
      </div>
    </div>
  )
}

export default App 