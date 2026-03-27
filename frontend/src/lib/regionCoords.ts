/* Lat/lon coordinates for cloud region markers on the map. */

export const REGION_COORDS: Record<string, [number, number]> = {
  /* ── AWS ─────────────────────────────────────────────── */
  "us-east-1":      [39.0, -77.5],
  "us-east-2":      [40.0, -83.0],
  "us-west-1":      [37.4, -122.1],
  "us-west-2":      [45.5, -122.7],
  "eu-west-1":      [53.3, -6.3],
  "eu-west-2":      [51.5, -0.1],
  "eu-central-1":   [50.1, 8.7],
  "ap-southeast-1": [1.3, 103.8],
  "ap-southeast-2": [-33.9, 151.2],
  "ap-northeast-1": [35.7, 139.7],
  "ap-south-1":     [19.1, 72.9],
  "sa-east-1":      [-23.5, -46.6],

  /* ── Azure ───────────────────────────────────────────── */
  "eastus":        [37.4, -79.5],
  "eastus2":       [36.7, -78.9],
  "westus":        [37.8, -122.4],
  "westus2":       [47.6, -122.3],
  "northeurope":   [53.3, -6.3],
  "westeurope":    [52.4, 4.9],
  "southeastasia": [1.3, 103.8],
  "eastasia":      [22.3, 114.2],
  "brazilsouth":   [-23.5, -46.6],

  /* ── GCP ─────────────────────────────────────────────── */
  "us-central1":        [41.3, -88.0],
  "us-east1":           [33.8, -84.0],
  "us-west1":           [45.6, -121.2],
  "europe-west1":       [50.4, 3.8],
  "europe-west2":       [51.5, -0.1],
  "asia-southeast1":    [1.3, 103.8],
  "asia-east1":         [24.0, 121.5],
  "asia-south1":        [19.1, 72.9],
  "southamerica-east1": [-23.5, -46.6],
}

/* Provider → list of regions belonging to that provider. */
export const PROVIDER_REGIONS: Record<string, string[]> = {
  aws: [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-west-2", "eu-central-1",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
    "ap-south-1", "sa-east-1",
  ],
  azure: [
    "eastus", "eastus2", "westus", "westus2",
    "northeurope", "westeurope",
    "southeastasia", "eastasia", "brazilsouth",
  ],
  gcp: [
    "us-central1", "us-east1", "us-west1",
    "europe-west1", "europe-west2",
    "asia-southeast1", "asia-east1",
    "asia-south1", "southamerica-east1",
  ],
}
