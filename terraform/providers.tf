terraform {
  required_version = ">= 1.5.0"

  # 1. Required Providers with 2026 Production Constraints
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.90.0" 
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.47.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12.0"
    }
  }

  # 2. Remote Backend
  # Note: The storage account and container must exist before running 'terraform init'
  backend "azurerm" {
    resource_group_name  = "bravado-tfstate-rg"
    storage_account_name = "bravadotfstorage"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
  }
}

# 3. Azure Provider Configuration
provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    postgresql_flexible_server {
      skip_drop_database = false
    }
  }
}

provider "azuread" {}

# 4. Kubernetes Provider
# Authenticates directly to your AKS cluster using the kube_config output
provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.aks.kube_config.0.host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.cluster_ca_certificate)
}

# 5. Helm Provider
# Allows Terraform to install charts (like Qdrant or Nginx) into your AKS cluster
provider "helm" {
  kubernetes {
    host                   = azurerm_kubernetes_cluster.aks.kube_config.0.host
    client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_certificate)
    client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_key)
    cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.cluster_ca_certificate)
  }
}