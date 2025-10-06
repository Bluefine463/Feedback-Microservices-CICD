resource "random_pet" "prefix" {
  length = 2
  prefix = var.name_prefix
}

resource "azurerm_resource_group" "rg" {
  name     = "${random_pet.prefix.id}-rg"
  location = var.location
}

resource "azurerm_service_plan" "asp" {
  name                = "${random_pet.prefix.id}-asp"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "B1"
}

resource "azurerm_container_registry" "acr" {
  # FIX: Removed hyphens from the name using the replace() function.
  name                = replace("${random_pet.prefix.id}acr", "-", "")
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = false
}

resource "azurerm_linux_web_app" "apps" {
  for_each = toset(var.microservices)

  name                = "${random_pet.prefix.id}-${each.value}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.asp.id
  https_only          = true

  identity {
    type = "SystemAssigned"
  }

  # FIX: Removed site_config block to break the dependency cycle.
  # The container configuration is now handled by the azurerm_app_service_configuration resource below.
}

# FIX: Added this new resource to configure the web apps after they are created.
resource "azurerm_app_service_configuration" "apps_config" {
  for_each = azurerm_linux_web_app.apps

  app_service_id = each.value.id

  site_config {
    # FIX: Corrected random_pet.prefix to random_pet.prefix.id to reference the string attribute.
    linux_fx_version = "DOCKER|${azurerm_container_registry.acr.login_server}/${random_pet.prefix.id}-${each.key}:latest"
    always_on        = true
  }
}

resource "random_password" "pg_pass" {
  length           = 20
  override_special = "_%@"
}

resource "azurerm_postgresql_flexible_server" "postgres" {
  name                   = "${random_pet.prefix.id}-pg"
  resource_group_name    = azurerm_resource_group.rg.name
  location               = azurerm_resource_group.rg.location
  version                = var.postgres_version
  administrator_login    = var.postgres_admin
  administrator_password = random_password.pg_pass.result

  # FIX: Corrected the SKU name to a valid one for PostgreSQL Flexible Server.
  sku_name            = "B_Standard_B1ms"
  storage_mb          = 32768
  backup_retention_days = 7
  zone                = "1"

  public_network_access_enabled = true
}

resource "azurerm_postgresql_flexible_server_database" "app_db" {
  name      = "${random_pet.prefix.id}_db"
  server_id = azurerm_postgresql_flexible_server.postgres.id

  # FIX: Corrected collation name to be lowercase utf8.
  collation = "en_US.utf8"
  charset   = "UTF8"
}

resource "azurerm_role_assignment" "acr_pull" {
  for_each = azurerm_linux_web_app.apps

  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"

  # FIX: Correctly accessed the principal_id from the first element of the identity list.
  principal_id = each.value.identity[0].principal_id

  # FIX: Replaced non-existent 'guid' function with 'uuidv5' for a stable, deterministic ID.
  name = uuidv5("e4085f1d-0f2c-4809-88b4-528742b7864c", "${each.value.id}-${azurerm_container_registry.acr.id}")
}