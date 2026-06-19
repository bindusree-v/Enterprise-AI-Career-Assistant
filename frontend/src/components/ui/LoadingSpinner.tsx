import { clsx } from 'clsx'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  label?: string
  className?: string
}

const sizes = {
  sm: 'w-4 h-4 border-2',
  md: 'w-8 h-8 border-2',
  lg: 'w-12 h-12 border-3',
}

export function LoadingSpinner({ size = 'md', label, className }: LoadingSpinnerProps) {
  return (
    <div className={clsx('flex flex-col items-center gap-3', className)}>
      <div
        className={clsx(
          sizes[size],
          'rounded-full border-gray-700 border-t-indigo-500 animate-spin'
        )}
      />
      {label && <p className="text-sm text-gray-400 animate-pulse">{label}</p>}
    </div>
  )
}

export function FullPageLoader({ label = 'Loading...' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <LoadingSpinner size="lg" label={label} />
    </div>
  )
}
