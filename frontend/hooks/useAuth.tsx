import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { api } from '@/lib/api';

interface User { id: string; name: string; email: string; phone?: string; role: string; status: string; created_at: string; }
interface AuthContextType { user: User | null; login: (email: string, password: string) => Promise<void>; register: (data: any) => Promise<void>; logout: () => void; loading: boolean; }

const AuthContext = createContext<AuthContextType>(null!);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { const token = localStorage.getItem('token'); if (token) { api.get<User>('/api/auth/refresh').then(u => setUser(u)).catch(() => localStorage.removeItem('token')).finally(() => setLoading(false)); } else { setLoading(false); } }, []);

  const login = async (email: string, password: string) => {
    const res = await api.post<{ access_token: string; user: User }>('/api/auth/login', { email, password });
    localStorage.setItem('token', res.access_token);
    setUser(res.user);
  };

  const register = async (data: any) => {
    const res = await api.post<{ access_token: string; user: User }>('/api/auth/register', data);
    localStorage.setItem('token', res.access_token);
    setUser(res.user);
  };

  const logout = () => { localStorage.removeItem('token'); setUser(null); };

  return <AuthContext.Provider value={{ user, login, register, logout, loading }}>{children}</AuthContext.Provider>;
}
