// ── Network / WiFi AP config ──────────────────────────────────────────────────

export interface NetworkSettingsData {
  client_enabled: boolean;
  client_ssid: string;
  country: string;
  hostname: string;
  ap_ssid: string;
  ap_pass?: string;
  ap_pass_is_default: boolean;
}

export interface NetworkSettingsResponse {
  ok: boolean;
  reboot?: boolean;
  data: NetworkSettingsData;
}
