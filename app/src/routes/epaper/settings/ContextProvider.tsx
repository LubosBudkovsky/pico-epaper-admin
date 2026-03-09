import { Fieldset, Select, Stack, Text, TextInput } from "@mantine/core";
import { useApiData } from "@/hooks/useApiData";
import { useEffect, useState } from "react";
import type { UseFormReturnType } from "@mantine/form";
import type { EpaperConfigFormValues } from "@/types/epaper";
import type { EpaperTemplate } from "@/types/epaper";
import type { ContextProvidersData, ContextProvider } from "@/types/context";

interface Props {
  template: EpaperTemplate;
  form: UseFormReturnType<EpaperConfigFormValues>;
}

// Renders a Select per template variable so the user can bind each one to a
// provider field (or enter inline custom text).
export default function ContextProviderConfig({ form, template }: Props) {
  const { data, loading } = useApiData<ContextProvidersData>('/api/context/providers');

  const [providerSelectData, setProviderSelectData] = useState<{ value: string; label: string }[]>([]);
  // Per-variable flag: true when the custom_text provider is selected.
  const [isCustomText, setIsCustomText] = useState<Record<string, boolean>>({});

  function handleProviderChange(contextVar: string, value: string | null) {
    if (!value) return;
    const parts = value.split('.');
    form.setFieldValue(`context.${contextVar}`, {
      provider: parts[0],
      field: parts.length > 1 ? parts[1] : '',
    });
    setIsCustomText(prev => ({ ...prev, [contextVar]: value === 'custom_text' }));
  }

  function getSelectValue(contextVar: string): string | null {
    const ctx = form.getValues()?.context;
    if (!ctx || !(contextVar in ctx)) return null;
    const entry = ctx[contextVar];
    if (entry?.provider === 'custom_text') return 'custom_text';
    return `${entry.provider}.${entry.field}`;
  }

  function getCustomTextValue(contextVar: string): string {
    const ctx = form.getValues()?.context;
    if (!ctx || !(contextVar in ctx)) return '';
    const entry = ctx[contextVar];
    return entry?.provider === 'custom_text' ? entry.field : '';
  }

  // Initialise `isCustomText` from form state when the template changes.
  useEffect(() => {
    const ctx = form.getValues()?.context;
    if (!ctx) return;
    const next: Record<string, boolean> = {};
    Object.entries(ctx).forEach(([key, val]) => {
      next[key] = val?.provider === 'custom_text';
    });
    setIsCustomText(next);
  }, [template]);

  // Build provider select options once data is available.
  useEffect(() => {
    if (!Array.isArray(data)) return;
    const opts = data.reduce((acc: { value: string; label: string }[], provider: ContextProvider) => {
      provider.fields.forEach(field => {
        acc.push({
          value: `${provider.name}.${field.name}`,
          label: `${provider.title ?? provider.name} → ${field.title ?? field.name}`,
        });
      });
      return acc;
    }, []);
    setProviderSelectData(opts);
  }, [data]);

  return (
    <Fieldset legend="Configure Context">
      <Stack>
        <Text size="sm" c="dimmed">
          Assign content to each section of your template by selecting variables from
          available providers. These mappings determine what appears on your screen.
        </Text>

        {template.layout.variables?.map(variable => (
          <Stack key={variable.name}>
            <Select
              label={variable.title}
              placeholder="Select context provider"
              data={[...providerSelectData, { value: 'custom_text', label: 'Custom Text' }]}
              value={getSelectValue(variable.name)}
              searchable
              disabled={loading}
              onChange={val => handleProviderChange(variable.name, val)}
            />
            {isCustomText[variable.name] && (
              <TextInput
                placeholder="Enter custom text"
                defaultValue={getCustomTextValue(variable.name)}
                onBlur={e =>
                  form.setFieldValue(`context.${variable.name}`, {
                    provider: 'custom_text',
                    field: e.currentTarget.value,
                  })
                }
              />
            )}
          </Stack>
        ))}
      </Stack>
    </Fieldset>
  );
}
