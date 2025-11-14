import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'

const BarChart = ({
  data = [],
  title = "Stock Mentions",
  enableClick = false,
  height = 400,
  barColor = "#8884d8",
  hoverColor = "#6366f1"
}) => {
  const navigate = useNavigate()
  const [hoveredIndex, setHoveredIndex] = useState(null)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 640)
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const handleBarClick = (data, index) => {
    if (enableClick && data) {
      navigate(`/stock/${data.name}`)
    }
  }

  const handleMouseEnter = (data, index) => {
    if (enableClick) {
      setHoveredIndex(index)
    }
  }

  const handleMouseLeave = () => {
    setHoveredIndex(null)
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-card p-2 sm:p-6 rounded-lg border">
        <h3 className="text-base sm:text-xl font-semibold mb-4">{title}</h3>
        <div className="h-64 flex items-center justify-center">
          <p className="text-muted-foreground">No data available</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-card p-1 sm:pt-6 sm:px-6 sm:pb-2 rounded-lg border w-full">
      <h3 className="text-base sm:text-xl font-semibold mb-4">{title}</h3>
      <div style={{ height: `${isMobile ? 220 : height}px` }}>
        <ResponsiveContainer width="100%" height="100%">
          <RechartsBarChart
            data={data}
            onMouseLeave={handleMouseLeave}
            margin={{
              top: 20,
              right: isMobile ? 10 : 30,
              left: isMobile ? 10 : 20,
              bottom: isMobile ? 15 : 5
            }}
          >
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis
              dataKey="name"
              className="text-sm"
              tick={{ fontSize: isMobile ? 10 : 12, fontWeight: 'bold' }}
              angle={isMobile ? -45 : 0}
              textAnchor={isMobile ? 'end' : 'middle'}
              height={isMobile ? 35 : 20}
            />
            <YAxis
              className="text-sm"
              tick={{ fontSize: isMobile ? 10 : 12 }}
              width={isMobile ? 30 : 60}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px',
                color: 'hsl(var(--foreground))'
              }}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
            />
            <Bar
              dataKey="mentions"
              cursor={enableClick ? 'pointer' : 'default'}
              onClick={handleBarClick}
              onMouseEnter={handleMouseEnter}
              animationDuration={900}
              animationEasing="ease-out"
              radius={[12, 12, 0, 0]}
            >
              {data.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={hoveredIndex === index ? hoverColor : barColor}
                />
              ))}
            </Bar>
          </RechartsBarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default BarChart