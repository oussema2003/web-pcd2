import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { API_BASE_URL, AppRole, AuthUser, apiFetch } from "@/api/client";

interface AuthContextType {
  user: AuthUser | null;
  role: AppRole | null;
  loading: boolean;
  signUp: (email: string, password: string, username: string, role: AppRole) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const ACCESS_TOKEN_KEY = "accessToken";
const REFRESH_TOKEN_KEY = "refreshToken";
const USER_KEY = "authUser";

function persistAuth(tokens: { access: string; refresh: string }, user: AuthUser) {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearAuthStorage() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [role, setRole] = useState<AppRole | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedUser = localStorage.getItem(USER_KEY);
    const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);

    if (storedUser && accessToken) {
      try {
        const parsed: AuthUser = JSON.parse(storedUser);
        setUser(parsed);
        setRole(parsed.role);
      } catch {
        clearAuthStorage();
      }
    }
    setLoading(false);
  }, []);

  const signUp = async (email: string, password: string, username: string, role: AppRole) => {
    try {
      await apiFetch("/auth/register/", {
        method: "POST",
        body: JSON.stringify({ email, password, username, role }),
      });

      // Auto-login après inscription pour garder le même comportement que l'UI existante
      await signIn(email, password);
    } catch (error: any) {
      const message = error?.message || "Erreur lors de la création du compte. Vérifiez que le serveur backend est démarré.";
      throw new Error(message);
    }
  };

  const signIn = async (email: string, password: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const message = data?.detail || data?.error || "Identifiants invalides";
        throw new Error(message);
      }

      const tokens = { access: data.access as string, refresh: data.refresh as string };
      const authUser = data.user as AuthUser;

      persistAuth(tokens, authUser);
      setUser(authUser);
      setRole(authUser.role);
    } catch (error: any) {
      // Si c'est une erreur réseau, donner un message plus clair
      if (error?.message === "Failed to fetch" || error?.name === "TypeError") {
        throw new Error("Impossible de se connecter au serveur. Vérifiez que le backend est démarré sur http://localhost:8000");
      }
      throw error;
    }
  };

  const signOut = async () => {
    try {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
      if (refreshToken) {
        // Mettre le refresh token en blacklist côté serveur
        await fetch(`${API_BASE_URL}/auth/token/blacklist/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ refresh: refreshToken }),
        }).catch(() => {
          // Ignorer les erreurs de blacklist
        });
      }
      // Appel logout pour cohérence
      await apiFetch("/auth/logout/", {
        method: "POST",
      }).catch(() => {
        // l'échec de logout côté serveur ne doit pas bloquer la déconnexion côté client
      });
    } catch {
      // l'échec de logout côté serveur ne doit pas bloquer la déconnexion côté client
    } finally {
      clearAuthStorage();
      setUser(null);
      setRole(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, role, loading, signUp, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
