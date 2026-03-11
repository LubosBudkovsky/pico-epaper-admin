// ── Context binding stored per template variable ─────────────────────────────

export interface EpaperContextEntry {
  provider: string;
  field: string;
}

// ── Active config: device-level settings + pointer to active layout preset ───

export interface EpaperActiveConfig {
  layout_preset: string;
  rotation: number;
  refresh_interval: number;
  invert_colors: boolean;
  padding_top: number;
  padding_right: number;
  padding_bottom: number;
  padding_left: number;
}

// ── A single layout preset (template + context bindings only) ────────────────

export interface EpaperPreset {
  name: string;
  title: string;
  template: string;
  context: Record<string, EpaperContextEntry>;
}

// ── Form values ───────────────────────────────────────────────────────────────
// Device config fields live at the top level; preset fields are grouped below.
// rotation / refresh_interval are strings because Mantine Select works with strings.

export interface EpaperConfigFormValues {
  // Device config (global)
  rotation: string;
  refresh_interval: string;
  invert_colors: boolean;
  padding_top: number;
  padding_right: number;
  padding_bottom: number;
  padding_left: number;
  // Layout preset
  preset_name: string;   // empty = new preset (name generated from title)
  preset_title: string;
  template: string;
  context: Record<string, EpaperContextEntry>;
}

// ── Templates ─────────────────────────────────────────────────────────────────

export interface TemplateVariable {
  name: string;
  title: string;
}

export interface TemplateLayout {
  elements: Record<string, unknown>[];
  variables?: TemplateVariable[];
}

export interface EpaperTemplate {
  name: string;
  title: string;
  layout: TemplateLayout;
}
