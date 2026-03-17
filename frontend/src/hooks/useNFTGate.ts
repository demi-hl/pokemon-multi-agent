/**
 * Hook to check if the connected wallet holds a Locals Only NFT on HyperEVM.
 * Returns { hasAccess, isLoading, isChecking, error, recheckAccess }.
 */
import { useState, useEffect, useCallback } from 'react'
import { useAccount, useReadContract } from 'wagmi'
import { LOCALS_ONLY_CONTRACT, ERC721_ABI } from '@/lib/web3-config'

const CACHE_KEY = 'pokeagent-nft-gate'
const CACHE_TTL = 10 * 60_000 // 10 minutes

interface NFTGateResult {
  hasAccess: boolean
  isLoading: boolean
  isChecking: boolean
  error: string | null
  recheckAccess: () => void
}

function getCachedAccess(address: string): boolean | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (parsed.address?.toLowerCase() !== address.toLowerCase()) return null
    if (Date.now() - parsed.timestamp > CACHE_TTL) return null
    return parsed.hasAccess
  } catch {
    return null
  }
}

function setCachedAccess(address: string, hasAccess: boolean) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      address: address.toLowerCase(),
      hasAccess,
      timestamp: Date.now(),
    }))
  } catch { /* ignore */ }
}

export function useNFTGate(): NFTGateResult {
  const { address, isConnected } = useAccount()
  const [hasAccess, setHasAccess] = useState(false)
  const [checkedFromCache, setCheckedFromCache] = useState(false)

  // Check cache on address change
  useEffect(() => {
    if (address && isConnected) {
      const cached = getCachedAccess(address)
      if (cached !== null) {
        setHasAccess(cached)
        setCheckedFromCache(true)
      } else {
        setCheckedFromCache(false)
      }
    } else {
      setHasAccess(false)
      setCheckedFromCache(false)
    }
  }, [address, isConnected])

  // On-chain balanceOf check
  const { data: balance, isLoading: isChecking, error: contractError, refetch } = useReadContract({
    address: LOCALS_ONLY_CONTRACT,
    abi: ERC721_ABI,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
    query: {
      enabled: !!address && isConnected && !checkedFromCache,
    },
  })

  // Update access based on on-chain result
  useEffect(() => {
    if (balance !== undefined && address) {
      const owns = BigInt(balance) > 0n
      setHasAccess(owns)
      setCachedAccess(address, owns)
    }
  }, [balance, address])

  // In dev mode, if contract call fails, grant access
  useEffect(() => {
    if (contractError && address && import.meta.env.DEV) {
      console.warn('[NFT Gate] Contract check failed, granting dev access:', contractError.message)
      setHasAccess(true)
      setCachedAccess(address, true)
    }
  }, [contractError, address])

  const recheckAccess = useCallback(() => {
    if (address) {
      localStorage.removeItem(CACHE_KEY)
      setCheckedFromCache(false)
      refetch()
    }
  }, [address, refetch])

  return {
    hasAccess,
    isLoading: !isConnected,
    isChecking: isChecking && !checkedFromCache,
    error: contractError && !import.meta.env.DEV ? 'Failed to verify NFT ownership.' : null,
    recheckAccess,
  }
}
