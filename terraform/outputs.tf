output "resource_group_name" {
  description = "The name of the Resource Group"
  value       = azurerm_resource_group.rg.name
}

output "aks_cluster_name" {
  description = "The name of the AKS cluster"
  value       = azurerm_kubernetes_cluster.aks.name
}

output "acr_login_server" {
  description = "The URL for the Azure Container Registry"
  value       = azurerm_container_registry.acr.login_server
}

output "postgres_fqdn" {
  description = "The Fully Qualified Domain Name of the Postgres server"
  value       = azurerm_postgresql_flexible_server.db.fqdn
}

output "oidc_issuer_url" {
  description = "The OIDC Issuer URL for Workload Identity"
  value       = azurerm_kubernetes_cluster.aks.oidc_issuer_url
}

output "control_plane_fqdn" {
  description = "The FQDN of the AKS Control Plane"
  value       = azurerm_kubernetes_cluster.aks.fqdn
}