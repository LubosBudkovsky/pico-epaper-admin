import { Button, Divider, Fieldset, Group, Stack, Select } from "@mantine/core";
import { useRef } from "react";
import { useForm, type UseFormReturnType } from "@mantine/form";
import type { EpaperPreset, EpaperActiveConfig, EpaperConfigFormValues } from "@/types/epaper";
import DeviceConfiguration from "./DeviceConfiguration";
import PresetConfiguration from "./PresetConfiguration";

interface Props {
  /** The layout preset currently loaded into the form. null = new-preset mode (blank form). */
  preset: EpaperPreset | null;
  /** All available presets, used to populate the preset selector. */
  presets: EpaperPreset[];
  /** Global device config (rotation, padding, refresh_interval). */
  configData: EpaperActiveConfig | null;
  /** Name of the preset selected in the dropdown. null = new-preset mode. */
  selectedPresetName: string | null;
  loading: boolean;
  onPresetSelect: (name: string | null) => void;
  onSubmit: (values: EpaperConfigFormValues) => void;
  onDelete: (name: string) => void;
}

export default function EpaperSettingsForm({
  preset,
  presets,
  configData,
  selectedPresetName,
  loading,
  onPresetSelect,
  onSubmit,
  onDelete,
}: Props) {
  const form: UseFormReturnType<EpaperConfigFormValues> = useForm<EpaperConfigFormValues>({
    mode: 'uncontrolled',
    initialValues: {
      // Device config — from global epaper.json, not the preset
      rotation: (configData?.rotation ?? 0).toString(),
      refresh_interval: (configData?.refresh_interval ?? 0).toString(),
      padding_top: configData?.padding_top ?? 50,
      padding_right: configData?.padding_right ?? 50,
      padding_bottom: configData?.padding_bottom ?? 50,
      padding_left: configData?.padding_left ?? 50,
      // Layout preset
      preset_name: preset?.name ?? '',
      preset_title: preset?.title ?? '',
      template: preset?.template ?? '',
      context: preset?.context ?? {},
    },
    validate: {      
      preset_title: (value) =>
        !value ? 'Required' : null,
      template: (value) =>
        !value ? 'Required' : null,
    },
  });

  // When the selected preset changes, update ONLY the preset fields synchronously
  // during render so that LayoutConfiguration remounts with the correct defaultValues.
  // Device config fields (rotation, padding, refresh_interval) are intentionally left untouched.
  const prevPresetNameRef = useRef(selectedPresetName);
  if (prevPresetNameRef.current !== selectedPresetName) {
    prevPresetNameRef.current = selectedPresetName;
    form.setValues({
      preset_name: preset?.name ?? '',
      preset_title: preset?.title ?? '',
      template: preset?.template ?? '',
      context: preset?.context ?? {},
    });
  }

  const isNewPreset = selectedPresetName === null;
  const isDeletable = !isNewPreset && selectedPresetName !== 'default';

  const presetSelectData = presets.map(p => ({ value: p.name, label: p.title }));

  return (
    <form onSubmit={form.onSubmit(onSubmit)}>
      <Stack>

        <DeviceConfiguration form={form} />

        <Fieldset legend="Layout Preset">
          <Stack>
            <Group align="end">
              <Select
                label="Select Preset"
                description="Choose a preset to load its layout and context bindings."
                style={{ flex: 1 }}
                data={presetSelectData}
                value={selectedPresetName}
                onChange={v => onPresetSelect(v)}
                allowDeselect={false}
                placeholder={isNewPreset ? 'New preset…' : undefined}
              />
              <Button
                variant="light"
                onClick={() => onPresetSelect(null)}
                disabled={isNewPreset || loading}
              >
                Add New Preset
              </Button>
              {isDeletable && (
                <Button
                  color="red"
                  variant="light"
                  loading={loading}
                  onClick={() => onDelete(selectedPresetName!)}
                >
                  Delete Preset
                </Button>
              )}
            </Group>

            <PresetConfiguration presetKey={selectedPresetName ?? '__new__'} form={form} />
          </Stack>
        </Fieldset>

        <Divider />

        <Group justify="end">
          <Button type="submit" loading={loading}>
            {isNewPreset ? 'Create Preset' : 'Save'}
          </Button>
        </Group>
      </Stack>
    </form>
  );
}
