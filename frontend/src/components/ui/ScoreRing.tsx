/**
 * Animated circular score indicator.
 * Used for ATS score, resume quality, job match percentages.
 */

import { clsx } from 'clsx'

interface ScoreRingProps {
  score: number        // 0–100
  size?: number        // px
  strokeWidth?: number
  label?: string
  className?: string
}

function getColor(score: number): string {
  if (score >= 75) return '#22c55e'   // green
  if (score >= 50) return '#eab308'   // yellow
  return '#ef4444'                     // red
}

export function ScoreRing({
  score,
  size = 120,
  strokeWidth = 10,
  label,
  className,
}: ScoreRingProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = getColor(score)

  return (
    <div className={clsx('flex flex-col items-center gap-2', className)}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#1f2937"
          strokeWidth={strokeWidth}
        />
        {/* Progress arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
        />
        {/* Score text (rotated back upright) */}
        <text
          x="50%"
          y="50%"
          dominantBaseline="middle"
          textAnchor="middle"
          fill={color}
          fontSize={size * 0.22}
          fontWeight="700"
          style={{ transform: `rotate(90deg)`, transformOrigin: 'center', fontFamily: 'sans-serif' }}
        >
          {Math.round(score)}
        </text>
      </svg>
      {label && (
        <span className="text-sm text-gray-400 font-medium">{label}</span>
      )}
    </div>
  )
}
