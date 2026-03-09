import { Navigate } from 'react-router-dom';
import type { AuthState } from './AuthProvider';

export default function RequireAuth({
  children,
  state,
}: {
  children: React.ReactNode;
  state: AuthState;
}) {

  if (state.status === 'loading') return null;
  if (state.status === 'guest') {
    return (
      <Navigate
        to={`/login`}
        replace
      />
    );
  }
  // 'open' or 'authed' — allow through
  return <>{children}</>;
}
