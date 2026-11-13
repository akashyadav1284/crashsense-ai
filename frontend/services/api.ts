import { config } from "@/config";
import { HealthState } from "@/types";

export async function fetchHealth(): Promise<HealthState | null> {
  try {
    const res = await fetch(`${config.apiUrl}/health`, {
      cache: "no-store",
    });
    if (!res.ok) {
      throw new Error(`Failed to fetch health status: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.error("Health check error:", error);
    return null;
  }
}

