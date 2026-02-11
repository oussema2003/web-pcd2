const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export type AppRole = "rh" | "candidate";

export interface AuthUser {
  id: number;
  email: string;
  username: string;
  role: AppRole;
}

const ACCESS_TOKEN_KEY = "accessToken";
const REFRESH_TOKEN_KEY = "refreshToken";

function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_URL}/auth/token/refresh/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    const newAccessToken = data.access;
    localStorage.setItem(ACCESS_TOKEN_KEY, newAccessToken);
    return newAccessToken;
  } catch {
    return null;
  }
}

export async function apiFetch<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_URL}${path}`;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  let token = getAccessToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch (error: any) {
    // Erreur réseau (serveur non accessible)
    throw new Error(
      `Impossible de se connecter au serveur backend. Vérifiez que le serveur Django est démarré sur ${API_URL.replace('/api', '')}`
    );
  }

  // Si le token a expiré (401), essayer de le rafraîchir
  if (response.status === 401 && token && getRefreshToken()) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers["Authorization"] = `Bearer ${newToken}`;
      try {
        response = await fetch(url, {
          ...options,
          headers,
        });
      } catch (error: any) {
        throw new Error(
          `Impossible de se connecter au serveur backend. Vérifiez que le serveur Django est démarré sur ${API_URL.replace('/api', '')}`
        );
      }
    }
  }

  if (response.status === 204) {
    // No content
    return null as T;
  }

  let data: any = null;
  try {
    data = await response.json();
  } catch {
    // ignore json parse error for empty bodies
  }

  if (!response.ok) {
    const message = data?.detail || data?.error || "Une erreur est survenue";
    throw new Error(message);
  }

  return data as T;
}

export const API_BASE_URL = API_URL;

