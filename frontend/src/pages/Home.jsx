import { useState, useEffect } from 'react'
import BarChart from '../components/BarChart'

const Home = () => {
  const [latestBatchData, setLatestBatchData] = useState([])
  const [totalMentions, setTotalMentions] = useState(0)
  const [batchInfo, setBatchInfo] = useState(null)
  const [loading, setLoading] = useState(true)

  // Fetch real data from API
  useEffect(() => {
    const fetchHomeData = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/home-data')

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
        setBatchInfo(apiResponse.batch_info || null)
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
          <h1 className="text-3xl md:text-5xl lg:text-5xl font-bold">Latest Top 10 Stocks</h1>
          <p className="text-muted-foreground mt-2">Most recent completed 3-day batch results <span className="text-blue-600 font-medium">(click on any bar to see a report)</span></p>
        </div>
        
        <div className="bg-card p-6 rounded-lg border">
          <h3 className="text-base sm:text-xl font-semibold mb-4">Top 10 Most Mentioned Stocks (Latest Batch)</h3>
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
          <h1 className="text-xl md:text-2xl lg:text-5xl font-bold">Latest Top 10 Stocks</h1>
          <p className="text-muted-foreground mt-2">Most recent completed 3-day batch results <span className="text-blue-600 font-medium">(click on any bar to see a report)</span></p>
        </div>

        <BarChart
          data={[]}
          title="Top 10 Most Mentioned Stocks (Latest Batch)"
          enableClick={false}
          height={400}
          barColor="var(--chart-home)"
          hoverColor="var(--chart-home-hover)"
        />

        <div className="bg-card p-4 rounded-lg border">
          <h3 className="font-semibold mb-2 text-center">Batch Information</h3>
          <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1 text-left">
            <li>There is currently no data, waiting for newest 3 day batch to complete.</li>
          </ul>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-3xl md:text-5xl lg:text-5xl font-bold">Latest Top 10 Stocks</h1>
        <p className="text-muted-foreground mt-2">Most recent completed 3-day batch results <span className="text-blue-600 font-medium">(click on any bar to see a report)</span></p>
      </div>

      
      <BarChart 
        data={latestBatchData}
        title="Top 10 Most Mentioned Stocks (Latest Batch)"
        enableClick={true}
        height={400}
        barColor="var(--chart-home)"
        hoverColor="var(--chart-home-hover)"
      />

      <div className="bg-card p-4 rounded-lg border">
        <h3 className="font-semibold mb-2 text-center">Batch Information</h3>
        <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1 text-left">
          <li>Data period: {batchInfo ?
            `${new Date(batchInfo.batch_start).toLocaleString()} - ${new Date(batchInfo.batch_end).toLocaleString()}`
            : 'Latest completed 3-day batch'}</li>
          <li>Total mentions: {totalMentions.toLocaleString()}</li>
          <li>Analysis reports available for each ticker</li>
        </ul>
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