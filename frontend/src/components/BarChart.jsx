import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

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
      <div className="bg-card p-6 rounded-lg border">
        <h3 className="text-xl font-semibold mb-4">{title}</h3>
        <div className="h-64 flex items-center justify-center">
          <p className="text-muted-foreground">No data available</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-card p-6 rounded-lg border w-full">
      <h3 className="text-xl font-semibold mb-4">{title}</h3>
      <div style={{ height: `${height}px` }}>
        <ResponsiveContainer width="100%" height="100%">
          <RechartsBarChart 
            data={data}
            onMouseLeave={handleMouseLeave}
          >
            <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
            <XAxis
              dataKey="name"
              className="text-sm"
              tick={{ fontSize: 12, fontWeight: 'bold' }}
            />
            <YAxis 
              className="text-sm"
              tick={{ fontSize: 12 }}
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
      {enableClick && (
        <p className="text-sm text-muted-foreground mt-2 text-center">
          Click on any bar to view detailed analysis
        </p>
      )}
    </div>
  )
}

export default BarChart