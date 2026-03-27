/* Zustand global store. */

import { create } from "zustand"
import type {
  RiskEvent,
  RegionRiskScore,
  Workload,
  SimulationResult,
  MigrationLog,
} from "./types"

interface AppState {
  riskScores: Record<string, Record<string, RegionRiskScore>>
  signals: RiskEvent[]
  workloads: Workload[]
  migrations: MigrationLog[]
  simulations: SimulationResult[]
  selectedRegion: { provider: string; region_id: string } | null
  isLoading: boolean

  setRiskScores: (s: Record<string, Record<string, RegionRiskScore>>) => void
  setSignals: (s: RiskEvent[]) => void
  setWorkloads: (w: Workload[]) => void
  setMigrations: (m: MigrationLog[]) => void
  setSimulations: (s: SimulationResult[]) => void
  setSelectedRegion: (r: { provider: string; region_id: string } | null) => void
  setIsLoading: (b: boolean) => void
}

export const useAppStore = create<AppState>((set) => ({
  riskScores: {},
  signals: [],
  workloads: [],
  migrations: [],
  simulations: [],
  selectedRegion: null,
  isLoading: false,

  setRiskScores: (s) => set({ riskScores: s }),
  setSignals: (s) => set({ signals: s }),
  setWorkloads: (w) => set({ workloads: w }),
  setMigrations: (m) => set({ migrations: m }),
  setSimulations: (s) => set({ simulations: s }),
  setSelectedRegion: (r) => set({ selectedRegion: r }),
  setIsLoading: (b) => set({ isLoading: b }),
}))
