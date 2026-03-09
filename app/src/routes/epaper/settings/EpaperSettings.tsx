import { useEffect, useState } from 'react';
import { useApiData } from '@/hooks/useApiData';
import { apiRequest } from '@/lib/apiRequest';
import FormSkeleton from '@/components/FormSkeleton';
import EpaperSettingsForm from './EpaperSettingsForm';
import type { EpaperPreset, EpaperActiveConfig, EpaperConfigFormValues } from '@/types/epaper';
import { Button, Fieldset, Group, Stack } from '@mantine/core';

type PresetPostResponse = { ok: boolean; data?: EpaperPreset };
type ConfigPostResponse = { ok: boolean; data?: EpaperActiveConfig };

export default function EpaperSettings() {
  const { data: presetsData, setData: setPresetsData } = useApiData<EpaperPreset[]>('/api/epaper/presets');
  const { data: configData } = useApiData<EpaperActiveConfig>('/api/epaper/config');

  // undefined = not yet initialised from server, null = new-preset mode, string = editing preset
  const [selectedPresetName, setSelectedPresetName] = useState<string | null | undefined>(undefined);
  const [formLoading, setFormLoading] = useState(false);
  const [refreshLoading, setRefreshLoading] = useState(false);
  const [clearLoading, setClearLoading] = useState(false);

  // Initialise selection from the active config once on first load
  useEffect(() => {
    if (configData && selectedPresetName === undefined) {
      setSelectedPresetName(configData.layout_preset);
    }
  }, [configData, selectedPresetName]);

  const selectedPreset =
    selectedPresetName != null
      ? (presetsData?.find(p => p.name === selectedPresetName) ?? null)
      : null;

  async function handleRefresh() {
    try {
      setRefreshLoading(true);
      await apiRequest({ url: '/api/epaper/refresh', method: 'POST' });
    } finally {
      setRefreshLoading(false);
    }
  }

  async function handleClear() {
    try {
      setClearLoading(true);
      await apiRequest({ url: '/api/epaper/clear', method: 'POST' });
    } finally {
      setClearLoading(false);
    }
  }

  const handleSubmit = async (values: EpaperConfigFormValues) => {
    try {
      setFormLoading(true);

      // 1. Save/create the layout preset (template + context only)
      const presetPayload: Record<string, unknown> = {
        ...(values.preset_name ? { name: values.preset_name } : {}),
        title: values.preset_title,
        template: values.template,
        context: values.context,
      };

      const presetRes = await apiRequest<PresetPostResponse>({
        url: '/api/epaper/presets',
        method: 'POST',
        body: presetPayload,
        returnJson: true,
        showNotifications: false,
      });
      if (!presetRes?.ok || !presetRes.data) return;
      const savedPreset = presetRes.data;

      // Update local presets list
      setPresetsData(prev => {
        if (!prev) return [savedPreset];
        const idx = prev.findIndex(p => p.name === savedPreset.name);
        if (idx >= 0) {
          const next = [...prev];
          next[idx] = savedPreset;
          return next;
        }
        return [...prev, savedPreset];
      });

      // 2. Save device config + activate the preset
      await apiRequest<ConfigPostResponse>({
        url: '/api/epaper/config',
        method: 'POST',
        body: {
          layout_preset: savedPreset.name,
          rotation: Number(values.rotation),
          refresh_interval: Number(values.refresh_interval),
          padding_top: values.padding_top,
          padding_right: values.padding_right,
          padding_bottom: values.padding_bottom,
          padding_left: values.padding_left,
        },
        returnJson: true,
      });

      setSelectedPresetName(savedPreset.name);
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (name: string) => {
    try {
      setFormLoading(true);
      const res = await apiRequest<{ ok: boolean }>({
        url: `/api/epaper/presets/${name}`,
        method: 'DELETE',
        returnJson: true,
      });
      if (!res?.ok) return;

      setPresetsData(prev => prev?.filter(p => p.name !== name) ?? []);

      // Fall back to the default preset
      setSelectedPresetName('default');
      await apiRequest<ConfigPostResponse>({
        url: '/api/epaper/config',
        method: 'POST',
        body: { layout_preset: 'default' },
        returnJson: true,
      });
    } finally {
      setFormLoading(false);
    }
  };

  if (!presetsData || selectedPresetName === undefined) return <FormSkeleton title="ePaper Settings" />;

  return (
    <Fieldset legend="ePaper Settings">
      <Stack>
        <Fieldset legend="Screen Controls">
          <Group>
            <Button onClick={handleRefresh} loading={refreshLoading}>Refresh</Button>
            <Button onClick={handleClear} loading={clearLoading} color="red" variant="light">Clear</Button>
          </Group>
        </Fieldset>
        <EpaperSettingsForm
          preset={selectedPreset}
          presets={presetsData}
          configData={configData}
          selectedPresetName={selectedPresetName}
          loading={formLoading}
          onPresetSelect={setSelectedPresetName}
          onSubmit={handleSubmit}
          onDelete={handleDelete}
        />
      </Stack>
    </Fieldset>
  );
}

