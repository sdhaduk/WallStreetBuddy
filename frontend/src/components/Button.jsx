import { cn } from '../lib/utils'

const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  type = 'button',
  className = '',
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center rounded-md font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none hover:scale-105 active:scale-95 cursor-pointer'

  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg focus:ring-blue-500',
    secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-300 hover:shadow-md border border-gray-300 focus:ring-gray-500',
    outline: 'border border-gray-300 bg-transparent text-gray-700 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-400 hover:shadow-md focus:ring-blue-500',
    ghost: 'hover:bg-blue-100 hover:text-blue-700 text-gray-700 hover:shadow-sm focus:ring-blue-500',
    destructive: 'bg-red-600 text-white hover:bg-red-700 hover:shadow-lg focus:ring-red-500',
  }

  const sizes = {
    sm: 'h-9 px-3 text-sm',
    md: 'h-10 py-2 px-4',
    lg: 'h-11 px-8',
    icon: 'h-10 w-10',
  }

  return (
    <button
      type={type}
      className={cn(
        baseClasses,
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  )
}

export default Button