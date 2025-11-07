import { useParams, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { ArrowLeft } from 'lucide-react'
import BarChart from '../components/BarChart'

const StockDetail = () => {
  const { symbol } = useParams()
  const navigate = useNavigate()
  const [stockData, setStockData] = useState(null)
  const [loading, setLoading] = useState(true)

  // Mock data generation for the stock
  useEffect(() => {
    const mockStockData = {
      symbol: symbol?.toUpperCase(),
      mentionCount: Math.floor(Math.random() * 1000) + 500,
      aiAnalysis: `${symbol?.toUpperCase()} shows strong community interest with significant mention volume on r/wallstreetbets. The stock demonstrates high volatility patterns typical of meme stock behavior, with retail investor sentiment driving price movements. Technical indicators suggest continued momentum trading opportunities.`,
      historicalMentions: [
        { name: 'Jan 10', mentions: Math.floor(Math.random() * 200) + 100 },
        { name: 'Jan 11', mentions: Math.floor(Math.random() * 200) + 100 },
        { name: 'Jan 12', mentions: Math.floor(Math.random() * 200) + 100 },
        { name: 'Jan 13', mentions: Math.floor(Math.random() * 200) + 100 },
        { name: 'Jan 14', mentions: Math.floor(Math.random() * 200) + 100 },
        { name: 'Jan 15', mentions: Math.floor(Math.random() * 200) + 100 },
        { name: 'Jan 16', mentions: Math.floor(Math.random() * 200) + 100 }
      ]
    }

    setTimeout(() => {
      setStockData(mockStockData)
      setLoading(false)
    }, 800)
  }, [symbol])

  if (loading) {
    return (
      <div className="space-y-6 w-full" style={{minWidth: '1200px', margin: '0 auto'}}>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-md transition-colors"
            style={{
              backgroundColor: '#f8f9fa',
              color: '#343a40',
              border: '1px solid #dee2e6'
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#e9ecef'
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = '#f8f9fa'
            }}
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="text-3xl font-bold">{symbol?.toUpperCase()}</h1>
            <p className="text-muted-foreground">Stock Analysis & Details</p>
          </div>
        </div>

        
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="bg-card p-6 rounded-lg border">
            <h2 className="text-xl font-semibold mb-4">AI Analysis</h2>
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="h-4 bg-muted rounded animate-pulse w-full"></div>
                <div className="h-4 bg-muted rounded animate-pulse w-11/12"></div>
                <div className="h-4 bg-muted rounded animate-pulse w-10/12"></div>
                <div className="h-4 bg-muted rounded animate-pulse w-9/12"></div>
              </div>
              <div className="bg-muted p-3 rounded">
                <div className="h-3 bg-gray-300 rounded animate-pulse w-4/5"></div>
              </div>
            </div>
          </div>
          
          <div className="bg-card p-6 rounded-lg border">
            <h2 className="text-xl font-semibold mb-4">Key Information</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Symbol:</span>
                <div className="h-4 w-12 bg-muted rounded animate-pulse"></div>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Positive Mentions:</span>
                <div className="h-4 w-20 bg-muted rounded animate-pulse"></div>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Negative Mentions:</span>
                <div className="h-4 w-20 bg-muted rounded animate-pulse"></div>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Total Mentions:</span>
                <div className="h-4 w-12 bg-muted rounded animate-pulse"></div>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Analysis Date:</span>
                <div className="h-4 w-20 bg-muted rounded animate-pulse"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Mention History Chart */}
        <div className="bg-card p-6 rounded-lg border w-full">
          <h3 className="text-xl font-semibold mb-4">{symbol?.toUpperCase()} Mention History (Last 7 Days)</h3>
          <div style={{ height: '300px' }} className="bg-muted rounded animate-pulse flex items-center justify-center">
            <p className="text-muted-foreground">Loading chart...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 w-full" style={{minWidth: '1200px', margin: '0 auto'}}>
      <div className="flex items-center space-x-4">
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-md transition-colors"
          style={{
            backgroundColor: '#f8f9fa',
            color: '#343a40',
            border: '1px solid #dee2e6'
          }}
          onMouseEnter={(e) => {
            e.target.style.backgroundColor = '#e9ecef'
          }}
          onMouseLeave={(e) => {
            e.target.style.backgroundColor = '#f8f9fa'
          }}
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div>
          <h1 className="text-3xl font-bold">{stockData.symbol}</h1>
          <p className="text-muted-foreground">Stock Analysis & Details</p>
        </div>
      </div>

      
      <div className="grid gap-6 lg:grid-cols-2">
        {/* AI Analysis */}
        <div className="bg-card p-6 rounded-lg border">
          <h2 className="text-xl font-semibold mb-4">AI Analysis</h2>
          <div className="space-y-4">
            <p className="text-sm leading-relaxed">{stockData.aiAnalysis}</p>
          </div>
        </div>
        
        {/* Stock Data Summary */}
        <div className="bg-card p-6 rounded-lg border">
          <h2 className="text-xl font-semibold mb-4">Key Information</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Symbol:</span>
              <span className="text-sm font-medium">{stockData.symbol}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Positive Mentions:</span>
              <span className="text-sm font-medium">Coming Soon</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Negative Mentions:</span>
              <span className="text-sm font-medium">Coming Soon</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Total Mentions:</span>
              <span className="text-sm font-medium">{stockData.mentionCount}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Analysis Date:</span>
              <span className="text-sm font-medium">Jan 15, 2024</span>
            </div>
          </div>
        </div>
      </div>

      {/* Mention History Chart */}
      <BarChart 
        data={stockData.historicalMentions}
        title={`${stockData.symbol} Mention History (Last 7 Days)`}
        enableClick={false}
        height={300}
        barColor="#8b5cf6"
        hoverColor="#7c3aed"
      />
    </div>
  )
}

export default StockDetail