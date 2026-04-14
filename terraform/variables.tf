variable "resource_group_name" {
  type        = string
  description = "The name of the resource group"
  default     = "bravado-resources"
}

variable "location" {
  type        = string
  description = "The Azure region for deployment"
  default     = "East US"
}

variable "aks_cluster_name" {
  type        = string
  description = "The name of the AKS cluster"
  default     = "bravado-aks"
}

variable "acr_name" {
  type        = string
  description = "The name of the Azure Container Registry (Alphanumeric only)"
  default     = "bravadoacr"
}

variable "node_count" {
  type        = number
  description = "The number of nodes in the AKS cluster"
  default     = 2
}

variable "vm_size" {
  type        = string
  description = "The size of the Virtual Machines for the nodes"
  default     = "Standard_DS2_v2"
}

variable "db_password" {
  type        = string
  description = "The administrator password for the Postgres Flexible Server"
  sensitive   = true
}