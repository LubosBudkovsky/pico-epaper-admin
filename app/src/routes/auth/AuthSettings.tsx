import { useEffect, useState } from 'react';
import {
  Button,
  Divider,
  Fieldset,
  Group,
  PasswordInput,
  Stack,
  Switch,
} from '@mantine/core';
import { useNavigate } from 'react-router-dom';
import { useApiData } from '@/hooks/useApiData';
import { apiRequest } from '@/lib/apiRequest';
import { useAuth } from '@/modules/AuthProvider';
import FormSkeleton from '@/components/FormSkeleton';

interface AuthConfigData {
  enabled: boolean;
}

export default function AuthSettings() {
  const auth = useAuth();
  const navigate = useNavigate();
  const { data, loading } = useApiData<AuthConfigData>('/api/auth/config');

  const [enabled, setEnabled] = useState(false);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (!loading && data && !initialized) {
      setEnabled(data.enabled);
      setInitialized(true);
    }
  }, [data, loading, initialized]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    const body = enabled ? { enabled: true, password } : { enabled: false };
    const result = await apiRequest<{ ok: boolean }>({
      url: '/api/auth/config',
      method: 'POST',
      body,
      successMessage: enabled ? 'Authentication enabled' : 'Authentication disabled',
      returnJson: true,
    });
    setSubmitting(false);
    if (result && (result as { ok: boolean }).ok) {
      if (enabled) {
        // Auth was just enabled — session revoked, must log in
        auth.setGuest();
        navigate('/login', { replace: true });
      } else {
        // Auth was just disabled — refetch so state becomes 'open', go home
        auth.refetch();
        navigate('/', { replace: true });
      }
    }
  }

  if (loading || !initialized) return <FormSkeleton title="Security" />;

  const wasEnabled = data?.enabled ?? false;
  const passwordMismatch = !!confirmPassword && password !== confirmPassword;
  const submitDisabled =
    enabled && (!password || passwordMismatch);

  return (
    <Fieldset legend="Security">
      <form onSubmit={handleSubmit}>
        <Stack>
          <Switch
            label="Enable password protection"
            checked={enabled}
            onChange={(e) => {
              setEnabled(e.currentTarget.checked);
              setPassword('');
              setConfirmPassword('');
            }}
          />
          {enabled && (
            <>
              <Divider />
              <PasswordInput
                label={wasEnabled ? 'New password' : 'Password'}
                value={password}
                onChange={(e) => setPassword(e.currentTarget.value)}
                required
                autoFocus
              />
              <PasswordInput
                label="Confirm password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.currentTarget.value)}
                required
                error={passwordMismatch ? 'Passwords do not match' : undefined}
              />
            </>
          )}

          <Divider />

          <Group justify="end">
            <Button type="submit" loading={submitting} disabled={submitDisabled}>
              Save
            </Button>
          </Group>
        </Stack>
      </form>
    </Fieldset>
  );
}
