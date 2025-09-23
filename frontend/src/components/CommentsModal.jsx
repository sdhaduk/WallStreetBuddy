import { useState } from 'react'
import { X, Search, MessageSquare, Calendar, Hash } from 'lucide-react'

const CommentsModal = ({ isOpen, onClose }) => {
  const [tickers, setTickers] = useState('')
  const [timeValue, setTimeValue] = useState(3)
  const [timeUnit, setTimeUnit] = useState('days')
  const [comments, setComments] = useState([])
  const [loading, setLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  // Mock data for skeleton functionality
  const mockComments = [
    {
      id: '1',
      body: 'Just bought more AAPL shares today. This dip is a great opportunity! 🚀',
      subreddit: 'stocks',
      timestamp: '2024-01-15T14:30:00Z',
      tickers: ['AAPL']
    },
    {
      id: '2',
      body: 'TSLA to the moon! Elon knows what he\'s doing. Also keeping an eye on NVDA for AI plays.',
      subreddit: 'wallstreetbets',
      timestamp: '2024-01-15T13:45:00Z',
      tickers: ['TSLA', 'NVDA']
    },
    {
      id: '3',
      body: 'Value investing approach: looking at SPY for long-term holds. Steady growth is key.',
      subreddit: 'ValueInvesting',
      timestamp: '2024-01-15T12:20:00Z',
      tickers: ['SPY']
    },
    {
      id: '4',
      body: 'AMD crushing it with their new chips. Competition with NVDA is heating up!',
      subreddit: 'stocks',
      timestamp: '2024-01-15T11:15:00Z',
      tickers: ['AMD', 'NVDA']
    },
    {
      id: '5',
      body: 'GOOGL earnings coming up. Expecting good numbers from cloud and advertising.',
      subreddit: 'stocks',
      timestamp: '2024-01-15T10:30:00Z',
      tickers: ['GOOGL']
    }
  ]

  const timeUnits = [
    { value: 'minutes', label: 'Minutes', max: 10080 },
    { value: 'hours', label: 'Hours', max: 168 },
    { value: 'days', label: 'Days', max: 7 }
  ]

  // Validation logic (same as Current.jsx)
  const currentUnit = timeUnits.find(unit => unit.value === timeUnit)
  const maxValue = currentUnit ? currentUnit.max : 7
  const numericTimeValue = parseInt(timeValue) || 0
  const isValidValue = numericTimeValue >= 1 && numericTimeValue <= maxValue && timeValue !== ''

  const getTimeDisplayText = () => {
    if (timeValue === '' || numericTimeValue < 1) return 'Enter a value'
    if (numericTimeValue > maxValue) return `Max ${maxValue} ${timeUnit}`
    return `showing last ${numericTimeValue} ${numericTimeValue === 1 ? timeUnit.slice(0, -1) : timeUnit}`
  }

  const handleSearch = () => {
    setLoading(true)
    setHasSearched(true)

    // Simulate API call
    setTimeout(() => {
      // Filter mock data based on tickers input
      if (tickers.trim()) {
        const tickerList = tickers.split(',').map(t => t.trim().toUpperCase())
        const filtered = mockComments.filter(comment =>
          comment.tickers.some(ticker => tickerList.includes(ticker))
        )
        setComments(filtered)
      } else {
        // Show all comments if no tickers specified
        setComments(mockComments)
      }
      setLoading(false)
    }, 1000)
  }

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString()
  }


  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-2">
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 w-[95vw] h-[95vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-gray-700 dark:text-gray-300" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">View Processed Comments</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md transition-colors"
            style={{
              backgroundColor: '#f3f4f6',
              border: '1px solid #d1d5db',
              color: '#374151',
              padding: '8px',
              fontSize: 'inherit',
              fontWeight: 'normal'
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = '#e5e7eb'
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = '#f3f4f6'
            }}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Search Form */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Ticker Input */}
            <div className="w-full lg:w-96">
              <label className="text-sm font-medium text-gray-900 dark:text-gray-100 block mb-2">
                Tickers (comma-separated)
              </label>
              <input
                type="text"
                value={tickers}
                onChange={(e) => setTickers(e.target.value)}
                placeholder="e.g., AAPL, TSLA, NVDA (leave empty for all)"
                className="w-full px-3 py-2 text-sm border rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Leave empty to see all comments from the timeframe
              </p>
            </div>

            {/* Time Period */}
            <div className="flex-shrink-0 w-full lg:w-64">
              <label className="text-sm font-medium text-gray-900 dark:text-gray-100 block mb-2">
                Time Period
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  min="1"
                  max={maxValue}
                  value={timeValue}
                  onChange={(e) => {
                    const value = e.target.value
                    if (value === '') {
                      setTimeValue('')
                    } else {
                      setTimeValue(parseInt(value) || 1)
                    }
                  }}
                  className={`w-20 px-2 py-2 text-sm border rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${
                    isValidValue
                      ? 'border-gray-300 dark:border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500'
                      : 'border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500'
                  }`}
                />
                <select
                  value={timeUnit}
                  onChange={(e) => setTimeUnit(e.target.value)}
                  className="flex-1 px-2 py-2 text-sm border rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  {timeUnits.map((unit) => (
                    <option key={unit.value} value={unit.value}>
                      {unit.label}
                    </option>
                  ))}
                </select>
              </div>
              <p className={`text-xs mt-1 ${isValidValue ? 'text-gray-600 dark:text-gray-400' : 'text-red-500'}`}>
                ({getTimeDisplayText()})
              </p>
            </div>

            {/* Search Button */}
            <div className="flex-shrink-0 w-full lg:w-auto">
              <label className="text-sm font-medium text-gray-900 dark:text-gray-100 block mb-2 opacity-0">
                Action
              </label>
              <button
                onClick={handleSearch}
                disabled={!isValidValue || loading}
                className="flex items-center gap-2 px-4 py-2 text-sm rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed w-full lg:w-auto justify-center"
                style={{
                  backgroundColor: '#f8f9fa',
                  color: '#343a40',
                  border: '1px solid #dee2e6'
                }}
                onMouseEnter={(e) => {
                  if (isValidValue && !loading) {
                    e.target.style.backgroundColor = '#e9ecef'
                  }
                }}
                onMouseLeave={(e) => {
                  if (isValidValue && !loading) {
                    e.target.style.backgroundColor = '#f8f9fa'
                  }
                }}
              >
                <Search className="h-4 w-4" />
                {loading ? 'Searching...' : 'Search Comments'}
              </button>
            </div>
          </div>
        </div>

        {/* Comments Display */}
        <div className="flex-1 overflow-auto p-4">
          {loading && (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg animate-pulse">
                  <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded mb-2"></div>
                  <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          )}

          {!loading && hasSearched && comments.length === 0 && (
            <div className="text-center py-8">
              <MessageSquare className="h-12 w-12 text-gray-500 dark:text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">No comments found matching your criteria</p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                Try adjusting your ticker list or timeframe
              </p>
            </div>
          )}

          {!loading && hasSearched && comments.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
                <MessageSquare className="h-4 w-4" />
                <span>Found {comments.length} comments</span>
              </div>

              {comments.map((comment) => (
                <div key={comment.id} className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg border border-gray-200 dark:border-gray-600">
                  <div className="mb-3">
                    <p className="text-gray-900 dark:text-gray-100 leading-relaxed">{comment.body}</p>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                    <div className="flex items-center gap-1">
                      <Hash className="h-3 w-3" />
                      <span>r/{comment.subreddit}</span>
                    </div>

                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      <span>{formatTimestamp(comment.timestamp)}</span>
                    </div>

                    <div className="flex items-center gap-1">
                      <span>Tickers:</span>
                      <div className="flex gap-1">
                        {comment.tickers.map((ticker) => (
                          <span
                            key={ticker}
                            className="bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 px-2 py-0.5 rounded text-xs font-medium"
                          >
                            {ticker}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {!hasSearched && (
            <div className="text-center py-8">
              <Search className="h-12 w-12 text-gray-500 dark:text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">Enter your search criteria and click "Search Comments"</p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                Leave tickers empty to see all comments from the timeframe
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default CommentsModal