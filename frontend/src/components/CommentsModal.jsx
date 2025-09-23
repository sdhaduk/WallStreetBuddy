import { useState } from 'react'
import { X, Search, MessageSquare, Calendar, Hash } from 'lucide-react'

const CommentsModal = ({ isOpen, onClose }) => {
  const [tickers, setTickers] = useState('')
  const [timeValue, setTimeValue] = useState(3)
  const [timeUnit, setTimeUnit] = useState('days')
  const [subreddit, setSubreddit] = useState('all')
  const [comments, setComments] = useState([])
  const [loading, setLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [cursor, setCursor] = useState(null)
  const [hasMore, setHasMore] = useState(false)
  const [error, setError] = useState(null)
  const [loadingMore, setLoadingMore] = useState(false)

  const timeUnits = [
    { value: 'minutes', label: 'Minutes', max: 10080 },
    { value: 'hours', label: 'Hours', max: 168 },
    { value: 'days', label: 'Days', max: 7 }
  ]

  const subreddits = [
    { value: 'all', label: 'All Subreddits' },
    { value: 'wallstreetbets', label: 'r/wallstreetbets' },
    { value: 'stocks', label: 'r/stocks' },
    { value: 'valueinvesting', label: 'r/ValueInvesting' }
  ]

  // API function to fetch comments
  const fetchComments = async (isLoadMore = false) => {
    const currentLoading = isLoadMore ? setLoadingMore : setLoading
    currentLoading(true)
    setError(null)

    try {
      // Build timeframe string
      let timeframe
      if (timeUnit === 'minutes') {
        timeframe = `${timeValue}m`
      } else if (timeUnit === 'hours') {
        timeframe = `${timeValue}h`
      } else if (timeUnit === 'days') {
        timeframe = `${timeValue}d`
      }

      // Map frontend subreddit names to backend values
      const subredditMap = {
        'all': 'all',
        'wallstreetbets': 'wallstreetbets',
        'stocks': 'stocks',
        'valueinvesting': 'ValueInvesting'
      }

      const mappedSubreddit = subredditMap[subreddit] || 'all'

      // Build URL with query parameters
      const params = new URLSearchParams({
        timeframe,
        subreddit: mappedSubreddit,
        size: '50'
      })

      // Add tickers if provided
      if (tickers && tickers.trim()) {
        params.append('tickers', tickers.trim())
      }

      // Add cursor for pagination
      if (isLoadMore && cursor) {
        params.append('cursor', cursor)
      }

      const response = await fetch(`http://localhost:8000/api/comments?${params}`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()

      if (result.status === 200) {
        const newComments = result.data || []

        if (isLoadMore) {
          // Append to existing comments
          setComments(prev => [...prev, ...newComments])
        } else {
          // Replace comments for new search
          setComments(newComments)
          setHasSearched(true)
        }

        // Update pagination state
        setCursor(result.pagination?.next_cursor || null)
        setHasMore(result.pagination?.has_next || false)
      } else {
        throw new Error(result.detail || 'Failed to fetch comments')
      }
    } catch (err) {
      console.error('Error fetching comments:', err)
      setError(err.message || 'Failed to fetch comments. Please try again.')

      if (!isLoadMore) {
        setComments([])
        setHasSearched(true)
      }
    } finally {
      currentLoading(false)
    }
  }

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
    // Reset pagination state for new search
    setCursor(null)
    setHasMore(false)

    // Call API to fetch comments
    fetchComments(false)
  }

  const handleLoadMore = () => {
    fetchComments(true)
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

            {/* Subreddit Filter */}
            <div className="flex-shrink-0 w-full lg:w-48">
              <label className="text-sm font-medium text-gray-900 dark:text-gray-100 block mb-2">
                Subreddit
              </label>
              <select
                value={subreddit}
                onChange={(e) => setSubreddit(e.target.value)}
                className="w-full px-3 py-2 text-sm border rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              >
                {subreddits.map((sub) => (
                  <option key={sub.value} value={sub.value}>
                    {sub.label}
                  </option>
                ))}
              </select>
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

          {/* Error State */}
          {!loading && error && (
            <div className="text-center py-8">
              <MessageSquare className="h-12 w-12 text-red-500 dark:text-red-400 mx-auto mb-4" />
              <p className="text-red-600 dark:text-red-400 mb-2">{error}</p>
              <button
                onClick={handleSearch}
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                Try again
              </button>
            </div>
          )}

          {!loading && !error && hasSearched && comments.length === 0 && (
            <div className="text-center py-8">
              <MessageSquare className="h-12 w-12 text-gray-500 dark:text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">No comments found matching your criteria</p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                Try adjusting your ticker list or timeframe
              </p>
            </div>
          )}

          {!loading && !error && hasSearched && comments.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
                <MessageSquare className="h-4 w-4" />
                <span>Found {comments.length} comments</span>
              </div>

              {comments.map((comment) => (
                <div key={comment.id} className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg border border-gray-200 dark:border-gray-600">
                  <div className="mb-3">
                    <p className="text-gray-900 dark:text-gray-100 leading-relaxed text-left">{comment.body}</p>
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                    <div className="flex items-center gap-1">
                      <Hash className="h-3 w-3" />
                      <span>r/{comment.subreddit}</span>
                    </div>

                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      <span>{comment.timestamp}</span>
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

              {/* Load More Button */}
              {hasMore && (
                <div className="text-center mt-6">
                  <button
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                    className="px-6 py-2 text-sm rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    style={{
                      backgroundColor: '#f8f9fa',
                      color: '#343a40',
                      border: '1px solid #dee2e6'
                    }}
                    onMouseEnter={(e) => {
                      if (!loadingMore) {
                        e.target.style.backgroundColor = '#e9ecef'
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!loadingMore) {
                        e.target.style.backgroundColor = '#f8f9fa'
                      }
                    }}
                  >
                    {loadingMore ? 'Loading...' : 'Load More Comments'}
                  </button>
                </div>
              )}
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