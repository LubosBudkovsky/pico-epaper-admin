import { useState } from 'react';
import { useApiData } from '@/hooks/useApiData';
import { apiRequest } from '@/lib/apiRequest';
import FormSkeleton from '@/components/FormSkeleton';
import ContextProvidersForm from './ContextProvidersForm';
import type { ContextProvider, ContextProvidersData } from '@/types/context';

type PostResponse = { ok: boolean; data?: ContextProvider };
type DeleteResponse = { ok: boolean };

export default function ContextProviders() {
  const { data: providersData, refetch: refetchProviders } =
    useApiData<ContextProvidersData>('/api/context/providers?exclude_system=true');

  const [editingProvider, setEditingProvider] = useState<ContextProvider | null>(null);
  const [formLoading, setFormLoading] = useState(false);

  async function handleSubmit(values: ContextProvider) {
    try {
      setFormLoading(true);
      const updated = await apiRequest<PostResponse>({
        url: '/api/context/providers',
        method: 'POST',
        body: values,
        returnJson: true,
      });
      if (updated?.ok && updated.data) {
        refetchProviders();
        setEditingProvider(JSON.parse(JSON.stringify(updated.data)));
      }
    } finally {
      setFormLoading(false);
    }
  }

  async function handleDelete(providerName: string) {
    try {
      setFormLoading(true);
      await apiRequest<DeleteResponse>({
        url: `/api/context/providers/${providerName}`,
        method: 'DELETE',
        returnJson: true,
      });
      refetchProviders();
      setEditingProvider(null);
    } finally {
      setFormLoading(false);
    }
  }

  function handleSelectedProviderChange(provider: ContextProvider | null) {
    setEditingProvider(provider ? JSON.parse(JSON.stringify(provider)) : null);
  }

  if (!providersData) return <FormSkeleton title="Context Providers" />;

  return (
    <ContextProvidersForm
      providersData={providersData}
      loading={formLoading}
      selectedProvider={editingProvider}
      onSelectedProviderChange={handleSelectedProviderChange}
      onSubmit={handleSubmit}
      onDelete={handleDelete}
    />
  );
}
