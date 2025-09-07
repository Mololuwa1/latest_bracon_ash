import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix for default markers in Leaflet with Vite
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const LocationMap = ({ latitude, longitude, onLocationChange }) => {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markerRef = useRef(null)

  useEffect(() => {
    if (!mapRef.current) return

    // Initialize map
    const map = L.map(mapRef.current).setView([latitude, longitude], 10)
    mapInstanceRef.current = map

    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map)

    // Add marker
    const marker = L.marker([latitude, longitude], {
      draggable: true
    }).addTo(map)
    markerRef.current = marker

    // Handle marker drag
    marker.on('dragend', function(e) {
      const position = e.target.getLatLng()
      onLocationChange(position.lat, position.lng)
    })

    // Handle map click
    map.on('click', function(e) {
      const { lat, lng } = e.latlng
      marker.setLatLng([lat, lng])
      onLocationChange(lat, lng)
    })

    // Cleanup function
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

  // Update marker position when props change
  useEffect(() => {
    if (markerRef.current && mapInstanceRef.current) {
      markerRef.current.setLatLng([latitude, longitude])
      mapInstanceRef.current.setView([latitude, longitude], mapInstanceRef.current.getZoom())
    }
  }, [latitude, longitude])

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-700">
        Click or drag marker to set location
      </label>
      <div 
        ref={mapRef} 
        className="w-full h-64 rounded-lg border border-gray-300 overflow-hidden"
        style={{ minHeight: '256px' }}
      />
      <p className="text-xs text-gray-500">
        Current: {latitude.toFixed(4)}°, {longitude.toFixed(4)}°
      </p>
    </div>
  )
}

export default LocationMap

