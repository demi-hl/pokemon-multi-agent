import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface LoadingScreenProps {
  message?: string
  className?: string
}

export default function LoadingScreen({
  message = 'Loading...',
  className,
}: LoadingScreenProps) {
  return (
    <div
      className={cn(
        'fixed inset-0 z-50 flex flex-col items-center justify-center bg-background',
        className
      )}
    >
      {/* Ambient background glow */}
      <div className="absolute inset-0 mesh-gradient opacity-50" />

      {/* Animated Pokeball SVG */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        className="relative"
      >
        {/* Outer glow ring */}
        <motion.div
          className="absolute -inset-4 rounded-full"
          animate={{
            boxShadow: [
              '0 0 20px rgba(239, 68, 68, 0.1)',
              '0 0 40px rgba(239, 68, 68, 0.25)',
              '0 0 20px rgba(239, 68, 68, 0.1)',
            ],
          }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        />

        <svg
          viewBox="0 0 100 100"
          className="h-20 w-20"
        >
          {/* Outer circle */}
          <motion.circle
            cx="50"
            cy="50"
            r="46"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            className="text-border"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1, rotate: 360 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          />
          {/* Top half (red) */}
          <motion.path
            d="M 4 50 A 46 46 0 0 1 96 50"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            className="text-red-500"
            animate={{ rotate: 360 }}
            transition={{ duration: 1.2, repeat: Infinity, ease: 'linear' }}
            style={{ transformOrigin: '50px 50px' }}
          />
          {/* Center line */}
          <line
            x1="4"
            y1="50"
            x2="96"
            y2="50"
            stroke="currentColor"
            strokeWidth="3"
            className="text-border-light"
          />
          {/* Center circle outer */}
          <circle
            cx="50"
            cy="50"
            r="14"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            className="text-border-light"
          />
          {/* Center circle inner - pulsing */}
          <motion.circle
            cx="50"
            cy="50"
            r="7"
            fill="currentColor"
            className="text-red-500"
            animate={{ r: [7, 9, 7] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          />
        </svg>
      </motion.div>

      {/* Loading text with typewriter effect */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.5 }}
        className="mt-8 flex flex-col items-center gap-2"
      >
        <p className="text-sm font-medium text-foreground text-glow">{message}</p>
        <motion.div
          className="flex gap-1"
          initial="hidden"
          animate="visible"
        >
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="h-1.5 w-1.5 rounded-full bg-red-500"
              animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1.2, 0.8] }}
              transition={{
                duration: 1.2,
                repeat: Infinity,
                delay: i * 0.2,
                ease: 'easeInOut',
              }}
            />
          ))}
        </motion.div>
      </motion.div>
    </div>
  )
}
