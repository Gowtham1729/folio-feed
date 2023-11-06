resource "google_project_iam_member" "artifact_registry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

resource "google_project_iam_member" "kubernetes_engine_cluster_viewer" {
  project = var.project_id
  role    = "roles/container.clusterViewer"
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

resource "google_project_iam_member" "kubernetes_engine_developer" {
  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}