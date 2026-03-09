import { createContext, useContext, useEffect, useState } from 'react';
import { useApiData } from '@/hooks/useApiData';

interface AuthMeData {
  protected: boolean;
  authed?: boolean;
}

export type AuthState =
  | { status: 'loading' }
  | { status: 'open' }    // no password configured — all routes public
  | { status: 'authed' }  // password configured, logged in
  | { status: 'guest' };  // password configured, not logged in

const Ctx = createContext<{
  state: AuthState;
  refetch: () => void;
  setGuest: () => void;
} | null>(null);

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const { data, loading, refetch } = useApiData<AuthMeData>('/api/auth/me');
  const [state, setState] = useState<AuthState>({ status: 'loading' });

  useEffect(() => {
    if (loading) {
      setState({ status: 'loading' });
    } else if (!data?.protected) {
      setState({ status: 'open' });
    } else if (data.authed) {
      setState({ status: 'authed' });
    } else {
      setState({ status: 'guest' });
    }
  }, [data, loading]);

  return (
    <Ctx.Provider value={{ state, refetch, setGuest: () => setState({ status: 'guest' }) }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
