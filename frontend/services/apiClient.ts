import { config } from "@/config";
import {
  HealthState,
  PlatformConnection,
  HistoricalRound,
  ModelMetadata,
  PredictionRecord,
  NotificationItem,
} from "@/types";

export interface ImportJobResponse {
  job_id: string;
  source_id: string;
  source_type: string;
  total_records: number;
  processed_records: number;
  accepted_records: number;
  rejected_records: number;
  duplicate_records: number;
  status: string;
  errors: string[];
}

export interface RoundsResponse {
  total: number;
  limit: number;
  rounds: any[];
}

export interface RoundStatsResponse {
  sample_size: number;
  mean: number | null;
  median: number | null;
  min: number | null;
  max: number | null;
  variance: number | null;
  std_dev: number | null;
  message?: string;
}

class ApiService {
  private baseUrl = config.apiUrl;

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${endpoint}`, {
      cache: "no-store",
      ...options,
    });
    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${res.statusText}`);
    }
    return res.json();
  }

  // Health
  async getHealth(): Promise<HealthState> {
    return this.request<HealthState>("/health");
  }

  async getSystemInfo(): Promise<any> {
    return this.request<any>("/api/v1/system/info");
  }

  // Platforms
  async getPlatforms(): Promise<any[]> {
    return this.request<any[]>("/api/v1/platforms");
  }

  async testPlatformConnection(platformId: string): Promise<any> {
    return this.request<any>(`/api/v1/platforms/${platformId}/test-connection`, {
      method: "POST",
    });
  }

  // Historical Rounds
  async getHistoricalRounds(params?: {
    platform?: string;
    provider?: string;
    limit?: number;
    search?: string;
  }): Promise<RoundsResponse> {
    const q = new URLSearchParams();
    if (params?.platform && params.platform !== "all") q.append("platform", params.platform);
    if (params?.provider && params.provider !== "all") q.append("provider", params.provider);
    if (params?.limit) q.append("limit", params.limit.toString());
    if (params?.search) q.append("search", params.search);
    return this.request<RoundsResponse>(`/api/v1/rounds?${q.toString()}`);
  }

  async getRoundStatistics(platform?: string): Promise<RoundStatsResponse> {
    const q = platform && platform !== "all" ? `?platform=${platform}` : "";
    return this.request<RoundStatsResponse>(`/api/v1/rounds/statistics${q}`);
  }

  // Historical File Import
  async importCsv(formData: FormData): Promise<ImportJobResponse> {
    const res = await fetch(`${this.baseUrl}/api/v1/import/csv`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  async importJson(formData: FormData): Promise<ImportJobResponse> {
    const res = await fetch(`${this.baseUrl}/api/v1/import/json`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  // Import jobs
  async getImportJobs(): Promise<ImportJobResponse[]> {
    return this.request<ImportJobResponse[]>("/api/v1/import/jobs");
  }

  // Data Quality
  async getDataQualitySummary(): Promise<any> {
    return this.request<any>("/api/v1/data-quality/summary");
  }

  // Statistical Analytics
  async getAnalyticsSummary(datasetId: string): Promise<any> {
    return this.request<any>(`/api/v1/analytics/summary?dataset_id=${datasetId}`);
  }

  async getDescriptiveStats(datasetId: string): Promise<any> {
    return this.request<any>(`/api/v1/analytics/descriptive?dataset_id=${datasetId}`);
  }

  async getDistribution(datasetId: string): Promise<any> {
    return this.request<any>(`/api/v1/analytics/distribution?dataset_id=${datasetId}`);
  }

  async getRollingStats(datasetId: string, window: number = 50): Promise<any> {
    return this.request<any>(`/api/v1/analytics/rolling?dataset_id=${datasetId}&window=${window}`);
  }

  async getAutocorrelation(datasetId: string): Promise<any> {
    return this.request<any>(`/api/v1/analytics/autocorrelation?dataset_id=${datasetId}`);
  }

  async getOutliers(datasetId: string): Promise<any> {
    return this.request<any>(`/api/v1/analytics/outliers?dataset_id=${datasetId}`);
  }

  async getDrift(datasetId: string): Promise<any> {
    return this.request<any>(`/api/v1/analytics/drift?dataset_id=${datasetId}`);
  }

  // Datasets
  async getDatasets(): Promise<any[]> {
    return this.request<any[]>("/api/v1/datasets");
  }

  async getDatasetRounds(
    datasetId: string,
    params?: {
      page?: number;
      pageSize?: number;
      sort?: string;
      search?: string;
      minMultiplier?: number;
      maxMultiplier?: number;
    }
  ): Promise<any> {
    const q = new URLSearchParams();
    if (params?.page) q.append("page", params.page.toString());
    if (params?.pageSize) q.append("page_size", params.pageSize.toString());
    if (params?.sort) q.append("sort", params.sort);
    if (params?.search) q.append("search", params.search);
    if (params?.minMultiplier) q.append("min_multiplier", params.minMultiplier.toString());
    if (params?.maxMultiplier) q.append("max_multiplier", params.maxMultiplier.toString());
    return this.request<any>(`/api/v1/datasets/${datasetId}/rounds?${q.toString()}`);
  }

  async getDatasetValidationReport(datasetId: string): Promise<any> {
    return this.request<any>(`/api/v1/datasets/${datasetId}/validation-report`);
  }

  async getDatasetCoverage(datasetId: string): Promise<any> {
    return this.request<any>(`/api/v1/datasets/${datasetId}/coverage`);
  }

  // Phase 6 ML Research Laboratory
  async getMLModels(params?: { platformId?: string; gameProvider?: string; status?: string }): Promise<any[]> {
    const q = new URLSearchParams();
    if (params?.platformId) q.append("platform_id", params.platformId);
    if (params?.gameProvider) q.append("game_provider", params.gameProvider);
    if (params?.status) q.append("status", params.status);
    return this.request<any[]>(`/api/v1/ml/models?${q.toString()}`);
  }

  async getMLModel(modelId: string): Promise<any> {
    return this.request<any>(`/api/v1/ml/models/${modelId}`);
  }

  async getMLExperiments(): Promise<any[]> {
    return this.request<any[]>("/api/v1/ml/experiments");
  }

  async getMLExperiment(experimentId: string): Promise<any> {
    return this.request<any>(`/api/v1/ml/experiments/${experimentId}`);
  }

  async trainMLModel(payload: {
    experiment_name: string;
    algorithm: string;
    platform_id: string;
    game_provider: string;
    game_id: string;
    room_id: string;
    target_threshold: number;
    walk_forward_splits: number;
    feature_window_size: number;
    hyperparameters?: Record<string, any>;
  }): Promise<any> {
    return this.request<any>("/api/v1/ml/train", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  async compareMLModels(modelIds: string[]): Promise<any> {
    const q = new URLSearchParams();
    modelIds.forEach((id) => q.append("model_ids", id));
    return this.request<any>(`/api/v1/ml/compare?${q.toString()}`);
  }

  async runMLInference(modelId: string, recentMultipliers: number[]): Promise<any> {
    return this.request<any>("/api/v1/ml/inference", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model_id: modelId,
        recent_multipliers: recentMultipliers,
      }),
    });
  }

  async getPredictions(): Promise<PredictionRecord[]> {
    return [];
  }

  // Phase 7 Real-Time Telemetry & Prediction Tracking
  async getRealtimeStatus(): Promise<any> {
    return this.request<any>("/api/v1/realtime/status");
  }

  async getRealtimeConnections(): Promise<any[]> {
    return this.request<any[]>("/api/v1/realtime/connections");
  }

  async reconnectConnector(connectorId: string): Promise<any> {
    return this.request<any>(`/api/v1/realtime/connections/${connectorId}/reconnect`, {
      method: "POST",
    });
  }

  async getLiveRounds(params?: { platformId?: string; providerId?: string; limit?: number }): Promise<any[]> {
    const q = new URLSearchParams();
    if (params?.platformId) q.append("platform_id", params.platformId);
    if (params?.providerId) q.append("provider_id", params.providerId);
    if (params?.limit) q.append("limit", params.limit.toString());
    return this.request<any[]>(`/api/v1/realtime/rounds?${q.toString()}`);
  }

  async getResearchEstimates(status?: string): Promise<any[]> {
    const q = new URLSearchParams();
    if (status) q.append("status", status);
    return this.request<any[]>(`/api/v1/realtime/estimates?${q.toString()}`);
  }

  async runResearchEstimate(payload: {
    platform_id: string;
    provider_id: string;
    game_id: string;
    room_id: string;
    round_id?: string;
    model_id?: string;
    target_threshold: number;
    recent_multipliers: number[];
  }): Promise<any> {
    return this.request<any>("/api/v1/realtime/estimates/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  async getScoredOutcomes(limit: number = 50): Promise<any[]> {
    return this.request<any[]>(`/api/v1/realtime/outcomes?limit=${limit}`);
  }

  async getEvaluationsSummary(): Promise<any> {
    return this.request<any>("/api/v1/realtime/evaluations/summary");
  }

  async getRealtimeOperationalMetrics(): Promise<any> {
    return this.request<any>("/api/v1/realtime/metrics");
  }

  async getRealtimeHealth(): Promise<any> {
    return this.request<any>("/api/v1/realtime/health");
  }

  // Phase 8 Paper Trading & Risk Simulation
  async getSimulations(): Promise<any[]> {
    return this.request<any[]>("/api/v1/simulation");
  }

  async getSimulation(id: string): Promise<any> {
    return this.request<any>(`/api/v1/simulation/${id}`);
  }

  async createSimulation(payload: {
    name: string;
    mode: string;
    dataset_id: string;
    starting_virtual_bankroll: number;
    strategy_id?: string;
    strategy_config?: Record<string, any>;
  }): Promise<any> {
    return this.request<any>("/api/v1/simulation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  async startSimulation(id: string): Promise<any> {
    return this.request<any>(`/api/v1/simulation/${id}/start`, { method: "POST" });
  }

  async pauseSimulation(id: string): Promise<any> {
    return this.request<any>(`/api/v1/simulation/${id}/pause`, { method: "POST" });
  }

  async resumeSimulation(id: string): Promise<any> {
    return this.request<any>(`/api/v1/simulation/${id}/resume`, { method: "POST" });
  }

  async stopSimulation(id: string): Promise<any> {
    return this.request<any>(`/api/v1/simulation/${id}/stop`, { method: "POST" });
  }

  async getSimulationHistory(id: string): Promise<any[]> {
    return this.request<any[]>(`/api/v1/simulation/${id}/history`);
  }

  async getSimulationMetrics(id: string): Promise<any> {
    return this.request<any>(`/api/v1/simulation/${id}/metrics`);
  }

  async getStrategies(): Promise<any[]> {
    return this.request<any[]>("/api/v1/simulation/strategies");
  }

  async getRiskOverview(): Promise<any> {
    return this.request<any>("/api/v1/risk/overview");
  }

  async runMonteCarlo(payload: {
    job_name: string;
    num_trials: number;
    rounds_per_trial: number;
    starting_bankroll: number;
    stake_amount: number;
    target_multiplier: number;
    house_edge?: number;
    max_drawdown_limit?: number;
    random_seed?: number;
  }): Promise<any> {
    return this.request<any>("/api/v1/monte-carlo/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  async getMonteCarloJobs(): Promise<any[]> {
    return this.request<any[]>("/api/v1/monte-carlo/jobs");
  }

  async getNotifications(params?: { unreadOnly?: boolean; type?: string }): Promise<any[]> {
    const q = new URLSearchParams();
    if (params?.unreadOnly) q.append("unread_only", "true");
    if (params?.type) q.append("notification_type", params.type);
    return this.request<any[]>(`/api/v1/notifications?${q.toString()}`);
  }

  async getUnreadNotificationCount(): Promise<{ unread_count: number }> {
    return this.request<{ unread_count: number }>("/api/v1/notifications/unread-count");
  }

  async markNotificationRead(id: string): Promise<any> {
    return this.request<any>(`/api/v1/notifications/${id}/read`, { method: "PATCH" });
  }

  async markAllNotificationsRead(): Promise<any> {
    return this.request<any>("/api/v1/notifications/read-all", { method: "POST" });
  }

  async deleteNotification(id: string): Promise<any> {
    return this.request<any>(`/api/v1/notifications/${id}`, { method: "DELETE" });
  }

  // Phase 9 Alerts & Rules
  async getAlertRules(): Promise<any[]> {
    return this.request<any[]>("/api/v1/alerts/rules");
  }

  async createAlertRule(payload: {
    name: string;
    description: string;
    event_type: string;
    threshold?: number;
    severity?: string;
    cooldown_seconds?: number;
  }): Promise<any> {
    return this.request<any>("/api/v1/alerts/rules", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  async testAlertRule(ruleId: string): Promise<any> {
    return this.request<any>(`/api/v1/alerts/rules/${ruleId}/test`, { method: "POST" });
  }

  async deleteAlertRule(ruleId: string): Promise<any> {
    return this.request<any>(`/api/v1/alerts/rules/${ruleId}`, { method: "DELETE" });
  }

  // Phase 9 User Profile & Preferences
  async getMyProfile(): Promise<any> {
    return this.request<any>("/api/v1/users/me");
  }

  async updateMyProfile(payload: { display_name?: string; avatar_url?: string; preferences?: any }): Promise<any> {
    return this.request<any>("/api/v1/users/me", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  async getMyPreferences(): Promise<any> {
    return this.request<any>("/api/v1/users/me/preferences");
  }

  async updateMyPreferences(payload: any): Promise<any> {
    return this.request<any>("/api/v1/users/me/preferences", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  // Phase 9 Admin Console
  async getAdminDashboard(): Promise<any> {
    return this.request<any>("/api/v1/admin/dashboard", {
      headers: { "x-user-id": "usr_admin_01" },
    });
  }

  async getAdminUsers(): Promise<any[]> {
    return this.request<any[]>("/api/v1/admin/users", {
      headers: { "x-user-id": "usr_admin_01" },
    });
  }

  async updateAdminUserStatus(userId: string, status: string, reason?: string): Promise<any> {
    return this.request<any>(`/api/v1/admin/users/${userId}/status`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "x-user-id": "usr_admin_01",
      },
      body: JSON.stringify({ status, reason }),
    });
  }

  async getAdminAuditLogs(): Promise<any[]> {
    return this.request<any[]>("/api/v1/admin/audit-logs", {
      headers: { "x-user-id": "usr_admin_01" },
    });
  }
}

export const api = new ApiService();
