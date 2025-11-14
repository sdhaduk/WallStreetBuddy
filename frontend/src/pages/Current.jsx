import { useState, useEffect, useCallback } from 'react'
import BarChart from '../components/BarChart'
import CommentsModal from '../components/CommentsModal'
import { RefreshCw, MessageSquare } from 'lucide-react'
import Button from '../components/Button'

// SubredditSelector Component
const SubredditSelector = ({ selectedSubreddit, onSubredditChange }) => {
  const subreddits = [
    { value: 'all', label: 'All', display: 'All Subreddits' },
    { value: 'wallstreetbets', label: 'WSB', display: 'r/wallstreetbets' },
    { value: 'stocks', label: 'Stocks', display: 'r/stocks' },
    { value: 'valueinvesting', label: 'Value', display: 'r/valueInvesting' }
  ]

  return (
    <div className="space-y-2 justify-self-start md:justify-self-center">
      <label className="text-sm font-medium text-foreground text-left sm:text-center block">Subreddit</label>
      <select
        value={selectedSubreddit}
        onChange={(e) => onSubredditChange(e.target.value)}
        className="w-full max-w-[200px] sm:max-w-[320px] md:mx-auto px-3 py-2 text-sm border rounded-md bg-card text-foreground border-border focus:border-primary focus:ring-1 focus:ring-primary"
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
      <label className="text-sm font-medium text-foreground text-left sm:text-center block">Time Period</label>
      <div className="flex items-center justify-start sm:justify-center gap-2">
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
          className={`w-16 px-2 py-2 text-sm border rounded-md bg-card text-foreground ${
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
      <p className={`text-xs text-left sm:text-center ${isValidValue ? 'text-muted-foreground' : 'text-red-500'}`}>
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
      <div className="flex justify-start sm:justify-center">
        <Button
          onClick={onApplyFilters}
          disabled={!isValidForApply || loading}
          variant="outline"
          size="sm"
        >
          Apply Filters
        </Button>
      </div>
    </div>
  )
}

const Current = () => {
  const [currentData, setCurrentData] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [totalMentions, setTotalMentions] = useState(0)
  const [isCommentsModalOpen, setIsCommentsModalOpen] = useState(false)

  // Filter state
  const [selectedSubreddit, setSelectedSubreddit] = useState('all')
  const [timeValue, setTimeValue] = useState(3)
  const [timeUnit, setTimeUnit] = useState('days')
  const [filtersChanged, setFiltersChanged] = useState(false)

  // Applied filter state (what's actually being used for data)
  const [appliedSubreddit, setAppliedSubreddit] = useState('all')
  const [appliedTimeValue, setAppliedTimeValue] = useState(3)
  const [appliedTimeUnit, setAppliedTimeUnit] = useState('days')

  // Helper function to fetch data with specific parameters
  const fetchCurrentDataWithParams = async (subredditParam, timeValueParam, timeUnitParam) => {
    setLoading(true)
    try {
      // Create timeframe string from provided parameters
      let timeframe
      if (timeUnitParam === 'minutes') {
        timeframe = `${timeValueParam}m`
      } else if (timeUnitParam === 'hours') {
        timeframe = `${timeValueParam}h`
      } else if (timeUnitParam === 'days') {
        timeframe = `${timeValueParam}d`
      }

      // Map frontend subreddit names to backend values
      const subredditMap = {
        'all': 'all',
        'wallstreetbets': 'wallstreetbets',
        'stocks': 'stocks',
        'valueinvesting': 'ValueInvesting'
      }

      const subreddit = subredditMap[subredditParam] || 'all'

      const response = await fetch(`/api/top-10-filtered?timeframe=${timeframe}&subreddit=${subreddit}`)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()

      if (result.status === 200 && result.data) {
        // Transform backend data format to frontend format
        const transformedData = result.data.map(item => ({
          name: item.ticker,
          mentions: item.mentions
        }))

        setCurrentData(transformedData)
        setTotalMentions(result.total_mentions || 0)
        setLastUpdated(new Date())
      } else {
        console.error('Invalid response format:', result)
        setCurrentData([])
        setTotalMentions(0)
      }
    } catch (error) {
      console.error('Error fetching ticker data:', error)
      setCurrentData([])
      setTotalMentions(0)
    } finally {
      setLoading(false)
    }
  }

  // Fetch data from backend API using applied state
  const fetchCurrentData = useCallback(async () => {
    await fetchCurrentDataWithParams(appliedSubreddit, appliedTimeValue, appliedTimeUnit)
  }, [appliedSubreddit, appliedTimeValue, appliedTimeUnit])

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
  const applyFilters = async () => {
    // Validate timeValue before applying
    const units = {
      minutes: { max: 10080 }, // 7 days in minutes
      hours: { max: 168 },     // 7 days in hours
      days: { max: 7 }         // 7 days
    }

    const maxValue = units[timeUnit]?.max || 7
    const validValue = Math.min(Math.max(1, parseInt(timeValue) || 1), maxValue)

    // Update the input value if it was corrected
    if (validValue !== timeValue) {
      setTimeValue(validValue)
    }

    // Set applied filters
    setAppliedSubreddit(selectedSubreddit)
    setAppliedTimeValue(validValue)
    setAppliedTimeUnit(timeUnit)

    // Call fetchCurrentData with the new values directly
    await fetchCurrentDataWithParams(selectedSubreddit, validValue, timeUnit)
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


  // Initial load
  useEffect(() => {
    fetchCurrentData()
  }, [])

  // Polling every minute
  useEffect(() => {
    const interval = setInterval(() => {
      fetchCurrentData()
    }, 60000) // 60 seconds

    return () => clearInterval(interval)
  }, [fetchCurrentData])

  if (loading && !currentData.length) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h1 className="text-3xl md:text-5xl lg:text-5xl font-bold">Live Count</h1>
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
            <RefreshCw className="h-4 w-4 hidden sm:inline" />
            <span className="hidden sm:inline">Loading...</span>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setIsCommentsModalOpen(true)}
              variant="outline"
              size="sm"
              className="gap-2"
            >
              <MessageSquare className="h-4 w-4" />
              View Comments
            </Button>
            <Button
              disabled={true}
              variant="outline"
              size="sm"
            >
              Refresh Now
            </Button>
          </div>
        </div>
        
        <div className="bg-card p-6 rounded-lg border">
          <h3 className="text-base sm:text-xl font-semibold mb-4">{getDynamicTitle()} (Live Count)</h3>
          <div className="h-96 bg-muted rounded animate-pulse flex items-center justify-center">
            <p className="text-muted-foreground">Loading chart...</p>
          </div>
        </div>

        <div className="bg-card p-4 rounded-lg border">
          <h3 className="font-semibold mb-2 text-center">Current Filter Information</h3>
          <div className="text-sm text-muted-foreground space-y-1 flex flex-col items-center">
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
        <h1 className="text-3xl md:text-5xl lg:text-5xl font-bold">Live Count</h1>
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
          <RefreshCw className={`h-4 w-4 hidden sm:inline ${loading || filtersChanged ? 'animate-spin' : ''}`} />
          <span>
            {filtersChanged ? 'Applying filters...' :
             loading ? 'Loading...' :
             <span className="hidden sm:inline">{`Last updated: ${lastUpdated ? lastUpdated.toLocaleTimeString() : 'Loading...'}`}</span>}
          </span>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => setIsCommentsModalOpen(true)}
            variant="outline"
            size="sm"
            className="gap-2"
          >
            <MessageSquare className="h-4 w-4" />
            Search Comments
          </Button>
          <Button
            onClick={fetchCurrentData}
            disabled={loading}
            variant="outline"
            size="sm"
          >
            Refresh Now
          </Button>
        </div>
      </div>
      
      <BarChart
        data={currentData}
        title={`${getDynamicTitle()} (Live Count)`}
        enableClick={false}
        height={350}
        barColor="var(--chart-current)"
        hoverColor="var(--chart-current-hover)"
      />

      <div className="bg-card p-4 rounded-lg border">
        <h3 className="font-semibold mb-2 text-center">Current Filter Information</h3>
        <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1 text-left">
          <li>Source: {getSubredditDisplayName()}</li>
          <li>Time Range: Last {getTimeDisplayText()}</li>
          <li>Total mentions: {totalMentions.toLocaleString()}</li>
          <li>Automatic refresh every minute</li>
        </ul>
      </div>

      <div className="p-4 rounded-lg border bg-green-50 border-green-400">
        <p className="text-sm text-green-800">
          ℹ️ This data represents live counting in progress. Charts are not clickable as analysis is not yet complete.
        </p>
      </div>

      <CommentsModal
        isOpen={isCommentsModalOpen}
        onClose={() => setIsCommentsModalOpen(false)}
      />
    </div>
  )
}

export default Current