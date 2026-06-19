import { clsx } from 'clsx'

interface ProgressBarProps {
  value: number   // 0–100
  label?: string
  showValue?: boolean
  colorClass?: string
  className?: string
}

function getColorClass(value: number): string {
  if (value >= 75) return 'bg-green-500'
  if (value >= 50) return 'bg-yellow-500'
  return 'bg-red-500'
}

export function ProgressBar({
  value,
  label,
  showValue = true,
  colorClass,
  className,
}: ProgressBarProps) {
  const color = colorClass ?? getColorClass(value)

  return (
    <div className={clsx('w-full', className)}>
      {(label || showValue) && (
        <div className="flex justify-between mb-1">
          {label && <span className="text-sm text-gray-400">{label}</span>}
          {showValue && (
            <span className="text-sm font-semibold text-gray-200">{Math.round(value)}%</span>
          )}
        </div>
      )}
      <div className="w-full bg-gray-800 rounded-full h-2">
        <div
          className={clsx('h-2 rounded-full transition-all duration-700', color)}
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
    </div>
  )
}
