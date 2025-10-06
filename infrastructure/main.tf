resource "random_pet" "prefix" {
  length              = 2
  prefix              = var.name_prefix
}

resource "azurerm_resource_group" "rg" {
  name                = "${random_pet.prefix.id}-rg"
  location            = var.location
}

resource "azurerm_service_plan" "asp" {
  name                = "${random_pet.prefix.id}-asp"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "B1"
}

resource "azurerm_container_registry" "acr" {
name                = "${random_pet.prefix.id}-acr"
resource_group_name = azurerm_resource_group.rg.name
location            = azurerm_resource_group.rg.location
sku                 = "Basic"
admin_enabled       = false
}

resource "azurerm_linux_web_app" "apps" {

  for_each            = toset(var.microservices)

  name                = "${random_pet.prefix.id}-${each.value}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.asp.id
  https_only          = true

  identity {
    type = "SystemAssigned"
  }
  site_config {
    # always_on         = true
    # java_version      = "17"
    # java_container    = "JAVA"
    linux_fx_version = "DOCKER|${azurerm_container_registry.acr.login_server}/${random_pet.prefix}-${each.value}:latest"
    always_on = true

  }
}

resource "random_password" "pg_pass" {
  length              = 20
  override_special    = "_%@"
}

resource "azurerm_postgresql_flexible_server" "postgres" {
  name                = "${random_pet.prefix.id}-pg"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  version             = var.postgres_version
  administrator_login = var.postgres_admin
  administrator_password = random_password.pg_pass.result

  sku_name            = "B_Standard_B1ms"
  storage_mb          = 32768
  backup_retention_days = 7
  zone                = "1"

  public_network_access_enabled     = true
}

resource "azurerm_postgresql_flexible_server_database" "app_db" {
  name                = "${random_pet.prefix.id}_db"
  server_id           = azurerm_postgresql_flexible_server.postgres.id
  collation           = "en_US.utf8"
  charset             = "UTF8"
}

resource "azurerm_role_assignment" "acr_pull" {
  for_each = azurerm_linux_web_app.apps

  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_linux_web_app.apps[each.key].identity.principal_id
  # use a deterministic name so re-runs are stable
  name = uuidv5("e4085f1d-0f2c-4809-88b4-528742b7864c","${azurerm_linux_web_app.apps[each.key].id}-${azurerm_container_registry.acr.id}")
}