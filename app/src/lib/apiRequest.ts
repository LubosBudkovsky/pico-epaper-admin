import { notifications } from '@mantine/notifications';

type ApiRequestOptions = {
  url: string;
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  successMessage?: string;
  errorMessage?: string;
  returnJson?: boolean;
  showNotifications?: boolean;
  signal?: AbortSignal;
};

export async function apiRequest<T = unknown>({
  url,
  method = 'GET',
  body,
  successMessage = 'Success',
  returnJson = false,
  showNotifications = true,
  signal,
}: ApiRequestOptions): Promise<T | void> {
  // Vite dev server proxies /api/* to the device via VITE_DEVICE_IP
  const resolvedUrl = url;
  try {
    const response = await fetch(`${resolvedUrl}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      credentials: "include",
      signal,
    });

    if (!response.ok) {     
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        const errorData = await response.json();
        let serverMessage: string
        if ( errorData?.detail[0]?.msg ) {
          serverMessage = errorData?.detail[0]?.msg.replace( /^Value error,\s*/i, '' );
        } else {
          serverMessage = errorData?.message || errorData?.error || errorData?.detail || 'Unknown error';
        }
        throw new Error(`${serverMessage}`);
      } else {
        throw new Error(response.statusText);
      }
    }

    if (successMessage && showNotifications) {
      notifications.show({
        message: successMessage,
        color: 'green',
      });
    }

    if (returnJson) {
      return (await response.json()) as T
    } else {
      return response as T
    }

  } catch (err) {
    if ( showNotifications ) {
      const message = err instanceof Error ? err.message : String(err);
      notifications.show({
        title: 'Error',
        message,
        color: 'red',
      });
    }
  }
}