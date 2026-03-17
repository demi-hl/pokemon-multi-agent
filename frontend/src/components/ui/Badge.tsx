import React from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

const variantStyles = {
  default: 'bg-surface-elevated text-foreground',
  accent: 'bg-accent-muted text-accent',
  success: 'bg-success-muted text-success',
  warning: 'bg-warning-muted text-warning',
  danger: 'bg-danger-muted text-danger',
  info: 'bg-info-muted text-info',
} as const

export type BadgeVariant = keyof typeof variantStyles

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  pulse?: boolean
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  pulse = false,
  className,
  children,
  ...props
}) => {
  const baseClassName = cn(
    'inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-full',
    variantStyles[variant],
    className,
  )

  if (pulse) {
    return (
      <motion.span
        className={baseClassName}
        animate={{ scale: [1, 1.05, 1] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        {...(props as React.ComponentPropsWithoutRef<typeof motion.span>)}
      >
        {children}
      </motion.span>
    )
  }

  return (
    <span
      className={baseClassName}
      {...props}
    >
      {children}
    </span>
  )
}

Badge.displayName = 'Badge'

export default Badge
