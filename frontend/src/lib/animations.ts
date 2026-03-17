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
    transition: { type: 'tween', duration: 0.3, ease: [0.22, 1, 0.36, 1] },
  },
}

export const staggerItemScale: Variants = {
  initial: { opacity: 0, scale: 0.9, y: 10 },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { type: 'tween', duration: 0.3, ease: [0.22, 1, 0.36, 1] },
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

/* ── Animated Number Counter ── */
export const numberCounter: Variants = {
  hidden: { opacity: 0 },
  visible: (custom: number) => ({
    opacity: 1,
    transition: { duration: 1.2, ease: 'easeOut' },
  }),
}

/* ── Glow Pulse for Accent Elements ── */
export const glowPulse = {
  animate: {
    boxShadow: [
      '0 0 0 0 rgba(96, 165, 250, 0)',
      '0 0 20px 4px rgba(96, 165, 250, 0.3)',
      '0 0 0 0 rgba(96, 165, 250, 0)',
    ],
    transition: { duration: 2, repeat: Infinity, ease: 'easeInOut' },
  },
}

/* ── Card 3D Tilt on Hover ── */
export const cardTilt = {
  rest: { rotateX: 0, rotateY: 0, scale: 1 },
  hover: { scale: 1.03, transition: { duration: 0.3, ease: 'easeOut' } },
}

/* ── Progress Bar Fill Animation ── */
export const progressFill: Variants = {
  hidden: { scaleX: 0, originX: 0 },
  visible: (custom: number) => ({
    scaleX: custom,
    originX: 0,
    transition: { duration: 1, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.2 },
  }),
}

/* ── Ripple Effect for Buttons ── */
export const ripple = {
  initial: { scale: 0, opacity: 0.5 },
  animate: { scale: 4, opacity: 0 },
  transition: { duration: 0.6, ease: 'easeOut' },
}

/* ── Chart Line Draw ── */
export const chartDraw: Variants = {
  hidden: { pathLength: 0, opacity: 0 },
  visible: {
    pathLength: 1,
    opacity: 1,
    transition: { duration: 1.5, ease: 'easeInOut' },
  },
}

/* ── Typewriter Text Reveal ── */
export const typewriter: Variants = {
  hidden: { width: '0%' },
  visible: {
    width: '100%',
    transition: { duration: 1, ease: 'linear' },
  },
}

/* ── Floating Animation ── */
export const floating = {
  animate: {
    y: [0, -8, 0],
    transition: { duration: 3, repeat: Infinity, ease: 'easeInOut' },
  },
}

/* ── Stagger List with Scale ── */
export const staggerListScale: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.1 },
  },
}

export const staggerListScaleItem: Variants = {
  hidden: { opacity: 0, scale: 0.9, y: 10 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { type: 'tween', duration: 0.3, ease: [0.22, 1, 0.36, 1] },
  },
}

/* ── Price Flash (green up, red down) ── */
export const priceFlashUp = {
  initial: { backgroundColor: 'rgba(52, 211, 153, 0)' },
  animate: {
    backgroundColor: ['rgba(52, 211, 153, 0.3)', 'rgba(52, 211, 153, 0)'],
    transition: { duration: 1, ease: 'easeOut' },
  },
}

export const priceFlashDown = {
  initial: { backgroundColor: 'rgba(248, 113, 113, 0)' },
  animate: {
    backgroundColor: ['rgba(248, 113, 113, 0.3)', 'rgba(248, 113, 113, 0)'],
    transition: { duration: 1, ease: 'easeOut' },
  },
}

// ===== New Enhanced Animations =====

/** Animated number counter config for useSpring */
export const numberCounterSpring = {
  type: "spring" as const,
  stiffness: 50,
  damping: 15,
  duration: 1.2,
};

/** Glow pulse for accent elements */
export const glowPulseAccent = {
  animate: {
    boxShadow: [
      "0 0 0 0 rgba(96, 165, 250, 0)",
      "0 0 20px 4px rgba(96, 165, 250, 0.3)",
      "0 0 0 0 rgba(96, 165, 250, 0)",
    ],
  },
  transition: {
    duration: 2,
    repeat: Infinity,
    ease: "easeInOut" as const,
  },
};

/** Card 3D flip animation */
export const cardFlip = {
  initial: { rotateY: 0 },
  animate: { rotateY: 180 },
  transition: { duration: 0.6, ease: "easeInOut" as const },
};

/** Progress bar fill with easing */
export const progressFillAnimated = {
  initial: { width: "0%" },
  animate: (percent: number) => ({ width: `${percent}%` }),
  transition: { duration: 1, ease: [0.33, 1, 0.68, 1] },
};

/** Animated list item for stagger children */
export const listItem = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  transition: { type: "spring" as const, stiffness: 300, damping: 24 },
};

/** Chart line draw animation */
export const chartDrawLine = {
  initial: { pathLength: 0, opacity: 0 },
  animate: { pathLength: 1, opacity: 1 },
  transition: { duration: 1.5, ease: "easeInOut" as const },
};

/** Ripple click effect */
export const rippleClick = {
  initial: { scale: 0, opacity: 0.5 },
  animate: { scale: 4, opacity: 0 },
  transition: { duration: 0.6, ease: "easeOut" as const },
};

/** Price flash animation (for price changes) */
export const priceFlashGreen = {
  animate: {
    backgroundColor: ["rgba(52, 211, 153, 0.3)", "rgba(52, 211, 153, 0)"],
  },
  transition: { duration: 1.5, ease: "easeOut" as const },
};

export const priceFlashRed = {
  animate: {
    backgroundColor: ["rgba(248, 113, 113, 0.3)", "rgba(248, 113, 113, 0)"],
  },
  transition: { duration: 1.5, ease: "easeOut" as const },
};

/** Typewriter effect config */
export const typewriterEffect = {
  initial: { width: 0 },
  animate: { width: "100%" },
  transition: { duration: 2, ease: "linear" as const },
};

/** Hover scale with glow */
export const hoverGlow = {
  whileHover: {
    scale: 1.03,
    boxShadow: "0 0 30px rgba(96, 165, 250, 0.15)",
  },
  transition: { type: "spring" as const, stiffness: 400, damping: 25 },
};

/** Entrance from bottom with bounce */
export const bounceIn = {
  initial: { opacity: 0, y: 40, scale: 0.95 },
  animate: { opacity: 1, y: 0, scale: 1 },
  transition: { type: "spring" as const, stiffness: 260, damping: 20 },
};

/** Pulse badge animation */
export const pulseBadge = {
  animate: {
    scale: [1, 1.1, 1],
    opacity: [1, 0.8, 1],
  },
  transition: {
    duration: 1.5,
    repeat: Infinity,
    ease: "easeInOut" as const,
  },
};
