/**
 * HTTP Client with in-memory access token storage, automatic cookie-based refresh rotation,
 * and 401 interception dispatching session expiration events.
 */

let inMemoryToken: string | null = null;
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: any) => void;
  reject: (reason?: any) => void;
}> = [];

export function getAccessToken(): string | null {
  return inMemoryToken;
}

export function setAccessToken(token: string | null) {
  inMemoryToken = token;
}

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

export const SESSION_EXPIRED_EVENT = 'nutrition_app:session_expired';

export function dispatchSessionExpired() {
  setAccessToken(null);
  window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
}

export async function apiClient<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const token = getAccessToken();
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include', // sends and receives httpOnly refresh cookie
  };

  const response = await fetch(endpoint, config);

  // If 401 Unauthorized and not an auth attempt itself
  if (
    response.status === 401 &&
    !endpoint.includes('/auth/login') &&
    !endpoint.includes('/auth/register') &&
    !endpoint.includes('/auth/refresh')
  ) {
    if (isRefreshing) {
      // Queue requests until refresh finishes
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((newToken) => {
        headers.set('Authorization', `Bearer ${newToken}`);
        return fetch(endpoint, { ...config, headers }).then((res) => {
          if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
          return res.json();
        });
      });
    }

    isRefreshing = true;

    try {
      // Attempt silent refresh via httpOnly cookie
      const refreshRes = await fetch('/auth/refresh', {
        method: 'POST',
        credentials: 'include',
      });

      if (!refreshRes.ok) {
        throw new Error('Refresh token expired or invalid');
      }

      const refreshData = await refreshRes.json();
      const newToken = refreshData.access_token;
      setAccessToken(newToken);
      processQueue(null, newToken);

      // Replay original request with new token
      headers.set('Authorization', `Bearer ${newToken}`);
      const retryRes = await fetch(endpoint, { ...config, headers });
      if (!retryRes.ok) {
        throw new Error(`HTTP Error ${retryRes.status}`);
      }
      return retryRes.json();
    } catch (refreshErr) {
      processQueue(refreshErr as Error, null);
      dispatchSessionExpired();
      throw refreshErr;
    } finally {
      isRefreshing = false;
    }
  }

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      // ignore json parse error
    }
    const err = new Error(errorDetail);
    (err as any).status = response.status;
    throw err;
  }

  // Handle blob or json
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/pdf')) {
    return (await response.blob()) as unknown as T;
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}
