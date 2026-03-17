import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../lib/utils';

interface OptimizedImageProps {
  src: string;
  alt: string;
  fallbackSrc?: string;
  className?: string;
  containerClassName?: string;
  width?: number;
  height?: number;
  /** Enable zoom on hover */
  zoomOnHover?: boolean;
  /** Enable holographic shine effect on hover */
  holoEffect?: boolean;
  /** Show loading skeleton */
  showSkeleton?: boolean;
  /** Aspect ratio for container (e.g. "3/4" for cards) */
  aspectRatio?: string;
  /** Click handler */
  onClick?: () => void;
}

/**
 * Optimized image component with:
 * - Lazy loading via IntersectionObserver
 * - Blur-up placeholder transition
 * - Error fallback chain
 * - Optional zoom on hover
 * - Optional holographic shine effect
 * - Shimmer loading skeleton
 */
export function OptimizedImage({
  src,
  alt,
  fallbackSrc,
  className,
  containerClassName,
  width,
  height,
  zoomOnHover = false,
  holoEffect = false,
  showSkeleton = true,
  aspectRatio,
  onClick,
}: OptimizedImageProps) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const [inView, setInView] = useState(false);
  const [mousePos, setMousePos] = useState({ x: 0.5, y: 0.5 });
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Lazy loading with IntersectionObserver
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true);
          observer.disconnect();
        }
      },
      { rootMargin: '200px' }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Reset state when src changes — standard React pattern for prop-driven reset
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => {
    setLoaded(false);
    setError(false);
  }, [src]);

  const handleLoad = () => {
    // Detect images that "loaded" but are actually blocked (naturalWidth === 0)
    if (imgRef.current && imgRef.current.naturalWidth === 0) {
      handleError();
      return;
    }
    setLoaded(true);
  };

  const handleError = () => {
    if (!error && fallbackSrc) {
      setError(true);
    } else {
      setError(true);
      setLoaded(true); // Show placeholder
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!holoEffect || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    setMousePos({
      x: (e.clientX - rect.left) / rect.width,
      y: (e.clientY - rect.top) / rect.height,
    });
  };

  const currentSrc = error && fallbackSrc ? fallbackSrc : src;

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative overflow-hidden rounded-lg',
        zoomOnHover && 'group cursor-pointer',
        containerClassName
      )}
      style={aspectRatio ? { aspectRatio } : undefined}
      onClick={onClick}
      onMouseMove={handleMouseMove}
    >
      {/* Shimmer skeleton while loading */}
      {showSkeleton && !loaded && (
        <div className="absolute inset-0 bg-surface-elevated animate-shimmer rounded-lg" />
      )}

      {/* Actual image */}
      {inView && (
        <motion.img
          ref={imgRef}
          src={currentSrc}
          alt={alt}
          width={width}
          height={height}
          onLoad={handleLoad}
          onError={handleError}
          loading="lazy"
          referrerPolicy="no-referrer"
          initial={{ opacity: 0, filter: 'blur(10px)' }}
          animate={{
            opacity: loaded ? 1 : 0,
            filter: loaded ? 'blur(0px)' : 'blur(10px)',
          }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          className={cn(
            'w-full h-full object-cover',
            zoomOnHover && 'transition-transform duration-500 ease-out group-hover:scale-110',
            className
          )}
        />
      )}

      {/* Holographic shine overlay */}
      {holoEffect && loaded && (
        <div
          className="absolute inset-0 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300"
          style={{
            background: `radial-gradient(
              circle at ${mousePos.x * 100}% ${mousePos.y * 100}%,
              rgba(255, 255, 255, 0.15) 0%,
              rgba(96, 165, 250, 0.08) 30%,
              rgba(168, 85, 247, 0.05) 60%,
              transparent 80%
            )`,
          }}
        />
      )}

      {/* Error state placeholder */}
      {error && !fallbackSrc && (
        <div className="absolute inset-0 flex items-center justify-center bg-surface-elevated text-muted">
          <svg className="w-8 h-8 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
      )}
    </div>
  );
}
