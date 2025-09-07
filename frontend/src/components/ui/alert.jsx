import React from 'react'

const Alert = ({ className = '', variant = 'default', children, ...props }) => {
  const variants = {
    default: 'bg-white border-gray-200',
    destructive: 'border-red-200 bg-red-50 text-red-900'
  }
  
  return (
    <div
      role="alert"
      className={`relative w-full rounded-lg border p-4 ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

const AlertDescription = ({ className = '', children, ...props }) => {
  return (
    <div
      className={`text-sm [&_p]:leading-relaxed ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export { Alert, AlertDescription }

