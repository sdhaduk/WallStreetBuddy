import { useParams, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { ArrowLeft, Maximize2, X } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import BarChart from '../components/BarChart'

const StockDetail = () => {
  const { symbol } = useParams()
  const navigate = useNavigate()
  const [stockData, setStockData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showAnalysisModal, setShowAnalysisModal] = useState(false)

  // Fetch real stock data from API
  useEffect(() => {
    const fetchStockData = async () => {
      if (!symbol) return

      try {
        setLoading(true)
        const response = await fetch(`http://localhost:8000/api/stock/${symbol}`)

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const result = await response.json()

        if (result.status === 200) {
          setStockData(result.data)
        } else {
          throw new Error(result.message || 'Failed to fetch stock data')
        }
      } catch (error) {
        console.error('Error fetching stock data:', error)
        // Set error state with fallback data
        setStockData({
          symbol: symbol?.toUpperCase(),
          total_mentions: 0,
          positive_mentions: null,
          negative_mentions: null,
          analysis_date: null,
          ai_analysis: 'Unable to load analysis. Please try again later.',
          historical_mentions: []
        })
      } finally {
        setLoading(false)
      }
    }

    fetchStockData()
  }, [symbol])

  // Handle keyboard events for modal
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && showAnalysisModal) {
        setShowAnalysisModal(false)
      }
    }

    if (showAnalysisModal) {
      document.addEventListener('keydown', handleKeyDown)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'auto'
    }
  }, [showAnalysisModal])

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

  // Handle case when stockData is null or empty
  if (!stockData) {
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
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="text-3xl font-bold">{symbol?.toUpperCase()}</h1>
            <p className="text-muted-foreground">Stock Analysis & Details</p>
          </div>
        </div>
        <div className="bg-card p-6 rounded-lg border text-center">
          <p className="text-lg">Unable to load stock data. Please try again later.</p>
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
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">AI Analysis <span className="text-xs text-red-600 font-medium">(This is not financial advice)</span></h2>
            <button
              onClick={() => setShowAnalysisModal(true)}
              className="flex items-center space-x-1 px-3 py-1 text-sm rounded-md transition-colors"
              style={{
                backgroundColor: '#ffffff',
                color: '#374151',
                border: '1px solid #d1d5db'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#f3f4f6'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#ffffff'}
              title="View Full Report"
            >
              <Maximize2 className="h-3 w-3" />
              <span>View Full</span>
            </button>
          </div>
          <div
            className="relative cursor-pointer group"
            onClick={() => setShowAnalysisModal(true)}
          >
            <div
              className="text-sm leading-relaxed overflow-hidden"
              style={{
                height: '200px',
                WebkitLineClamp: 10,
                WebkitBoxOrient: 'vertical',
                display: '-webkit-box'
              }}
            >
              <style>
                {`
                  .card-markdown-content * {
                    color: black !important;
                    font-size: 0.875rem !important;
                  }
                  .card-markdown-content ul li::marker,
                  .card-markdown-content ol li::marker {
                    color: black !important;
                  }
                  .card-markdown-content h1,
                  .card-markdown-content h2,
                  .card-markdown-content h3,
                  .card-markdown-content h4 {
                    font-size: 1rem !important;
                    font-weight: 600 !important;
                    margin: 0.5rem 0 !important;
                  }
                `}
              </style>
              <div className="prose max-w-none text-left card-markdown-content">
                <ReactMarkdown>
                  {stockData.ai_analysis || 'No analysis available'}
                </ReactMarkdown>
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-white to-transparent pointer-events-none"></div>
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
              <span className="text-sm font-medium">{stockData.total_mentions}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Analysis Date:</span>
              <span className="text-sm font-medium">
                {stockData.analysis_date ? new Date(stockData.analysis_date).toLocaleDateString() : 'Not available'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Mention History Chart */}
      <BarChart
        data={stockData.historical_mentions}
        title={`${stockData.symbol} Mention History (Last 7 Days)`}
        enableClick={false}
        height={300}
        barColor="#E15759"
        hoverColor="#7c3aed"
      />

      {/* AI Analysis Modal */}
      {showAnalysisModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-2xl font-semibold">AI Analysis - {stockData.symbol}</h2>
              <button
                onClick={() => setShowAnalysisModal(false)}
                className="p-2 rounded-full transition-colors"
                style={{
                  backgroundColor: '#ffffff',
                  color: '#374151',
                  border: '1px solid #d1d5db'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#f3f4f6'}
                onMouseLeave={(e) => e.target.style.backgroundColor = '#ffffff'}
                title="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)] modal-content" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
              <style>
                {`
                  .markdown-content * {
                    color: black !important;
                  }
                  .markdown-content ul li::marker,
                  .markdown-content ol li::marker {
                    color: black !important;
                  }
                  .modal-content::-webkit-scrollbar {
                    display: none;
                  }
                `}
              </style>
              <div className="prose max-w-none text-left markdown-content">
                <ReactMarkdown>
                  {stockData.ai_analysis || 'No analysis available'}
                </ReactMarkdown>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t bg-gray-50">
              <span className="text-sm text-gray-600">
                Analysis Date: {stockData.analysis_date ? new Date(stockData.analysis_date).toLocaleDateString() : 'Not available'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default StockDetail