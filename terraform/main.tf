# 1. Create Resource Group
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# 2. Create Azure Container Registry (ACR)
resource "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Standard"
  admin_enabled       = true
}

# 3. Create Postgres Flexible Server (MISSING IN YOUR SNIPPET)
# This is where your tenant, user, and usage data lives.
resource "azurerm_postgresql_flexible_server" "db" {
  name                   = "bravado-db-prod"
  resource_group_name    = azurerm_resource_group.rg.name
  location               = azurerm_resource_group.rg.location
  version                = "14"
  administrator_login    = "bravadoadmin"
  administrator_password = var.db_password # Ensure this is in variables.tf as sensitive
  storage_mb             = 32768
  sku_name               = "GP_Standard_D2s_v3"
  
  # Crucial for SaaS reliability
  zone = "1"
}

# Allow AKS/Azure services to communicate with the DB
resource "azurerm_postgresql_flexible_server_firewall_rule" "aks_access" {
  name             = "AllowAzureAccess"
  server_id        = azurerm_postgresql_flexible_server.db.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# 4. Create Azure Kubernetes Service (AKS)
resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.aks_cluster_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "bravado"

  default_node_pool {
    name       = "default"
    node_count = var.node_count
    vm_size    = var.vm_size
    os_sku     = "Ubuntu2404" # 2026 Standard
  }

  identity {
    type = "SystemAssigned"
  }

  # MODERN SECURITY (Added for 2026 Workload Identity support)
  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  tags = {
    Environment = "Production"
    Project     = "Bravado-Solutions"
  }
}

# 5. Give AKS permission to pull images from ACR
resource "azurerm_role_assignment" "aks_to_acr" {
  principal_id                     = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                            = azurerm_container_registry.acr.id
  skip_service_principal_aad_check = true
}