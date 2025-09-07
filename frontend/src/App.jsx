import React, { useState, useEffect } from 'react'
import axios from 'axios'
import SystemForm from './components/SystemForm'
import LocationMap from './components/LocationMap'
import ResultsDashboard from './components/ResultsDashboard'
import './App.css'

function App() {
  const [systemConfig, setSystemConfig] = useState({
    location: {
      latitude: 51.5074,
      longitude: -0.1278,
      altitude: 11
    },
    array: {
      tilt: 35,
      azimuth: 180,
      stringing: {
        modules_per_string: 20,
        strings_per_inverter: 10
      }
    },
    module_params: {
      power: 400,
      temp_coefficient: -0.35
    },
    inverter_params: {
      power: 50000,
      efficiency: 96.5
    },
    loss_params: {
      soiling: 2.0,
      shading: 1.0,
      snow: 0.5,
      mismatch: 2.0,
      wiring: 2.0,
      connections: 0.5,
      lid: 1.5,
      nameplate: 1.0,
      age: 0.0,
      availability: 3.0
    }
  })

  const [predictionResults, setPredictionResults] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleLocationChange = (newLocation) => {
    setSystemConfig(prev => ({
      ...prev,
      location: { ...prev.location, ...newLocation }
    }))
  }

  const handleConfigChange = (section, updates) => {
    setSystemConfig(prev => ({
      ...prev,
      [section]: { ...prev[section], ...updates }
    }))
  }

  const generatePrediction = async () => {
    setIsLoading(true)
    setError(null)
    setPredictionResults(null)

    try {
      const response = await axios.post('/api/v1/predict', systemConfig)
      setPredictionResults(response.data)
    } catch (err) {
      console.error('Prediction error:', err)
      setError(err.response?.data?.error || 'Failed to generate prediction')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-orange-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-orange-400 to-yellow-500 rounded-lg">
                <span className="text-white text-xl">☀</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Heliotelligence</h1>
                <p className="text-sm text-gray-500">Solar Energy Prediction Platform</p>
              </div>
            </div>
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <span>⚡</span>
                <span>Physics-Based Predictions</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <span>📊</span>
                <span>UK Solar Market</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Configuration Panel */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center space-x-2 mb-4">
                <span className="text-blue-600">⚙️</span>
                <h2 className="text-lg font-semibold text-gray-900">System Configuration</h2>
              </div>

              {/* Location Section */}
              <div className="mb-6">
                <LocationMap
                  location={systemConfig.location}
                  onLocationChange={handleLocationChange}
                />
              </div>

              {/* System Form */}
              <SystemForm
                config={systemConfig}
                onConfigChange={handleConfigChange}
                onGenerate={generatePrediction}
                isLoading={isLoading}
              />
            </div>
          </div>

          {/* Results Panel */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center space-x-2 mb-4">
                <span className="text-green-600">📊</span>
                <h2 className="text-lg font-semibold text-gray-900">Energy Prediction Results</h2>
              </div>

              <ResultsDashboard
                results={predictionResults}
                isLoading={isLoading}
                error={error}
              />
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-gray-600">
            <p className="font-medium">Heliotelligence - Physics-based Solar Energy Prediction Platform</p>
            <p className="text-sm mt-1">Powered by PVGIS weather data and advanced solar modeling</p>
            <div className="flex items-center justify-center space-x-4 mt-2 text-xs">
              <span>🌍 UK Solar Market Optimized</span>
              <span>⚡ Real-time Weather Integration</span>
              <span>🔬 Advanced Physics Engine</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App

