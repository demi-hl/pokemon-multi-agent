import type { Variants, Transition } from 'framer-motion'

/* ── Page Transitions ── */
export const pageTransition: Transition = {
  type: 'tween',
  ease: 'easeOut',
  duration: 0.3,
}

export const pageVariants: Variants = {
  initial: { opacity: 0, y: 20, filter: 'blur(4px)' },
  animate: { opacity: 1, y: 0, filter: 'blur(0px)' },
  exit: { opacity: 0, y: -10, filter: 'blur(4px)' },
}

/* ── Fade Variants ── */
export const fadeIn: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
}

export const fadeInUp: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 20 },
}

export const fadeInDown: Variants = {
  initial: { opacity: 0, y: -20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
}

/* ── Slide Variants ── */
export const slideInRight: Variants = {
  initial: { opacity: 0, x: 30 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -30 },
}

export const slideInLeft: Variants = {
  initial: { opacity: 0, x: -30 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 30 },
}

/* ── Scale Variants ── */
export const scaleIn: Variants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
}

export const popIn: Variants = {
  initial: { opacity: 0, scale: 0.8 },
  animate: {
    opacity: 1,
    scale: 1,
    transition: { type: 'spring', stiffness: 400, damping: 15 },
  },
  exit: { opacity: 0, scale: 0.8 },
}

/* ── Stagger Containers ── */
export const staggerContainer: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
}

export const staggerFast: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.03,
      delayChildren: 0.05,
    },
  },
}

export const staggerSlow: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.15,
    },
  },
}

export const staggerItem: Variants = {
  initial: { opacity: 0, y: 15 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 24 },
  },
}

export const staggerItemScale: Variants = {
  initial: { opacity: 0, scale: 0.9, y: 10 },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 24 },
  },
}

/* ── Hover & Tap ── */
export const cardHover = {
  scale: 1.02,
  y: -4,
  transition: { type: 'spring' as const, stiffness: 400, damping: 17 },
}

export const cardHoverSubtle = {
  y: -2,
  transition: { type: 'spring' as const, stiffness: 400, damping: 20 },
}

export const buttonTap = {
  scale: 0.97,
}

export const buttonPulse = {
  scale: [1, 1.05, 1],
  transition: { duration: 0.3 },
}

/* ── Modal ── */
export const modalOverlay: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
}

export const modalContent: Variants = {
  initial: { opacity: 0, scale: 0.95, y: 20 },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 25 },
  },
  exit: { opacity: 0, scale: 0.95, y: 20 },
}

/* ── Toast ── */
export const toastVariants: Variants = {
  initial: { opacity: 0, x: 100, scale: 0.95 },
  animate: { opacity: 1, x: 0, scale: 1 },
  exit: { opacity: 0, x: 100, scale: 0.95 },
}

/* ── Shimmer / Loading ── */
export const shimmer: Variants = {
  initial: { opacity: 0.5 },
  animate: {
    opacity: [0.5, 1, 0.5],
    transition: { duration: 1.5, repeat: Infinity, ease: 'easeInOut' },
  },
}

/* ── Counter Animation Helper ── */
export const counterSpring = {
  type: 'spring' as const,
  stiffness: 100,
  damping: 20,
}

/* ── List Reorder ── */
export const listItemLayout = {
  layout: true,
  transition: {
    type: 'spring' as const,
    stiffness: 300,
    damping: 30,
  },
}
