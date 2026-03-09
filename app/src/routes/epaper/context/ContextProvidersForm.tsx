import {
  Button,
  Divider,
  Fieldset,
  Group,
  Loader,
  Paper,
  Select,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";
import { useForm, type UseFormReturnType } from "@mantine/form";
import { useEffect, useState } from "react";
import { useApiData } from "@/hooks/useApiData";
import type { ContextProvider, ContextProvidersData, ContextTransformersData } from "@/types/context";
import ContextProviderSelect from "./ContextProviderSelect";

const uid = () => Math.random().toString(36).slice(2, 10);

interface Props {
  providersData: ContextProvidersData;
  loading: boolean;
  selectedProvider: ContextProvider | null;
  onSelectedProviderChange: (value: ContextProvider | null) => void;
  onSubmit: (values: ContextProvider) => void;
  onDelete: (name: string) => void;
}

export default function ContextProvidersForm({
  providersData,
  loading,
  selectedProvider,
  onSelectedProviderChange,
  onSubmit,
  onDelete,
}: Props) {
  const { data: transformersData } = useApiData<ContextTransformersData>('/api/context/transformers');

  const [localFields, setLocalFields] = useState<ContextProvider['fields']>(
    selectedProvider?.fields ?? []
  );

  const form: UseFormReturnType<ContextProvider> = useForm<ContextProvider>({
    mode: 'uncontrolled',
    validate: (values) => {
      const errors: Record<string, string> = {};
      if (!values.title) errors.title = 'Required';
      if (!values.endpoint) errors.endpoint = 'Required';
      values.fields.forEach((f, i) => {
        if (!f.title) errors[`fields.${i}.title`] = 'Required';
        if (!f.path) errors[`fields.${i}.path`] = 'Required';
      });
      return errors;
    },
  });

  function handleAddNewProvider() {
    const newProvider: ContextProvider = {
      name: uid(),
      title: 'New Provider',
      endpoint: '',
      fields: [{ name: uid(), title: 'Field Name', path: '' }],
    };
    onSelectedProviderChange(newProvider);
  }

  function handleNewField() {
    const current = form.getValues();
    const newField = { name: uid(), title: 'New Field', path: '' };
    const updatedFields = [...(current.fields ?? []), newField];
    setLocalFields(updatedFields);
    form.setValues({ ...current, fields: updatedFields });
  }

  function handleRemoveField(fieldName: string) {
    const current = form.getValues();
    const updatedFields = (current.fields ?? []).filter(f => f.name !== fieldName);
    setLocalFields(updatedFields);
    form.setValues({ ...current, fields: updatedFields });
  }

  // Re-sync form only when a genuinely different provider is selected
  useEffect(() => {
    if (selectedProvider) {
      const fresh = { ...selectedProvider };
      setLocalFields(fresh.fields ?? []);
      form.setValues(fresh as ContextProvider);
    } else {
      setLocalFields([]);
      form.setValues({ name: '', title: '', endpoint: '', fields: [] });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedProvider?.name]);

  const isCreatingNew =
    selectedProvider !== null &&
    !providersData.some((p) => p.name === selectedProvider.name);

  return (
    <Fieldset legend="Context Providers">
      <form onSubmit={form.onSubmit(onSubmit)}>
        <Stack gap="lg">
          <Stack gap={4}>
            <Text size="sm" c="dimmed">
              A data provider connects to a single JSON endpoint. You can expose
              selected fields from the response and later bind them to template
              variables used in your ePaper layouts.
            </Text>
          </Stack>
        
          {providersData ? (
            <Group align="end">
              <ContextProviderSelect
                providersData={providersData}
                selectedProvider={selectedProvider}
                disabled={loading}
                onChange={onSelectedProviderChange}
              />
              <Button
                variant="light"
                onClick={handleAddNewProvider}
                disabled={isCreatingNew || loading}
              >
                Add New Provider
              </Button>
              {selectedProvider && !isCreatingNew && (
                <Button
                  color="red"
                  variant="light"
                  loading={loading}
                  onClick={() => onDelete(selectedProvider.name)}
                >
                  Delete Provider
                </Button>
              )}
            </Group>
          ) : (
            <Loader />
          )}          

          {selectedProvider && (
            <Fieldset legend="Provider Configuration" key={selectedProvider.name}>
              <Stack gap="md">
                {/* Hidden field — carries the provider name for updates; uid for new providers */}
                <input type="hidden" {...form.getInputProps('name')} />
                <TextInput
                  key={form.key('title')}
                  label="Provider Title"
                  description="Human-readable name used when selecting this provider in context bindings."
                  placeholder="e.g. Weather - Home"
                  disabled={loading}
                  withAsterisk
                  {...form.getInputProps('title')}
                />
                <TextInput
                  key={form.key('endpoint')}
                  label="Endpoint URL"
                  description="Full URL returning JSON."
                  placeholder="https://api.example.com/data.json"
                  disabled={loading}
                  withAsterisk
                  {...form.getInputProps('endpoint')}
                />

                <Fieldset legend="Exposed Fields">
                  <Stack gap="md">
                    <Text size="sm" c="dimmed">
                      Define which values from the JSON response should be available
                      for templates. Use dot-notation paths to reference nested data.
                    </Text>
                    {localFields.map((field, i) => (
                      <Paper withBorder p="md" key={field.name}>
                        <Stack gap="sm">
                          <TextInput
                            key={form.key(`fields.${i}.title`)}
                            label="Field Title"
                            description="Display name shown in template variable selection."
                            placeholder="e.g. Current Temperature"
                            disabled={loading}
                            withAsterisk
                            {...form.getInputProps(`fields.${i}.title`)}
                          />
                          <TextInput
                            key={form.key(`fields.${i}.path`)}
                            label="Field Path"
                            description="Path inside the JSON response."
                            placeholder="e.g. forecast.[0].temp"
                            disabled={loading}
                            withAsterisk
                            {...form.getInputProps(`fields.${i}.path`)}
                          />
                          <Select
                            key={form.key(`fields.${i}.transformer`)}
                            label="Field Transformer"
                            description="Optional transformation applied to the value before display."
                            placeholder="Select a transformation (optional)"
                            data={transformersData?.map(t => ({ value: t.name, label: t.title }))}
                            disabled={loading || !transformersData}
                            clearable
                            {...form.getInputProps(`fields.${i}.transformer`)}
                          />
                          {localFields.length > 1 && (
                            <Group>
                              <Button
                                color="red"
                                variant="light"
                                disabled={loading}
                                onClick={() => handleRemoveField(field.name)}
                              >
                                Remove Field
                              </Button>
                            </Group>
                          )}
                        </Stack>
                      </Paper>
                    ))}
                    <Group>
                      <Button variant="light" disabled={loading} onClick={handleNewField}>
                        Add New Field
                      </Button>
                    </Group>
                  </Stack>
                </Fieldset>

                <Divider />

                <Group justify="end">
                  <Button type="submit" loading={loading}>
                    {isCreatingNew ? 'Create Provider' : 'Save Provider'}
                  </Button>
                </Group>
              </Stack>
            </Fieldset>
          )}
        </Stack>
      </form>
    </Fieldset>
  );
}
