
export interface LogEntry {
  id: string;
  timestamp: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success' | 'system';
}

export interface TelemetryData {
  neuralLoad: number;
  memStack: number;
  systemStability: number;
}
