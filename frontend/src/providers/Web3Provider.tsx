/**
 * Web3Provider — wraps the app with wagmi + WalletConnect + React Query.
 * Uses the existing QueryClient from main.tsx (passed as prop).
 */
import type { ReactNode } from 'react'
import { WagmiProvider } from 'wagmi'
import { wagmiConfig } from '@/lib/web3-config'

export default function Web3Provider({ children }: { children: ReactNode }) {
  return (
    <WagmiProvider config={wagmiConfig}>
      {children}
    </WagmiProvider>
  )
}
