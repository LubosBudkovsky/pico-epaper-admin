import { Divider, Fieldset, Group, Skeleton, Stack } from "@mantine/core";

type FormSkeletonProps = {
  title?: string;
};

export default function FormSkeleton({ title }: FormSkeletonProps) {
  return (

    <Stack>
      <Fieldset legend={title || 'Settings'}>
        <Stack gap="lg">

          <Stack gap="xs">
            <Skeleton height={18} width="15%" radius="sm" />
            <Skeleton height={18} width="30%" radius="sm" />
            <Skeleton height={36} radius="sm" />
          </Stack>

          <Stack gap="xs">
            <Skeleton height={18} width="15%" radius="sm" />
            <Skeleton height={18} width="30%" radius="sm" />
            <Skeleton height={36} radius="sm" />
          </Stack>

          <Stack gap="xs">
            <Skeleton height={18} width="15%" radius="sm" />
            <Skeleton height={18} width="30%" radius="sm" />
            <Skeleton height={36} radius="sm" />
          </Stack>

          <Divider />

          <Group justify="end">
            <Skeleton height={36} width={100} radius="sm" />
          </Group>
        </Stack>
      </Fieldset>


    </Stack>
  )
}