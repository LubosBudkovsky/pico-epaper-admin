import { Divider, Fieldset, Grid, NumberInput, Select, Stack, Switch } from "@mantine/core";
import type { UseFormReturnType } from "@mantine/form";
import type { EpaperConfigFormValues } from "@/types/epaper";
import { useState } from "react";

interface Props {
  form: UseFormReturnType<EpaperConfigFormValues>;
}

export default function DeviceConfiguration({ form }: Props) {

  const [invertColors, setInvertColors] = useState(form.getInitialValues().invert_colors ?? false)

  // Track invert_colors changes in uncontrolled mode so conditional UI is reactive
  form.watch('invert_colors', ({ value }) => setInvertColors(Boolean(value)))

  return (
    <Fieldset legend="Device Configuration">
      <Stack>

        <Select
          label="Refresh Interval"
          description="Time between automatic ePaper updates."
          placeholder="Select refresh interval"
          data={[
            { value: '0', label: 'Do not refresh' },
            { value: '60', label: '1 minute' },
            { value: '300', label: '5 minutes' },
            { value: '600', label: '10 minutes' },
            { value: '900', label: '15 minutes' },
            { value: '1800', label: '30 minutes' },
            { value: '2700', label: '45 minutes' },
            { value: '3600', label: '1 hour' },
            { value: '7200', label: '2 hours' },
            { value: '14400', label: '4 hours' },
            { value: '28800', label: '8 hours' },
            { value: '43200', label: '12 hours' },
            { value: '86400', label: '24 hours' },
          ]}
          allowDeselect={false}
          {...form.getInputProps('refresh_interval')}
        />

        <Select
          label="Rotation"
          description="Rotation value applied before rendering."
          placeholder="Select rotation"
          data={[
            { value: '0', label: 'Rotate 0°' },
            { value: '90', label: 'Rotate 90°' },
            { value: '180', label: 'Rotate 180°' },
            { value: '270', label: 'Rotate 270°' },
          ]}
          allowDeselect={false}
          {...form.getInputProps('rotation')}
        />

        <Grid>
          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <NumberInput
              label="Top Padding"
              description="Space between top edge and content in pixels."
              placeholder="e.g. 10"
              min={0}
              w="100%"
              styles={{ description: { minHeight: 36 } }}
              {...form.getInputProps('padding_top')}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <NumberInput
              label="Right Padding"
              description="Space between right edge and content in pixels."
              placeholder="e.g. 10"
              min={0}
              w="100%"
              styles={{ description: { minHeight: 36 } }}
              {...form.getInputProps('padding_right')}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <NumberInput
              label="Bottom Padding"
              description="Space between bottom edge and content in pixels."
              placeholder="e.g. 10"
              min={0}
              w="100%"
              styles={{ description: { minHeight: 36 } }}
              {...form.getInputProps('padding_bottom')}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, sm: 6, md: 3 }}>
            <NumberInput
              label="Left Padding"
              description="Space between left edge and content in pixels."
              placeholder="e.g. 10"
              min={0}
              w="100%"
              styles={{ description: { minHeight: 36 } }}
              {...form.getInputProps('padding_left')}
            />
          </Grid.Col>
        </Grid>

        <Divider />

        <Switch
          label="Invert Colors"
          description="Display dark background with light content."
          checked={invertColors}
          {...form.getInputProps('invert_colors', { type: 'checkbox' })}
        />
        
      </Stack>
    </Fieldset>
  );
}
