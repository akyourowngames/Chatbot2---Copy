
export enum SettingsTab {
  PROFILE = 'PROFILE',
  SECURITY = 'SECURITY',
  DEVICES = 'DEVICES',
  TELEMETRY = 'TELEMETRY',
  UPLINK = 'UPLINK',
  NOTIFICATIONS = 'NOTIFICATIONS'
}

export interface OperatorProfile {
  name: string;
  email: string;
  id: string;
  rank: string;
  avatar: string;
  bio: string;
}

export interface SystemConfig {
  neuralLoadLimit: number;
  memoryStackAllocation: number;
  encryptionLevel: string;
  tlsEnabled: boolean;
  autoPurge: boolean;
}
