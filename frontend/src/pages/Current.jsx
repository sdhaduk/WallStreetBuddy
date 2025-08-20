import { useState, useEffect } from 'react'
import BarChart from '../components/BarChart'
import { RefreshCw } from 'lucide-react'

const Current = () => {
  const [currentData, setCurrentData] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  // Mock data function to simulate changing values
  const generateMockCurrentData = () => {
    const baseData = [
      { name: 'AAPL', mentions: 890 },
      { name: 'TSLA', mentions: 720 },
      { name: 'NVDA', mentions: 650 },
      { name: 'AMD', mentions: 480 },
      { name: 'MSFT', mentions: 420 },
      { name: 'GOOGL', mentions: 380 },
      { name: 'AMZN', mentions: 340 },
      { name: 'META', mentions: 290 },
      { name: 'NFLX', mentions: 250 },
      { name: 'INTC', mentions: 180 }
    ]

    // Add some randomness to simulate live updating
    return baseData.map(item => ({
      ...item,
      mentions: item.mentions + Math.floor(Math.random() * 20) - 10
    }))
  }

  // Fetch current data
  const fetchCurrentData = () => {
    setLoading(true)
    // Simulate API call
    setTimeout(() => {
      setCurrentData(generateMockCurrentData())
      setLastUpdated(new Date())
      setLoading(false)
    }, 500)
  }

  // Initial load
  useEffect(() => {
    fetchCurrentData()
  }, [])

  // Polling every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchCurrentData()
    }, 30000) // 30 seconds

    return () => clearInterval(interval)
  }, [])

  if (loading && !currentData.length) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold">Live Count</h1>
          <p className="text-muted-foreground mt-2">Live count of mentions in current 3-day window</p>
        </div>

        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <RefreshCw className="h-4 w-4" />
            <span>Loading...</span>
          </div>
          <button
            disabled={true}
            className="px-3 py-1 text-sm rounded-md transition-colors disabled:opacity-50"
            style={{
              backgroundColor: '#f8f9fa',
              color: '#343a40',
              border: '1px solid #dee2e6'
            }}
          >
            Refresh Now
          </button>
        </div>
        
        <div className="bg-card p-6 rounded-lg border">
          <h3 className="text-xl font-semibold mb-4">Current Top 10 Mentions (Live Count)</h3>
          <div className="h-96 bg-muted rounded animate-pulse flex items-center justify-center">
            <p className="text-muted-foreground">Loading chart...</p>
          </div>
        </div>

        <div className="bg-card p-4 rounded-lg border">
          <h3 className="font-semibold mb-2">Current Window Information</h3>
          <div className="text-sm text-muted-foreground space-y-1">
            <div className="h-4 bg-muted rounded animate-pulse mb-1"></div>
            <div className="h-4 bg-muted rounded animate-pulse mb-1 w-4/5"></div>
            <div className="h-4 bg-muted rounded animate-pulse mb-1 w-3/4"></div>
            <div className="h-4 bg-muted rounded animate-pulse w-5/6"></div>
          </div>
        </div>

        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-4 rounded-lg">
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            ℹ️ This data represents live counting in progress. Charts are not clickable as analysis is not yet complete.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold">Live Count</h1>
        <p className="text-muted-foreground mt-2">Live count of mentions in current 3-day window</p>
      </div>

      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>
            Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Loading...'}
          </span>
        </div>
        <button
          onClick={fetchCurrentData}
          disabled={loading}
          className="px-3 py-1 text-sm rounded-md transition-colors disabled:opacity-50"
          style={{
            backgroundColor: '#f8f9fa',
            color: '#343a40',
            border: '1px solid #dee2e6'
          }}
          onMouseEnter={(e) => {
            if (!loading) {
              e.target.style.backgroundColor = '#e9ecef'
            }
          }}
          onMouseLeave={(e) => {
            if (!loading) {
              e.target.style.backgroundColor = '#f8f9fa'
            }
          }}
        >
          Refresh Now
        </button>
      </div>
      
      <BarChart 
        data={currentData}
        title="Current Top 10 Mentions (Live Count)"
        enableClick={false}
        height={400}
        barColor="#10b981"
        hoverColor="#059669"
      />

      <div className="bg-card p-4 rounded-lg border">
        <h3 className="font-semibold mb-2">Current Window Information</h3>
        <div className="text-sm text-muted-foreground space-y-1">
          <p>• Window started: 2 days ago</p>
          <p>• Posts analyzed so far: 1,205</p>
          <p>• Total mentions: 8,430</p>
          <p>• Next update: Automatic refresh every 30 seconds</p>
        </div>
      </div>

      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-4 rounded-lg">
        <p className="text-sm text-yellow-800 dark:text-yellow-200">
          ℹ️ This data represents live counting in progress. Charts are not clickable as analysis is not yet complete.
        </p>
      </div>
    </div>
  )
}

export default Current