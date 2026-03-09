// ── Context provider field ─────────────────────────────────────────────────────

export interface ContextProviderField {
  name: string;
  title: string;
  path: string;
  transformer?: string;
}

// ── Context provider (external JSON endpoint) ─────────────────────────────────

export interface ContextProvider {
  name: string;
  title: string;
  endpoint: string;
  fields: ContextProviderField[];
}

export type ContextProvidersData = ContextProvider[];

// ── Transformer ───────────────────────────────────────────────────────────────

export interface ContextTransformer {
  name: string;
  title: string;
}

export type ContextTransformersData = ContextTransformer[];
