import React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

const colorStyles = {
  accent: 'bg-accent',
  success: 'bg-success',
  warning: 'bg-warning',
  danger: 'bg-danger',
} as const

export type ProgressColor = keyof typeof colorStyles

export interface ProgressProps {
  value: number
  className?: string
  color?: ProgressColor
  glow?: boolean
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  className,
  color = 'accent',
  glow = false,
}) => {
  const clampedValue = Math.min(100, Math.max(0, value))

  return (
    <div
      className={cn(
        'h-2 w-full overflow-hidden rounded-full bg-border',
        glow && 'glow-accent',
        className,
      )}
      role="progressbar"
      aria-valuenow={clampedValue}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <motion.div
        className={cn(
          'h-full rounded-full',
          colorStyles[color],
        )}
        initial={{ width: 0 }}
        animate={{ width: `${clampedValue}%` }}
        transition={{
          duration: 0.8,
          ease: [0.25, 0.46, 0.45, 0.94],
        }}
      />
    </div>
  )
}

Progress.displayName = 'Progress'

export default Progress
