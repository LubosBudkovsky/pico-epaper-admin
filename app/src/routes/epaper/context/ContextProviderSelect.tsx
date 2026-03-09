import { Select } from "@mantine/core";
import { useEffect, useState } from "react";
import type { ContextProvider, ContextProvidersData } from "@/types/context";

interface Props {
  providersData: ContextProvidersData;
  selectedProvider: ContextProvider | null;
  disabled: boolean;
  onChange: (value: ContextProvider | null) => void;
}

export default function ContextProviderSelect({ providersData, selectedProvider, disabled, onChange }: Props) {
  const [selectData, setSelectData] = useState<{ value: string; label: string }[]>([]);
  const [selectProviderName, setSelectProviderName] = useState<string | null>(null);

  function handleChange(newName: string | null) {
    const found = providersData.find(p => p.name === newName) || null;
    onChange(found);
  }

  useEffect(() => {
    if (Array.isArray(providersData)) {
      setSelectData(providersData.map(p => ({ value: p.name, label: p.title })));
    }
  }, [providersData]);

  useEffect(() => {
    if (selectedProvider && providersData.some(p => p.name === selectedProvider.name)) {
      setSelectProviderName(selectedProvider.name);
    } else {
      setSelectProviderName(null);
    }
  }, [selectedProvider, providersData]);

  return (
    <Select
      label="Data Provider"
      description="Select a configured provider to edit."
      placeholder="Choose provider"
      data={selectData}
      value={selectProviderName}
      onChange={handleChange}
      disabled={disabled}
      searchable
      allowDeselect={false}
      nothingFoundMessage="No providers found"
      style={{ flex: 1 }}
    />
  );
}
