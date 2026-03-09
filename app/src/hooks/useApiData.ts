import { useEffect, useState, useCallback } from 'react';
import { nprogress } from '@mantine/nprogress';
import { apiRequest } from '@/lib/apiRequest';

export function useApiData<T>(endpoint: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);

  const url = endpoint;

  const fetchData = useCallback(
    
    async (signal?: AbortSignal) => {

      setLoading(true);
      nprogress.start()

      try {
        const response = await apiRequest<{ ok: boolean; data: T }>({
            url,
            showNotifications: false,
            returnJson: true,
            signal,
          })

          // Only update state if request wasn't aborted
          if (!signal?.aborted) {
            if (response && 'data' in response) {
              setData(response.data);
            } else {
              setData(response as T);
            }
          }
      } catch (err: any) {
        // Ignore aborted requests
        if (err.name !== 'AbortError' && !signal?.aborted) {
          console.error(err);
        }
      } finally {
        // Only update loading if not aborted
        if (!signal?.aborted) {
          setLoading(false);
        }
        nprogress.complete()
      }

    }, [url]
  );

  useEffect(() => {
    const controller = new AbortController();
    fetchData(controller.signal);
    return () => {
      controller.abort();
    };
  }, [fetchData]);

  return { data, setData, loading, refetch: () => fetchData() };
}
