import {
  Button,
  Fieldset,
  Group,
  Stack,
  TextInput,
  Switch,
  Text,
  Divider,
  PasswordInput,
  Alert,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useState } from 'react';

export type NetworkSettingsFormValues = {
  client_enabled?: boolean;
  client_ssid?: string;
  client_pass?: string;
  country?: string;
  hostname?: string;
  ap_ssid?: string;
  ap_pass?: string;
  ap_pass_is_default?: boolean;
};

type NetworkSettingsFormProps = {
  initialValues?: NetworkSettingsFormValues;
  onSubmit: (values: NetworkSettingsFormValues) => void;
  isLoading?: boolean;
};

export default function NetworkSettingsForm({ initialValues, onSubmit, isLoading }: NetworkSettingsFormProps) {

  const [hasDefaultApPass, setHasDefaultApPass] = useState(initialValues?.ap_pass_is_default)
  const [clientEnabled, setClientEnabled] = useState(initialValues?.client_enabled ?? false)
  const [requiresReboot, setRequiresReboot] = useState(false)

  const initClientEnabled = initialValues?.client_enabled ?? false

  const form = useForm<NetworkSettingsFormValues>({
    mode: 'uncontrolled',
    initialValues: {
      client_enabled: initialValues?.client_enabled,
      client_ssid: initialValues?.client_ssid ?? '',
      client_pass: '',
      country: initialValues?.country ?? '',
      hostname: initialValues?.hostname ?? '',
      ap_ssid: initialValues?.ap_ssid ?? '',
      ap_pass: initialValues?.ap_pass ?? '',
    },
    validate: {
      client_ssid: (value, values) =>
        values.client_enabled && !value ? 'Required' : null,
      client_pass: (value, values) =>
        values.client_enabled && !value ? 'Required' : null,
      ap_ssid: (value) =>
        !value ? 'Required' : null,
    },
    onValuesChange: (values) => {
      if (initialValues?.ap_pass_is_default === true) {
        if (initialValues?.ap_pass === values.ap_pass) {
          setHasDefaultApPass(true)
        } else {
          setHasDefaultApPass(false)
        }
      }

      const modeChanging = Boolean(values.client_enabled) !== initClientEnabled
      const inClientMode = Boolean(values.client_enabled)
      const clientDirty =
        (values.client_ssid ?? '') !== (initialValues?.client_ssid ?? '') ||
        (values.country ?? '') !== (initialValues?.country ?? '') ||
        (values.hostname ?? '') !== (initialValues?.hostname ?? '') ||
        Boolean(values.client_pass)
      const apDirty =
        (values.ap_ssid ?? '') !== (initialValues?.ap_ssid ?? '') ||
        Boolean(values.ap_pass)

      setRequiresReboot(
        modeChanging ||
        (inClientMode && clientDirty) ||
        (!inClientMode && apDirty)
      )
    },
  });

  // Track client_enabled changes in uncontrolled mode so conditional UI is reactive
  form.watch('client_enabled', ({ value }) => setClientEnabled(Boolean(value)))

  const enableWifi = clientEnabled

  return (
    <Fieldset legend="Network Settings">
      <form onSubmit={form.onSubmit(onSubmit)}>
        <Stack>

          <Fieldset legend="WiFi">
            <Stack>

              <Switch
                label="Enable WiFi Connection"
                description="Toggle to enable or disable automatic connection to a WiFi network on startup. "
                checked={enableWifi}
                disabled={isLoading}
                {...form.getInputProps('client_enabled', { type: 'checkbox' })}
              />

              {enableWifi && <>

                <TextInput
                  label="WiFi Network Name (SSID)"
                  description="Enter the name of the WiFi network you want the device to connect to."
                  placeholder="MyHomeNetwork"
                  disabled={isLoading}
                  withAsterisk
                  {...form.getInputProps('client_ssid')}
                />

                <PasswordInput
                  label="WiFi Password"
                  description="Enter the password for the selected WiFi network."
                  placeholder="supersecret123"
                  disabled={isLoading}
                  withAsterisk
                  {...form.getInputProps('client_pass')}
                />

                <TextInput
                  label="Country Code"
                  description="Two-letter ISO 3166-1 country code (e.g. US, GB, DE, CZ). Sets the WiFi regulatory domain."
                  placeholder="US"
                  maxLength={2}
                  disabled={isLoading}
                  {...form.getInputProps('country')}
                />

                <TextInput
                  label="Hostname"
                  description="mDNS hostname — device reachable at http://<hostname>.local on your network."
                  placeholder="pico-epaper-admin"
                  disabled={isLoading}
                  {...form.getInputProps('hostname')}
                />

              </>}
            </Stack>
          </Fieldset>

          <Fieldset legend="Access Point">
            <Stack>

              <Text size="sm" c="dimmed">The device can create its own WiFi network (access point), allowing you to connect directly without relying on an existing network.<br />
                The access point will be created and activated on startup if WiFi is disabled or the device cannot connect to the configured WiFi network.
              </Text>
              <Divider />

              <TextInput
                label="Access Point Name (SSID)"
                description="Name of the WiFi network the device will broadcast if no external WiFi is connected."
                placeholder="pico-admin-ap"
                disabled={isLoading}
                withAsterisk
                {...form.getInputProps('ap_ssid')}
              />

              <PasswordInput
                label="Access Point Password"
                description="Password required to connect to the device's access point. Leave empty to keep existing password."
                placeholder="supersecret123"
                disabled={isLoading}
                minLength={8}
                {...form.getInputProps('ap_pass')}
              />

            </Stack>
          </Fieldset>

          {hasDefaultApPass &&
            <Alert color="orange" title="Default AP password">
              <Group>You are using the default access point password.
                Please change it before submitting the form.</Group>
              <Group>After saving, this password will no longer be visible.
                Make sure you have noted it down.</Group>
            </Alert>}

          {requiresReboot &&
            <Alert color="orange" title="Reboot required">
              These changes will take effect after the device reboots automatically.
              {enableWifi
                ? ' After the reboot, make sure you are connected to the same WiFi network as the device, then reopen this page.'
                : ' After the reboot, the device will broadcast its access point — reconnect to it and reopen this page.'}
            </Alert>}

          <Divider />

          <Group justify="end">
            <Button type="submit" loading={isLoading} disabled={hasDefaultApPass}>Save</Button>
          </Group>

        </Stack>
      </form>
    </Fieldset>
  );
}
