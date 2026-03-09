import { Group, SimpleGrid, Text } from "@mantine/core";
import { Fragment } from "react";

type DataValue = string | number | boolean
type DefinitionItem = { label: string, value?: DataValue }
type Props = {
  data: Record<string, DefinitionItem>
}

export default function DefinitionList({ data }: Props) {
  return (
    <Group>
      <SimpleGrid cols={2} spacing="lg" verticalSpacing={0}>
        {data && Object.entries(data).map(([key, row]) => {
          return (
            <Fragment key={key}>
              <Text fw={500}>{row.label}</Text>
              {typeof row.value == 'boolean' && <Text c="dimmed">{row.value === true ? 'true' : 'false'}</Text>}
              {typeof row.value !== 'boolean' && <Text c="dimmed">{String(row.value || '-')}</Text>}
            </Fragment>
          )
        })}
      </SimpleGrid>
    </Group>
  )
}