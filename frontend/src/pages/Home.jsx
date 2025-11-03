import { useState, useEffect } from 'react'
import BarChart from '../components/BarChart'

const Home = () => {
  const [latestBatchData, setLatestBatchData] = useState([])
  const [totalMentions, setTotalMentions] = useState(0)
  const [loading, setLoading] = useState(true)

  // Fetch real data from API
  useEffect(() => {
    const fetchHomeData = async () => {
      try {
        setLoading(true)
        const response = await fetch('http://localhost:8000/api/home-data')

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const apiResponse = await response.json()

        // Transform API data to match BarChart component format
        // API returns: { status: 200, data: [...], total_mentions: ... }
        const transformedData = apiResponse.data.map(ticker => ({
          name: ticker.ticker,
          mentions: ticker.mentions
        }))

        setLatestBatchData(transformedData)
        setTotalMentions(apiResponse.total_mentions || 0)
      } catch (error) {
        console.error('Failed to fetch home data:', error)
        // Fallback to empty array on error
        setLatestBatchData([])
      } finally {
        setLoading(false)
      }
    }

    fetchHomeData()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold">Latest Top 10 Stocks</h1>
          <p className="text-muted-foreground mt-2">Most recent completed 3-day batch results</p>
        </div>
        
        <div className="bg-card p-6 rounded-lg border">
          <h3 className="text-xl font-semibold mb-4">Top 10 Most Mentioned Stocks (Latest Batch)</h3>
          <div className="h-96 bg-muted rounded animate-pulse flex items-center justify-center">
            <p className="text-muted-foreground">Loading chart...</p>
          </div>
        </div>

        <div className="bg-card p-4 rounded-lg border">
          <h3 className="font-semibold mb-2">Batch Information</h3>
          <div className="text-sm text-muted-foreground space-y-1">
            <div className="h-4 bg-muted rounded animate-pulse mb-1"></div>
            <div className="h-4 bg-muted rounded animate-pulse mb-1 w-4/5"></div>
            <div className="h-4 bg-muted rounded animate-pulse mb-1 w-3/4"></div>
            <div className="h-4 bg-muted rounded animate-pulse w-5/6"></div>
          </div>
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-4 rounded-lg">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            ℹ️ This data represents completed analysis from the latest batch. Click any bar to view detailed analysis.
          </p>
        </div>
      </div>
    )
  }

  // Show message if no data available
  if (latestBatchData.length === 0) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold">Latest Top 10 Stocks</h1>
          <p className="text-muted-foreground mt-2">Most recent completed 3-day batch results</p>
        </div>

        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-8 rounded-lg text-center">
          <h3 className="text-xl font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
            📊 More data required
          </h3>
          <p className="text-sm text-yellow-600 dark:text-yellow-400 mt-2">
            Waiting for the next 3-day batch to complete data collection
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold">Latest Top 10 Stocks</h1>
        <p className="text-muted-foreground mt-2">Most recent completed 3-day batch results</p>
      </div>

      
      <BarChart 
        data={latestBatchData}
        title="Top 10 Most Mentioned Stocks (Latest Batch)"
        enableClick={true}
        height={400}
        barColor="#3b82f6"
        hoverColor="#1d4ed8"
      />

      <div className="bg-card p-4 rounded-lg border">
        <h3 className="font-semibold mb-2">Batch Information</h3>
        <div className="text-sm text-muted-foreground space-y-1">
          <p>• Data period: Last completed 3-day batch (6-3 days ago)</p>
          <p>• Top {latestBatchData.length} most mentioned tickers</p>
          <p>• Total mentions: {totalMentions.toLocaleString()}</p>
          <p>• Analysis reports available for each ticker</p>
        </div>
      </div>

      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-4 rounded-lg">
        <p className="text-sm text-blue-800 dark:text-blue-200">
          ℹ️ This data represents completed analysis from the latest batch. Click any bar to view detailed analysis.
        </p>
      </div>
    </div>
  )
}

export default Home