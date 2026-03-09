import { AppShell, Burger, Button, Group } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { Outlet } from 'react-router';
import MainNavigation from './MainNavigation';
import { NavigationProgress } from '@mantine/nprogress';
import { useAuth } from '@/modules/AuthProvider';
import { apiRequest } from '@/lib/apiRequest';
import { useState } from 'react';

export default function Layout() {
  const [opened, { close, toggle }] = useDisclosure();
  const auth = useAuth();
  const [logoutLoading, setLogoutLoading] = useState(false)

  async function handleLogout() {
    try {
      setLogoutLoading(true)
      await apiRequest({
        url: '/api/auth/logout',
        method: 'POST',
        successMessage: 'Signed out',
      });
      auth.setGuest();
    } finally {
      setLogoutLoading(false)
    }
  }

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{
        width: 220,
        breakpoint: 'sm',
        collapsed: { mobile: !opened },
      }}
      padding="md"
    >
      <AppShell.Header>
        <NavigationProgress withinPortal={false} />
        <Group h="100%" px="md" justify="space-between">
          <Group gap="xs">
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <div>
              Pico<strong>Epaper</strong>Admin
            </div>
          </Group>                      
          {auth.state.status === 'authed' && (
            <Group gap="xs">
            <Button variant="subtle" size="xs" onClick={handleLogout} loading={logoutLoading}>
              Sign out
            </Button>
            </Group>
          )}          
        </Group>
      </AppShell.Header>

      <AppShell.Navbar>
        <MainNavigation close={close} />
      </AppShell.Navbar>

      <AppShell.Main>        
        <Outlet />        
      </AppShell.Main>
    </AppShell>
  );
}
