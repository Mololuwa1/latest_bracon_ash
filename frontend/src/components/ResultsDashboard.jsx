import { useEffect, useRef } from 'react'
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  BarElement, 
  LineElement,
  PointElement,
  Title, 
  Tooltip, 
  Legend,
  ArcElement
} from 'chart.js'
import { Bar, Line, Doughnut } from 'react-chartjs-2'
import { TrendingUp, Zap, Calendar, AlertTriangle, Loader2, BarChart3 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
)

const ResultsDashboard = ({ results, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <p className="text-gray-600">Generating energy prediction...</p>
        <p className="text-sm text-gray-500">Fetching weather data and running physics simulation</p>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4 text-gray-500">
        <BarChart3 className="w-12 h-12" />
        <p className="text-lg font-medium">No prediction results yet</p>
        <p className="text-sm text-center">
          Configure your solar system parameters and click "Generate Energy Prediction" to see detailed results
        </p>
      </div>
    )
  }

  // Prepare monthly energy chart data
  const monthlyChartData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    datasets: [
      {
        label: 'Monthly Energy Production (kWh)',
        data: results.monthly_energy_kwh,
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
        borderRadius: 4,
      }
    ]
  }

  const monthlyChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: true,
        text: 'Monthly Energy Production'
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Energy (kWh)'
        }
      }
    }
  }

  // Prepare loss breakdown chart data
  const lossData = results.loss_breakdown_kwh
  const lossLabels = Object.keys(lossData).map(key => 
    key.replace('_loss_kwh', '').replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
  )
  const lossValues = Object.values(lossData)

  const lossChartData = {
    labels: lossLabels,
    datasets: [
      {
        data: lossValues,
        backgroundColor: [
          '#ef4444', '#f97316', '#eab308', '#84cc16', '#22c55e',
          '#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6', '#d946ef',
          '#ec4899'
        ],
        borderWidth: 2,
        borderColor: '#ffffff'
      }
    ]
  }

  const lossChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          boxWidth: 12,
          padding: 8,
          font: {
            size: 11
          }
        }
      },
      title: {
        display: true,
        text: 'Energy Loss Breakdown'
      }
    }
  }

  // Calculate key metrics
  const totalLosses = Object.values(lossData).reduce((sum, loss) => sum + loss, 0)
  const systemEfficiency = ((results.annual_energy_kwh / (results.annual_energy_kwh + totalLosses)) * 100).toFixed(1)
  const peakMonth = results.monthly_energy_kwh.indexOf(Math.max(...results.monthly_energy_kwh))
  const peakMonthName = monthlyChartData.labels[peakMonth]

  return (
    <div className="space-y-6">
      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Annual Energy Production</CardTitle>
            <Zap className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {results.annual_energy_kwh.toLocaleString()} kWh
            </div>
            <p className="text-xs text-muted-foreground">
              Estimated annual yield
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Performance Ratio</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {(results.performance_ratio * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              System efficiency metric
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Peak Production Month</CardTitle>
            <Calendar className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {peakMonthName}
            </div>
            <p className="text-xs text-muted-foreground">
              {Math.max(...results.monthly_energy_kwh).toFixed(0)} kWh
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total System Losses</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {totalLosses.toFixed(0)} kWh
            </div>
            <p className="text-xs text-muted-foreground">
              {systemEfficiency}% system efficiency
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Energy Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Energy Production</CardTitle>
          <CardDescription>
            Seasonal variation in energy output throughout the year
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <Bar data={monthlyChartData} options={monthlyChartOptions} />
          </div>
        </CardContent>
      </Card>

      {/* Loss Breakdown Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Energy Loss Analysis</CardTitle>
          <CardDescription>
            Breakdown of system losses affecting energy production
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <Doughnut data={lossChartData} options={lossChartOptions} />
          </div>
        </CardContent>
      </Card>

      {/* Detailed Loss Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Loss Breakdown</CardTitle>
          <CardDescription>
            Individual loss components and their impact on energy production
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Loss Type</th>
                  <th className="text-right py-2">Energy Loss (kWh)</th>
                  <th className="text-right py-2">Percentage of Total</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(lossData).map(([key, value]) => {
                  const percentage = ((value / totalLosses) * 100).toFixed(1)
                  const displayName = key.replace('_loss_kwh', '').replace('_', ' ')
                    .replace(/\b\w/g, l => l.toUpperCase())
                  
                  return (
                    <tr key={key} className="border-b">
                      <td className="py-2">{displayName}</td>
                      <td className="text-right py-2">{value.toFixed(1)}</td>
                      <td className="text-right py-2">{percentage}%</td>
                    </tr>
                  )
                })}
                <tr className="border-b-2 border-gray-400 font-semibold">
                  <td className="py-2">Total Losses</td>
                  <td className="text-right py-2">{totalLosses.toFixed(1)}</td>
                  <td className="text-right py-2">100.0%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ResultsDashboard

