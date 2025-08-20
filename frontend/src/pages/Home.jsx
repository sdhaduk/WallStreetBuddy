import { useState, useEffect } from 'react'
import BarChart from '../components/BarChart'

const Home = () => {
  const [latestBatchData, setLatestBatchData] = useState([])
  const [loading, setLoading] = useState(true)

  // Mock data for development - replace with API call later
  useEffect(() => {
    const mockLatestBatch = [
      { name: 'AAPL', mentions: 1250 },
      { name: 'TSLA', mentions: 890 },
      { name: 'NVDA', mentions: 750 },
      { name: 'AMD', mentions: 620 },
      { name: 'MSFT', mentions: 580 },
      { name: 'GOOGL', mentions: 450 },
      { name: 'AMZN', mentions: 380 },
      { name: 'META', mentions: 320 },
      { name: 'NFLX', mentions: 280 },
      { name: 'INTC', mentions: 220 }
    ]

    // Simulate API loading
    setTimeout(() => {
      setLatestBatchData(mockLatestBatch)
      setLoading(false)
    }, 500)
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
          <p>• Batch completed: 3 days ago</p>
          <p>• Total posts analyzed: 2,341</p>
          <p>• Total mentions: 15,420</p>
          <p>• Analysis period: Jan 12-15, 2024</p>
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