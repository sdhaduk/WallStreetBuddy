import { useState, useEffect, useCallback } from 'react'
import BarChart from '../components/BarChart'
import { RefreshCw } from 'lucide-react'

// SubredditSelector Component
const SubredditSelector = ({ selectedSubreddit, onSubredditChange }) => {
  const subreddits = [
    { value: 'all', label: 'All', display: 'All Subreddits' },
    { value: 'wallstreetbets', label: 'WSB', display: 'r/wallstreetbets' },
    { value: 'stocks', label: 'Stocks', display: 'r/stocks' },
    { value: 'valueinvesting', label: 'Value', display: 'r/valueInvesting' }
  ]

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-foreground text-center block">Subreddit</label>
      <select
        value={selectedSubreddit}
        onChange={(e) => onSubredditChange(e.target.value)}
        className="w-60 mx-auto px-3 py-2 text-sm border rounded-md bg-card text-foreground border-border focus:border-primary focus:ring-1 focus:ring-primary"
      >
        {subreddits.map((subreddit) => (
          <option key={subreddit.value} value={subreddit.value}>
            {subreddit.display}
          </option>
        ))}
      </select>
    </div>
  )
}

// TimeSelector Component
const TimeSelector = ({ timeValue, timeUnit, onTimeValueChange, onTimeUnitChange }) => {
  const units = [
    { value: 'minutes', label: 'Minutes', max: 10080 }, // 7 days in minutes
    { value: 'hours', label: 'Hours', max: 168 },       // 7 days in hours
    { value: 'days', label: 'Days', max: 7 }            // 7 days
  ]

  const currentUnit = units.find(unit => unit.value === timeUnit)
  const maxValue = currentUnit ? currentUnit.max : 7

  const numericTimeValue = parseInt(timeValue) || 0
  const isValidValue = numericTimeValue >= 1 && numericTimeValue <= maxValue && timeValue !== ''

  const getDisplayText = () => {
    if (timeValue === '' || numericTimeValue < 1) return 'Enter a value'
    if (numericTimeValue > maxValue) return `Max ${maxValue} ${timeUnit}`
    return `showing last ${numericTimeValue} ${numericTimeValue === 1 ? timeUnit.slice(0, -1) : timeUnit}`
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-foreground text-center block">Time Period</label>
      <div className="flex items-center justify-center gap-2">
        <input
          type="number"
          min="1"
          max={maxValue}
          value={timeValue}
          onChange={(e) => {
            const value = e.target.value
            if (value === '') {
              onTimeValueChange('')
            } else {
              onTimeValueChange(parseInt(value) || 1)
            }
          }}
          className={`w-20 px-3 py-2 text-sm border rounded-md bg-card text-foreground ${
            isValidValue
              ? 'border-border focus:border-primary focus:ring-1 focus:ring-primary'
              : 'border-red-500 focus:border-red-500 focus:ring-1 focus:ring-red-500'
          }`}
        />
        <select
          value={timeUnit}
          onChange={(e) => onTimeUnitChange(e.target.value)}
          className="px-3 py-2 text-sm border rounded-md bg-card text-foreground border-border focus:border-primary focus:ring-1 focus:ring-primary"
        >
          {units.map((unit) => (
            <option key={unit.value} value={unit.value}>
              {unit.label}
            </option>
          ))}
        </select>
      </div>
      <p className={`text-xs text-center ${isValidValue ? 'text-muted-foreground' : 'text-red-500'}`}>
        ({getDisplayText()})
      </p>
    </div>
  )
}

// FilterControls Container Component
const FilterControls = ({
  selectedSubreddit,
  onSubredditChange,
  timeValue,
  timeUnit,
  onTimeValueChange,
  onTimeUnitChange,
  onApplyFilters,
  loading
}) => {
  // Check if current values are valid for the apply button
  const numericTimeValue = parseInt(timeValue) || 0
  const units = {
    minutes: { max: 10080 },
    hours: { max: 168 },
    days: { max: 7 }
  }
  const maxValue = units[timeUnit]?.max || 7
  const isValidForApply = numericTimeValue >= 1 && numericTimeValue <= maxValue && timeValue !== ''

  return (
    <div className="bg-card p-4 rounded-lg border space-y-4">
      <h3 className="text-lg font-semibold text-center">Filters</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SubredditSelector
          selectedSubreddit={selectedSubreddit}
          onSubredditChange={onSubredditChange}
        />
        <TimeSelector
          timeValue={timeValue}
          timeUnit={timeUnit}
          onTimeValueChange={onTimeValueChange}
          onTimeUnitChange={onTimeUnitChange}
        />
      </div>
      <div className="flex justify-center">
        <button
          onClick={onApplyFilters}
          disabled={!isValidForApply || loading}
          className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          Apply Filters
        </button>
      </div>
    </div>
  )
}

const Current = () => {
  const [currentData, setCurrentData] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  // Filter state
  const [selectedSubreddit, setSelectedSubreddit] = useState('all')
  const [timeValue, setTimeValue] = useState(3)
  const [timeUnit, setTimeUnit] = useState('days')
  const [filtersChanged, setFiltersChanged] = useState(false)

  // Applied filter state (what's actually being used for data)
  const [appliedSubreddit, setAppliedSubreddit] = useState('all')
  const [appliedTimeValue, setAppliedTimeValue] = useState(3)
  const [appliedTimeUnit, setAppliedTimeUnit] = useState('days')

  // Debounced refresh function
  const debouncedRefresh = useCallback(() => {
    setFiltersChanged(true)
    const timeoutId = setTimeout(() => {
      fetchCurrentData()
      setFiltersChanged(false)
    }, 300) // 300ms delay

    return () => clearTimeout(timeoutId)
  }, [])

  // Filter handlers (no automatic updates)
  const handleSubredditChange = (subreddit) => {
    setSelectedSubreddit(subreddit)
  }

  const handleTimeValueChange = (value) => {
    setTimeValue(value)
  }

  const handleTimeUnitChange = (unit) => {
    setTimeUnit(unit)
    // Auto-adjust timeValue if it exceeds new unit's max
    const units = {
      minutes: { max: 10080 }, // 7 days in minutes
      hours: { max: 168 },     // 7 days in hours
      days: { max: 7 }         // 7 days
    }

    const maxValue = units[unit]?.max || 7
    if (timeValue > maxValue) {
      setTimeValue(maxValue)
    }
  }

  // Apply filters function
  const applyFilters = () => {
    // Validate timeValue before applying
    const units = {
      minutes: { max: 10080 }, // 7 days in minutes
      hours: { max: 168 },     // 7 days in hours
      days: { max: 7 }         // 7 days
    }

    const maxValue = units[timeUnit]?.max || 7
    const validValue = Math.min(Math.max(1, parseInt(timeValue) || 1), maxValue)

    setAppliedSubreddit(selectedSubreddit)
    setAppliedTimeValue(validValue)
    setAppliedTimeUnit(timeUnit)

    // Update the input value if it was corrected
    if (validValue !== timeValue) {
      setTimeValue(validValue)
    }

    fetchCurrentData()
  }

  // Enhanced mock data function based on filters
  const generateMockCurrentData = () => {
    // Subreddit-specific stock preferences
    const subredditData = {
      wallstreetbets: [
        { name: 'GME', mentions: 1200 },
        { name: 'AMC', mentions: 980 },
        { name: 'TSLA', mentions: 850 },
        { name: 'NVDA', mentions: 720 },
        { name: 'PLTR', mentions: 650 },
        { name: 'BB', mentions: 580 },
        { name: 'AAPL', mentions: 520 },
        { name: 'AMD', mentions: 480 },
        { name: 'MSFT', mentions: 420 },
        { name: 'SPY', mentions: 380 }
      ],
      stocks: [
        { name: 'AAPL', mentions: 950 },
        { name: 'MSFT', mentions: 820 },
        { name: 'GOOGL', mentions: 750 },
        { name: 'AMZN', mentions: 680 },
        { name: 'TSLA', mentions: 620 },
        { name: 'NVDA', mentions: 580 },
        { name: 'META', mentions: 520 },
        { name: 'NFLX', mentions: 480 },
        { name: 'AMD', mentions: 450 },
        { name: 'INTC', mentions: 380 }
      ],
      valueinvesting: [
        { name: 'BRK.B', mentions: 720 },
        { name: 'JNJ', mentions: 650 },
        { name: 'KO', mentions: 580 },
        { name: 'PG', mentions: 520 },
        { name: 'AAPL', mentions: 480 },
        { name: 'MSFT', mentions: 450 },
        { name: 'VTI', mentions: 420 },
        { name: 'SPY', mentions: 380 },
        { name: 'WMT', mentions: 350 },
        { name: 'JPM', mentions: 320 }
      ],
      all: [
        { name: 'AAPL', mentions: 890 },
        { name: 'TSLA', mentions: 720 },
        { name: 'NVDA', mentions: 650 },
        { name: 'AMD', mentions: 480 },
        { name: 'MSFT', mentions: 420 },
        { name: 'GOOGL', mentions: 380 },
        { name: 'AMZN', mentions: 340 },
        { name: 'META', mentions: 290 },
        { name: 'NFLX', mentions: 250 },
        { name: 'GME', mentions: 220 }
      ]
    }

    // Get base data for applied subreddit
    const baseData = subredditData[appliedSubreddit] || subredditData.all

    // Calculate time multiplier based on applied timeframe
    let timeMultiplier = 1
    const totalMinutes = appliedTimeUnit === 'minutes' ? appliedTimeValue :
                        appliedTimeUnit === 'hours' ? appliedTimeValue * 60 :
                        appliedTimeValue * 24 * 60

    // Shorter timeframes have fewer mentions
    if (totalMinutes < 60) timeMultiplier = 0.1      // < 1 hour
    else if (totalMinutes < 360) timeMultiplier = 0.3 // < 6 hours
    else if (totalMinutes < 1440) timeMultiplier = 0.6 // < 1 day
    else if (totalMinutes < 4320) timeMultiplier = 0.8 // < 3 days

    // Add randomness and apply time multiplier
    return baseData.map(item => ({
      ...item,
      mentions: Math.max(1, Math.floor((item.mentions * timeMultiplier) + Math.floor(Math.random() * 20) - 10))
    }))
  }

  // Helper functions for dynamic content (using applied filters)
  const getSubredditDisplayName = () => {
    const names = {
      all: 'All Subreddits',
      wallstreetbets: 'r/wallstreetbets',
      stocks: 'r/stocks',
      valueinvesting: 'r/valueInvesting'
    }
    return names[appliedSubreddit] || 'All Subreddits'
  }

  const getTimeDisplayText = () => {
    const singular = appliedTimeValue === 1 ? appliedTimeUnit.slice(0, -1) : appliedTimeUnit
    return `${appliedTimeValue} ${singular}`
  }

  const getDynamicTitle = () => {
    return `Top 10 from ${getSubredditDisplayName()} - Last ${getTimeDisplayText()}`
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
          <p className="text-muted-foreground mt-2">Live count of mentions from {getSubredditDisplayName()} in the last {getTimeDisplayText()}</p>
        </div>

        <FilterControls
          selectedSubreddit={selectedSubreddit}
          onSubredditChange={handleSubredditChange}
          timeValue={timeValue}
          timeUnit={timeUnit}
          onTimeValueChange={handleTimeValueChange}
          onTimeUnitChange={handleTimeUnitChange}
          onApplyFilters={applyFilters}
          loading={loading}
        />

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
          <h3 className="text-xl font-semibold mb-4">{getDynamicTitle()} (Live Count)</h3>
          <div className="h-96 bg-muted rounded animate-pulse flex items-center justify-center">
            <p className="text-muted-foreground">Loading chart...</p>
          </div>
        </div>

        <div className="bg-card p-4 rounded-lg border">
          <h3 className="font-semibold mb-2">Current Filter Information</h3>
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
        <p className="text-muted-foreground mt-2">Live count of mentions from {getSubredditDisplayName()} in the last {getTimeDisplayText()}</p>
      </div>

      <FilterControls
        selectedSubreddit={selectedSubreddit}
        onSubredditChange={handleSubredditChange}
        timeValue={timeValue}
        timeUnit={timeUnit}
        onTimeValueChange={handleTimeValueChange}
        onTimeUnitChange={handleTimeUnitChange}
        onApplyFilters={applyFilters}
        loading={loading}
      />

      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
          <RefreshCw className={`h-4 w-4 ${loading || filtersChanged ? 'animate-spin' : ''}`} />
          <span>
            {filtersChanged ? 'Applying filters...' :
             loading ? 'Loading...' :
             `Last updated: ${lastUpdated ? lastUpdated.toLocaleTimeString() : 'Loading...'}`}
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
        title={`${getDynamicTitle()} (Live Count)`}
        enableClick={false}
        height={400}
        barColor="#10b981"
        hoverColor="#059669"
      />

      <div className="bg-card p-4 rounded-lg border">
        <h3 className="font-semibold mb-2">Current Filter Information</h3>
        <div className="text-sm text-muted-foreground space-y-1">
          <p>• Source: {getSubredditDisplayName()}</p>
          <p>• Time Range: Last {getTimeDisplayText()}</p>
          <p>• Total mentions: {currentData.reduce((sum, item) => sum + item.mentions, 0).toLocaleString()}</p>
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