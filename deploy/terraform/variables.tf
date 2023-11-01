variable "project_id" {
    description = "The project ID to deploy to"
    type = string
}

variable "region" {
    description = "The region to deploy to"
    type = string
}

variable "zone" {
    description = "The zone to deploy to"
    type = string
}

variable "gke-cluster-name" {
    description = "The name of the GKE cluster"
    type = string
}