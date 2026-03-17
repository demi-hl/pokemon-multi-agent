/**
 * Web3 / WalletConnect configuration for NFT token gating.
 *
 * Token gate: Locals Only NFT by DEMI on HyperEVM (Hyperliquid).
 * Contract: 0x62FCFAf7573AD8B41a0FBF347AfEb85e06599A75
 * Supply: 500 | Standard: ERC-721
 *
 * Uses wagmi + viem + Reown AppKit (WalletConnect).
 */
import { http, createConfig } from 'wagmi'
import { defineChain } from 'viem'
import { injected, walletConnect } from 'wagmi/connectors'

// ── HyperEVM chain definition ──
export const hyperEVM = defineChain({
  id: 999,
  name: 'HyperEVM',
  nativeCurrency: { name: 'HYPE', symbol: 'HYPE', decimals: 18 },
  rpcUrls: {
    default: { http: ['https://rpc.hyperliquid.xyz/evm'] },
  },
  blockExplorers: {
    default: { name: 'HyperEVM Explorer', url: 'https://hyperevmscan.io' },
  },
})

// ── Locals Only NFT contract (ERC-721 by DEMI) ──
export const LOCALS_ONLY_CONTRACT = '0x62FCFAf7573AD8B41a0FBF347AfEb85e06599A75' as const
export const LOCALS_ONLY_SUPPLY = 500

// ── WalletConnect Project ID ──
// Get yours at https://cloud.reown.com
export const WALLETCONNECT_PROJECT_ID = import.meta.env.VITE_WALLETCONNECT_PROJECT_ID || 'demo-project-id'

// ── Wagmi config ──
export const wagmiConfig = createConfig({
  chains: [hyperEVM],
  connectors: [
    injected(),
    walletConnect({ projectId: WALLETCONNECT_PROJECT_ID }),
  ],
  transports: {
    [hyperEVM.id]: http(),
  },
})

// ── ERC-721 balanceOf ABI (minimal) ──
export const ERC721_ABI = [
  {
    name: 'balanceOf',
    type: 'function',
    stateMutability: 'view',
    inputs: [{ name: 'owner', type: 'address' }],
    outputs: [{ name: '', type: 'uint256' }],
  },
] as const
