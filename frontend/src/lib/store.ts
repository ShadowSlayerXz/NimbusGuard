/* Zustand global store. */

import { create } from "zustand"
import type {
  RegionRiskScore,
  Workload,
  MigrationLog,
} from "./types"

interface AppState {
  riskScores: Record<string, Record<string, RegionRiskScore>>
  workloads: Workload[]
  migrations: MigrationLog[]
  isLoading: boolean

  setRiskScores: (s: Record<string, Record<string, RegionRiskScore>>) => void
  setWorkloads: (w: Workload[]) => void
  setMigrations: (m: MigrationLog[]) => void
  setIsLoading: (b: boolean) => void
}

export const useAppStore = create<AppState>((set) => ({
  riskScores: {},
  workloads: [],
  migrations: [],
  isLoading: false,

  setRiskScores: (s) => set({ riskScores: s }),
  setWorkloads: (w) => set({ workloads: w }),
  setMigrations: (m) => set({ migrations: m }),
  setIsLoading: (b) => set({ isLoading: b }),
}))
