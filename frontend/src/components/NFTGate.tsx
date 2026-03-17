/**
 * NFTGate — blocks access to the app unless the user holds a Locals Only NFT.
 * Shows a premium "access denied" screen with wallet connect option.
 */
import { motion } from 'framer-motion'
import { useAccount, useConnect, useDisconnect } from 'wagmi'
import { injected } from 'wagmi/connectors'
import { useNFTGate } from '@/hooks/useNFTGate'
import { LOCALS_ONLY_CONTRACT } from '@/lib/web3-config'
import { Shield, Wallet, ExternalLink, Loader2, RefreshCw, LogOut } from 'lucide-react'

interface NFTGateProps {
  children: React.ReactNode
}

export default function NFTGate({ children }: NFTGateProps) {
  const { address, isConnected } = useAccount()
  const { connect, connectors, isPending: isConnecting } = useConnect()
  const { disconnect } = useDisconnect()
  const { hasAccess, isChecking, error, recheckAccess } = useNFTGate()

  // If connected and has access, render children
  if (isConnected && hasAccess && !isChecking) {
    return <>{children}</>
  }

  const truncatedAddress = address
    ? `${address.slice(0, 6)}...${address.slice(-4)}`
    : null

  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center relative overflow-hidden">
      {/* Background effects */}
      <div className="particles-bg" aria-hidden="true" />
      <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 via-transparent to-purple-500/5" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 max-w-md w-full mx-4"
      >
        {/* Card */}
        <div className="bg-surface/80 backdrop-blur-2xl border border-white/[0.08] rounded-2xl p-8 shadow-2xl">
          {/* Pokeball icon */}
          <div className="flex justify-center mb-6">
            <motion.div
              animate={{ y: [0, -4, 0] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
              className="relative"
            >
              <svg
                viewBox="0 0 100 100"
                className="w-16 h-16 drop-shadow-[0_0_25px_rgba(239,68,68,0.15)]"
              >
                <path d="M 4 50 A 46 46 0 0 1 96 50" fill="none" stroke="#ef4444" strokeWidth="3.5" strokeLinecap="round" />
                <path d="M 96 50 A 46 46 0 0 1 4 50" fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth="3.5" strokeLinecap="round" />
                <line x1="4" y1="50" x2="96" y2="50" stroke="#52525b" strokeWidth="3.5" />
                <circle cx="50" cy="50" r="14" fill="none" stroke="#52525b" strokeWidth="3.5" />
                <circle cx="50" cy="50" r="7" fill="white" filter="drop-shadow(0 0 6px rgba(255,255,255,0.4))" />
              </svg>
              <div className="absolute -inset-3 rounded-full bg-red-500/10 blur-xl" />
            </motion.div>
          </div>

          {/* Title */}
          <h1 className="text-xl font-bold text-center mb-2">
            Token-Gated Access
          </h1>
          <p className="text-sm text-muted-foreground text-center mb-6">
            Hold a{' '}
            <a
              href="https://drip.trade/collections/locals-only"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:underline inline-flex items-center gap-1"
            >
              Locals Only NFT
              <ExternalLink className="w-3 h-3" />
            </a>{' '}
            on HyperEVM to access PokeAgent.
          </p>

          {/* Status */}
          {!isConnected ? (
            <>
              {/* Connect wallet buttons */}
              <div className="space-y-3">
                {connectors.map((connector) => (
                  <motion.button
                    key={connector.uid}
                    onClick={() => connect({ connector })}
                    disabled={isConnecting}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full flex items-center justify-center gap-2 h-12 rounded-xl text-sm font-semibold bg-accent text-white hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-accent/20 transition-all duration-200"
                  >
                    {isConnecting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Wallet className="w-4 h-4" />
                    )}
                    {connector.name === 'Injected' ? 'Connect Wallet' : connector.name}
                  </motion.button>
                ))}
              </div>

              <p className="text-xs text-muted-foreground/50 text-center mt-4">
                Supports MetaMask, WalletConnect, and other wallets
              </p>
            </>
          ) : isChecking ? (
            /* Checking NFT ownership */
            <div className="flex flex-col items-center gap-3 py-4">
              <Loader2 className="w-6 h-6 text-accent animate-spin" />
              <p className="text-sm text-muted-foreground">
                Checking NFT ownership...
              </p>
              <p className="text-xs text-muted-foreground/50 font-mono">
                {truncatedAddress}
              </p>
            </div>
          ) : !hasAccess ? (
            /* No NFT found */
            <div className="space-y-4">
              <div className="bg-rose-500/10 border border-rose-500/20 rounded-xl p-4 text-center">
                <p className="text-sm text-rose-400 font-medium mb-1">
                  No Locals Only NFT found
                </p>
                <p className="text-xs text-muted-foreground">
                  Wallet: <span className="font-mono">{truncatedAddress}</span>
                </p>
              </div>

              {error && (
                <p className="text-xs text-rose-400/80 text-center">{error}</p>
              )}

              <div className="flex gap-2">
                <motion.button
                  onClick={recheckAccess}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex-1 flex items-center justify-center gap-2 h-10 rounded-xl text-sm font-medium bg-white/[0.06] border border-white/[0.08] text-foreground hover:bg-white/[0.1] transition-all duration-200"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Re-check
                </motion.button>
                <motion.button
                  onClick={() => disconnect()}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex-1 flex items-center justify-center gap-2 h-10 rounded-xl text-sm font-medium bg-white/[0.06] border border-white/[0.08] text-muted-foreground hover:text-foreground hover:bg-white/[0.1] transition-all duration-200"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Disconnect
                </motion.button>
              </div>

              <a
                href="https://drip.trade/collections/locals-only"
                target="_blank"
                rel="noopener noreferrer"
                className="block"
              >
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="w-full flex items-center justify-center gap-2 h-12 rounded-xl text-sm font-semibold bg-gradient-to-r from-accent to-purple-500 text-white shadow-lg transition-all duration-200"
                >
                  Get a Locals Only NFT
                  <ExternalLink className="w-3.5 h-3.5" />
                </motion.div>
              </a>
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <p className="text-[10px] text-muted-foreground/30 text-center mt-4">
          Contract: {LOCALS_ONLY_CONTRACT.slice(0, 10)}... on HyperEVM
        </p>
      </motion.div>
    </div>
  )
}
