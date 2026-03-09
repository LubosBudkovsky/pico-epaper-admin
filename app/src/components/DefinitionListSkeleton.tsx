import { Group, SimpleGrid, Skeleton } from "@mantine/core";

export default function DefinitionListSkeleton() {
  return (
    <Group>
      <SimpleGrid cols={2} spacing="lg" verticalSpacing="sm">
        <Skeleton height={18} width="110px" radius="sm" />
        <Skeleton height={18} width="50px" radius="sm" />
        <Skeleton height={18} width="150px" radius="sm" />
        <Skeleton height={18} width="60px" radius="sm" />
        <Skeleton height={18} width="140px" radius="sm" />
        <Skeleton height={18} width="60px" radius="sm" />
        <Skeleton height={18} width="90px" radius="sm" />
        <Skeleton height={18} width="50px" radius="sm" />
        <Skeleton height={18} width="120px" radius="sm" />
        <Skeleton height={18} width="60px" radius="sm" />
      </SimpleGrid>
    </Group>
  )
}