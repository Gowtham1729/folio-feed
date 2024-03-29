resource "google_container_cluster" "folio-feed-cluster" {
  name             = var.gke-cluster-name
  location         = var.region
  enable_autopilot = true

  network             = "default"
  subnetwork          = "default"
  deletion_protection = false

  monitoring_config {
    managed_prometheus {
      enabled = true
    }
    enable_components = [
      "SYSTEM_COMPONENTS",
#      "STORAGE",
#      "HPA",
#      "POD",
#      "DEPLOYMENT",
#      "STATEFULSET"
    ]
  }
}