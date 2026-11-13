export interface SystemServiceStatus {
  status: string;
  configured: boolean;
  message?: string;
  database?: string;
}

export interface HealthState {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  services: {
    mongodb: SystemServiceStatus;
    redis: SystemServiceStatus;
    [key: string]: SystemServiceStatus;
  };
}

export interface PlatformConnection {
  id: string;
  name: string;
  provider: string;
  category: "Official API" | "Licensed Feed" | "Authorized WebSocket" | "WebSocket" | "CSV Import" | "JSON Import";
  status: "CONNECTED" | "DISCONNECTED" | "AUTHORIZATION REQUIRED" | "ERROR" | "NOT CONFIGURED";
  lastSync: string | null;
  dataAvailable: boolean;
  latencyMs?: number;
  errorMessage?: string;
  endpoint?: string;
}

export interface HistoricalRound {
  roundId: string;
  platform: string;
  provider: string;
  room: string;
  multiplier: number;
  timestamp: string;
  status: "VERIFIED" | "UNVERIFIED" | "DISPUTED";
  source: string;
  hash?: string;
}

export interface ModelMetadata {
  id: string;
  name: string;
  type: "Logistic Regression" | "Random Forest" | "XGBoost" | "Gradient Boosting" | "Statistical Baseline";
  version: string;
  status: "ACTIVE" | "TRAINING" | "EVALUATED" | "STANDBY" | "ARCHIVED";
  trainingDataset: string;
  trainingDate: string;
  validationStatus: "PASS" | "FAIL" | "PENDING";
  brierScore: number | null;
  logLoss: number | null;
  calibration: string | null;
  walkForwardResult: string | null;
  hasEdge: boolean;
}

export interface PredictionRecord {
  id: string;
  modelVersion: string;
  platform: string;
  dataset: string;
  estimatedProbability: number | null;
  confidenceInterval: [number, number] | null;
  calibrationStatus: "CALIBRATED" | "UNCALIBRATED" | "DRIFTING";
  timestamp: string;
  actualOutcome: number | null;
  evaluationResult: "CORRECT" | "INCORRECT" | "PENDING";
}

export interface PaperTradeRecord {
  id: string;
  timestamp: string;
  stake: number;
  targetMultiplier: number;
  actualCrash: number | null;
  pnl: number;
  status: "WON" | "LOST" | "PENDING" | "CANCELLED";
  strategy: string;
}

export interface NotificationItem {
  id: string;
  type: "INFO" | "WARNING" | "CRITICAL" | "SUCCESS";
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}
