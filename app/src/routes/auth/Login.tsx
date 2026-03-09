import { useEffect } from 'react';
import { Button, Container, Paper, PasswordInput, Stack, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useNavigate } from 'react-router-dom';
import { apiRequest } from '@/lib/apiRequest';
import { useAuth } from '@/modules/AuthProvider';

export default function Login() {
  const auth = useAuth();
  const navigate = useNavigate();

  const next = '/';

  // No auth configured, or already logged in — nothing to do here
  useEffect(() => {
    if (auth.state.status === 'open' || auth.state.status === 'authed') {
      navigate(next, { replace: true });
    }
  }, [auth.state.status, navigate, next]);

  const form = useForm({
    initialValues: { password: '' },
  });

  async function handleSubmit(values: { password: string }) {
    // The login endpoint always returns HTTP 200 — ok:true on success,
    // ok:false on wrong password — so apiRequest never triggers a 401 redirect.
    const result = await apiRequest<{ ok: boolean; error?: string }>({
      url: '/api/auth/login',
      method: 'POST',
      body: { password: values.password },
      successMessage: 'Logged in',
      showNotifications: false,
      returnJson: true,
    });
    const data = result as { ok: boolean; error?: string } | undefined;
    if (data?.ok) {
      auth.refetch();
      navigate(next, { replace: true });
    } else {
      form.setFieldError('password', data?.error ?? 'Invalid password');
    }
  }

  return (
    <Container size={420} my={40}>
      <Title ta="center">
        Pico<strong>Epaper</strong>Admin
      </Title>
      <Paper withBorder shadow="sm" p={22} mt={30} radius="md">
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack>
            <PasswordInput
              label="Password"
              autoFocus
              {...form.getInputProps('password')}
            />
            <Button type="submit" loading={form.submitting} fullWidth>
              Sign in
            </Button>
          </Stack>
        </form>
      </Paper>
    </Container>
  );
}