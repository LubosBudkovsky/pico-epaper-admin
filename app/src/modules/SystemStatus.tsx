import { useApiData } from '@/hooks/useApiData'
import DefinitionList from '@/components/DefinitionList'
import { Divider, Fieldset, Group, Progress, Stack, Text } from '@mantine/core'
import DefinitionListSkeleton from '@/components/DefinitionListSkeleton'

type StatusData = Record<string, string | number>

const LABELS: Record<string, string> = {
  network_ip:          'IP Address',
  network_ssid:        'SSID',
  network_rssi:        'Signal (RSSI)',
  network_mac:         'MAC Address', 
  system_micropython:  'MicroPython',
  uptime:              'Uptime',
}

export default function SystemStatus() {
  const { data, loading } = useApiData<StatusData>('/api/system/status')

  const listData = Object.fromEntries(
    Object.entries(LABELS)
      .filter(([key]) => data && key in data)
      .map(([key, label]) => [key, { label, value: data![key] }])
  )

  const memUsed    = Number(data?.memory_used  ?? 0)
  const memTotal   = Number(data?.memory_total ?? 1)
  const memUnit    = data?.memory_unit ?? 'KB'
  const memPct     = Number(data?.memory_free_pct ?? 0)

  const storUsed  = Number(data?.storage_used  ?? 0)
  const storTotal = Number(data?.storage_total ?? 1)
  const storUnit  = data?.storage_unit ?? 'KB'
  const storPct   = Number(data?.storage_free_pct ?? 0)

  return (
    <Fieldset legend="System Status">
      <Stack>

        <Stack gap={4}>
          <Group justify="space-between">
            <Text size="sm">Storage</Text>
            {!loading && <Text size="sm" c="dimmed">{storUsed} / {storTotal} {storUnit}</Text>}
          </Group>
          <Progress value={loading ? 0 : 100 - storPct} />
        </Stack>

        <Stack gap={4}>
          <Group justify="space-between">
            <Text size="sm">Memory</Text>
            {!loading && <Text size="sm" c="dimmed">{memUsed} / {memTotal} {memUnit}</Text>}
          </Group>
          <Progress value={loading ? 0 : 100 - memPct} />
        </Stack>        

        <Divider my="xs" />

        {loading ? <DefinitionListSkeleton /> : <DefinitionList data={listData} /> }

      </Stack>
    </Fieldset>
  )
}