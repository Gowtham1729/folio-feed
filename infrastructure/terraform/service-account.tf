resource "google_service_account" "github_actions_sa" {
  account_id   = "github-actions"
  display_name = "Github actions"
  description = "Github Actions access to the GCP Project"
}