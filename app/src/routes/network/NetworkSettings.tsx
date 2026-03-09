import { useState } from 'react';
import { Alert, Stack } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { apiRequest } from '@/lib/apiRequest';
import { useApiData } from '@/hooks/useApiData';
import FormSkeleton from '@/components/FormSkeleton';
import NetworkSettingsForm, { type NetworkSettingsFormValues } from './NetworkSettingsForm';
import type { NetworkSettingsData, NetworkSettingsResponse } from '@/types/network';

export default function NetworkSettings() {

  const { data, loading } = useApiData<NetworkSettingsData>('/api/system/wifiap');

  const [formLoading, setFormLoading] = useState(false);
  const [rebooting, setRebooting] = useState(false);

  const handleSubmit = async (values: NetworkSettingsFormValues) => {
    try {
      setFormLoading(true);

      // Only send client_ssid and client_pass when client mode is enabled
      const body: NetworkSettingsFormValues = values?.client_enabled
        ? values
        : {       // Only send client_enabled and AP settings
          client_enabled: values?.client_enabled,
          ap_ssid: values.ap_ssid,
          ap_pass: values.ap_pass,
        };

      const updated = await apiRequest<NetworkSettingsResponse>({
        url: '/api/system/wifiap',
        method: 'PATCH',
        body,
        returnJson: true,
        showNotifications: false,
      });

      if (updated?.ok) {
        if (updated.reboot) {
          setRebooting(true);
        } else {
          notifications.show({ message: 'Network settings saved.', color: 'green' });
        }
      }
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <Stack>
      {loading
        ? <FormSkeleton title="Network Settings" />
        : rebooting
          ? <Alert color="orange" title="Device is rebooting">
              Network settings saved. The device is now rebooting to apply the changes.
              {data?.client_enabled
                ? ' Make sure your device connects to the configured WiFi network, then refresh this page.'
                : ' Once it restarts, connect to the access point and reopen this page.'}
            </Alert>
          : <NetworkSettingsForm
          initialValues={{
            client_enabled: data?.client_enabled,
            client_ssid: data?.client_ssid,
            country: data?.country ?? '',            hostname: data?.hostname ?? '',            ap_ssid: data?.ap_ssid,
            ap_pass: data?.ap_pass && data?.ap_pass_is_default ? data?.ap_pass : '',
            ap_pass_is_default: data?.ap_pass_is_default,
          }}
          onSubmit={handleSubmit}
          isLoading={loading || formLoading}
            />
      }
    </Stack>
  );
}