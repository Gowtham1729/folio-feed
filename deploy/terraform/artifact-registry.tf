resource "google_artifact_registry_repository" "image-registry" {
  location = var.region
  repository_id = "image-registry"
  description = "Folio feed docker image registry"
  format = "DOCKER"
}