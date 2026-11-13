import { create } from "zustand";

interface NavigationState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
}

export const useNavigationStore = create<NavigationState>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));

interface PaperTradingState {
  virtualBalance: number;
  initialBalance: number;
  simulatedStake: number;
  targetCashout: number;
  simulationActive: boolean;
  sessionDurationSec: number;
  emergencyStop: boolean;
  dailyLossLimit: number;
  currentLossToday: number;
  setStake: (val: number) => void;
  setCashout: (val: number) => void;
  toggleSimulation: () => void;
  resetSession: () => void;
  triggerEmergencyStop: () => void;
}

export const usePaperTradingStore = create<PaperTradingState>((set) => ({
  virtualBalance: 10000.0,
  initialBalance: 10000.0,
  simulatedStake: 100.0,
  targetCashout: 1.50,
  simulationActive: false,
  sessionDurationSec: 0,
  emergencyStop: false,
  dailyLossLimit: 1500.0,
  currentLossToday: 0.0,
  setStake: (simulatedStake) => set({ simulatedStake }),
  setCashout: (targetCashout) => set({ targetCashout }),
  toggleSimulation: () => set((s) => ({ simulationActive: !s.simulationActive })),
  resetSession: () =>
    set({
      virtualBalance: 10000.0,
      simulationActive: false,
      sessionDurationSec: 0,
      emergencyStop: false,
      currentLossToday: 0.0,
    }),
  triggerEmergencyStop: () =>
    set({
      simulationActive: false,
      emergencyStop: true,
    }),
}));

