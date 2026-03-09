import { Fieldset, Select, Stack, TextInput } from "@mantine/core";
import { useApiData } from "@/hooks/useApiData";
import { useEffect, useState } from "react";
import type { UseFormReturnType } from "@mantine/form";
import type { EpaperConfigFormValues, EpaperTemplate } from "@/types/epaper";
import ContextProvider from "./ContextProvider";

type EpaperTemplatesData = EpaperTemplate[];

interface Props {
  form: UseFormReturnType<EpaperConfigFormValues>;
  presetKey: string;
}

export default function PresetConfiguration({ form, presetKey }: Props) {
  const { data, loading } = useApiData<EpaperTemplatesData>('/api/epaper/templates');
  const [templateSelectData, setTemplateSelectData] = useState<{ value: string; label: string }[]>([]);  
  const [selectedTemplate, setSelectedTemplate] = useState<EpaperTemplate | undefined>();

  // Sync selectedTemplate whenever the template field or the loaded data changes
  useEffect(() => {
    if (!Array.isArray(data)) return;

    setTemplateSelectData(data.map(t => ({ value: t.name, label: t.title })));

    const currentTemplateName = form.getValues().template;
    if (currentTemplateName) {
      const found = data.find(t => t.name === currentTemplateName);
      if (found) setSelectedTemplate(found);

      // Remove any context vars that no longer exist in the selected template.
      const newContext = form.getValues().context;
      if (newContext && found) {
        const validVarNames = new Set(found.layout.variables?.map(v => v.name) ?? []);
        Object.keys(newContext).forEach(key => {
          if (!validVarNames.has(key)) delete newContext[key];
        });
        form.setFieldValue('context', newContext);
      }
    } else {
      setSelectedTemplate(undefined);
    }
  }, [data, presetKey]);

  // Watch template field changes (uncontrolled mode — form doesn't re-render)
  form.watch('template', ({ value }) => {
    setSelectedTemplate(data?.find(t => t.name === value));
  });

  return (
    <Fieldset legend="Preset Configuration">
      <Stack>
        
        <TextInput
          key={`${presetKey}-title`}
          label="Preset Title"
          description="A human-readable name for this preset."
          placeholder="e.g. Weather Dashboard"
          withAsterisk
          {...form.getInputProps('preset_title')}
        />

        {/* Hidden field — carries the preset name for updates; empty for new presets */}
        <input type="hidden" {...form.getInputProps('preset_name')} />

        <Select
          key={`${presetKey}-template`}
          label="Select Template"
          description="Pick a template to set the screen's layout and available content."
          placeholder="Template for ePaper"
          data={templateSelectData}
          withAsterisk
          searchable
          nothingFoundMessage="No templates found"
          disabled={loading}
          allowDeselect={false}
          {...form.getInputProps('template')}
        />

        {selectedTemplate?.layout?.variables && selectedTemplate.layout.variables.length > 0 && (
          <ContextProvider form={form} template={selectedTemplate} />
        )}
      </Stack>
    </Fieldset>
  );
}
