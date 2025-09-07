import { useState } from 'react'
import { MapPin, Settings, Zap, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import LocationMap from './LocationMap'
import axios from 'axios'

const SystemForm = ({ onPredictionStart, onPredictionComplete, isLoading }) => {
  const [formData, setFormData] = useState({
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

  const [error, setError] = useState(null)

  const handleInputChange = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: parseFloat(value) || 0
      }
    }))
  }

  const handleNestedInputChange = (section, subsection, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [subsection]: {
          ...prev[section][subsection],
          [field]: parseFloat(value) || 0
        }
      }
    }))
  }

  const handleLocationChange = (lat, lng) => {
    setFormData(prev => ({
      ...prev,
      location: {
        ...prev.location,
        latitude: lat,
        longitude: lng
      }
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    onPredictionStart()

    try {
      // Use port 8002 where our updated API is running
      const response = await axios.post('/api/v1/predict', formData, {
        timeout: 60000 // 60 second timeout
      })
      
      onPredictionComplete(response.data)
    } catch (err) {
      console.error('Prediction error:', err)
      setError(
        err.response?.data?.error || 
        err.message || 
        'Failed to generate prediction. Please check your inputs and try again.'
      )
      onPredictionComplete(null)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Location Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MapPin className="w-5 h-5" />
            <span>Location</span>
          </CardTitle>
          <CardDescription>
            Specify the geographic location of your solar installation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="latitude">Latitude (°)</Label>
              <Input
                id="latitude"
                type="number"
                step="0.0001"
                value={formData.location.latitude}
                onChange={(e) => handleInputChange('location', 'latitude', e.target.value)}
                placeholder="51.5074"
              />
            </div>
            <div>
              <Label htmlFor="longitude">Longitude (°)</Label>
              <Input
                id="longitude"
                type="number"
                step="0.0001"
                value={formData.location.longitude}
                onChange={(e) => handleInputChange('location', 'longitude', e.target.value)}
                placeholder="-0.1278"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="altitude">Altitude (m)</Label>
            <Input
              id="altitude"
              type="number"
              value={formData.location.altitude}
              onChange={(e) => handleInputChange('location', 'altitude', e.target.value)}
              placeholder="11"
            />
          </div>
          <LocationMap
            latitude={formData.location.latitude}
            longitude={formData.location.longitude}
            onLocationChange={handleLocationChange}
          />
        </CardContent>
      </Card>

      {/* Array Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="w-5 h-5" />
            <span>Array Configuration</span>
          </CardTitle>
          <CardDescription>
            Configure your solar panel array geometry and layout
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="tilt">Tilt Angle (°)</Label>
              <Input
                id="tilt"
                type="number"
                min="0"
                max="90"
                value={formData.array.tilt}
                onChange={(e) => handleInputChange('array', 'tilt', e.target.value)}
                placeholder="35"
              />
            </div>
            <div>
              <Label htmlFor="azimuth">Azimuth (°)</Label>
              <Input
                id="azimuth"
                type="number"
                min="0"
                max="360"
                value={formData.array.azimuth}
                onChange={(e) => handleInputChange('array', 'azimuth', e.target.value)}
                placeholder="180"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="modules_per_string">Modules per String</Label>
              <Input
                id="modules_per_string"
                type="number"
                min="1"
                value={formData.array.stringing.modules_per_string}
                onChange={(e) => handleNestedInputChange('array', 'stringing', 'modules_per_string', e.target.value)}
                placeholder="20"
              />
            </div>
            <div>
              <Label htmlFor="strings_per_inverter">Strings per Inverter</Label>
              <Input
                id="strings_per_inverter"
                type="number"
                min="1"
                value={formData.array.stringing.strings_per_inverter}
                onChange={(e) => handleNestedInputChange('array', 'stringing', 'strings_per_inverter', e.target.value)}
                placeholder="10"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Module & Inverter Parameters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="w-5 h-5" />
            <span>Equipment Specifications</span>
          </CardTitle>
          <CardDescription>
            Specify your solar modules and inverter parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="module_power">Module Power (W)</Label>
              <Input
                id="module_power"
                type="number"
                min="1"
                value={formData.module_params.power}
                onChange={(e) => handleInputChange('module_params', 'power', e.target.value)}
                placeholder="400"
              />
            </div>
            <div>
              <Label htmlFor="temp_coefficient">Temperature Coefficient (%/°C)</Label>
              <Input
                id="temp_coefficient"
                type="number"
                step="0.01"
                value={formData.module_params.temp_coefficient}
                onChange={(e) => handleInputChange('module_params', 'temp_coefficient', e.target.value)}
                placeholder="-0.35"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="inverter_power">Inverter Power (W)</Label>
              <Input
                id="inverter_power"
                type="number"
                min="1"
                value={formData.inverter_params.power}
                onChange={(e) => handleInputChange('inverter_params', 'power', e.target.value)}
                placeholder="50000"
              />
            </div>
            <div>
              <Label htmlFor="inverter_efficiency">Inverter Efficiency (%)</Label>
              <Input
                id="inverter_efficiency"
                type="number"
                min="80"
                max="100"
                step="0.1"
                value={formData.inverter_params.efficiency}
                onChange={(e) => handleInputChange('inverter_params', 'efficiency', e.target.value)}
                placeholder="96.5"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Losses */}
      <Card>
        <CardHeader>
          <CardTitle>System Losses (%)</CardTitle>
          <CardDescription>
            Configure expected system losses for accurate predictions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="soiling">Soiling</Label>
              <Input
                id="soiling"
                type="number"
                min="0"
                max="20"
                step="0.1"
                value={formData.loss_params.soiling}
                onChange={(e) => handleInputChange('loss_params', 'soiling', e.target.value)}
                placeholder="2.0"
              />
            </div>
            <div>
              <Label htmlFor="shading">Shading</Label>
              <Input
                id="shading"
                type="number"
                min="0"
                max="50"
                step="0.1"
                value={formData.loss_params.shading}
                onChange={(e) => handleInputChange('loss_params', 'shading', e.target.value)}
                placeholder="1.0"
              />
            </div>
            <div>
              <Label htmlFor="mismatch">Module Mismatch</Label>
              <Input
                id="mismatch"
                type="number"
                min="0"
                max="10"
                step="0.1"
                value={formData.loss_params.mismatch}
                onChange={(e) => handleInputChange('loss_params', 'mismatch', e.target.value)}
                placeholder="2.0"
              />
            </div>
            <div>
              <Label htmlFor="wiring">DC Wiring</Label>
              <Input
                id="wiring"
                type="number"
                min="0"
                max="10"
                step="0.1"
                value={formData.loss_params.wiring}
                onChange={(e) => handleInputChange('loss_params', 'wiring', e.target.value)}
                placeholder="2.0"
              />
            </div>
            <div>
              <Label htmlFor="availability">Availability</Label>
              <Input
                id="availability"
                type="number"
                min="0"
                max="10"
                step="0.1"
                value={formData.loss_params.availability}
                onChange={(e) => handleInputChange('loss_params', 'availability', e.target.value)}
                placeholder="3.0"
              />
            </div>
            <div>
              <Label htmlFor="lid">Light-Induced Degradation</Label>
              <Input
                id="lid"
                type="number"
                min="0"
                max="5"
                step="0.1"
                value={formData.loss_params.lid}
                onChange={(e) => handleInputChange('loss_params', 'lid', e.target.value)}
                placeholder="1.5"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Submit Button */}
      <Button 
        type="submit" 
        className="w-full h-12 text-lg"
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            Generating Prediction...
          </>
        ) : (
          <>
            <Zap className="w-5 h-5 mr-2" />
            Generate Energy Prediction
          </>
        )}
      </Button>
    </form>
  )
}

export default SystemForm

