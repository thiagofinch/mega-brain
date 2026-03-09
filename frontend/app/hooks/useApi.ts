import useSWR, { SWRConfiguration } from 'swr'
import { cacheManager, CACHE_TTL, getCacheKey } from '@/lib/cache'

const fetcher = async (url: string) => {
  try {
    // Check local cache first
    const cacheKey = getCacheKey(url)
    const cachedData = cacheManager.get(cacheKey)
    if (cachedData) {
      return cachedData
    }

    const response = await fetch(url, {
      headers: {
        'Accept': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()

    // Store in cache with appropriate TTL
    const ttl = getTTLForEndpoint(url)
    cacheManager.set(cacheKey, data, ttl)

    return data
  } catch (error) {
    console.error('API Error:', error)
    throw error
  }
}

/**
 * Determine cache TTL based on endpoint
 */
const getTTLForEndpoint = (url: string): number => {
  if (url.includes('/api/kpi')) return CACHE_TTL.KPI
  if (url.includes('/api/sales')) return CACHE_TTL.SALES
  if (url.includes('/api/products')) return CACHE_TTL.PRODUCTS
  if (url.includes('/api/tariffs')) return CACHE_TTL.TARIFFS
  if (url.includes('/api/user')) return CACHE_TTL.USER
  return CACHE_TTL.SALES // default
}

interface UseApiOptions extends SWRConfiguration {
  skip?: boolean
}

export function useApi<T>(url: string, options?: UseApiOptions) {
  const shouldFetch = !options?.skip

  const { data, error, isLoading, mutate } = useSWR<T, Error>(
    shouldFetch ? url : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      dedupingInterval: 30000, // Reduced from 60s to 30s for fresher data
      errorRetryCount: 3,
      errorRetryInterval: 5000,
      keepPreviousData: true,
      ...options,
    }
  )

  return {
    data,
    error,
    isLoading,
    isError: !!error,
    mutate,
  }
}

export function useApiBatch<T extends Record<string, any>>(
  urls: Record<keyof T, string>,
  options?: UseApiOptions
): Record<keyof T, { data?: any; error?: Error; isLoading: boolean }> {
  const results: Record<keyof T, any> = {} as Record<keyof T, any>

  for (const key in urls) {
    const { data, error, isLoading } = useApi(urls[key], options)
    results[key] = { data, error, isLoading }
  }

  return results
}
