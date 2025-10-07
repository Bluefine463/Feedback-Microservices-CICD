locals {
  # Create a predictable prefix, e.g., "build35cheker"
  prefix = "build${var.build_id}${var.name_prefix}"
}

resource "azurerm_resource_group" "rg" {
  name     = "${local.prefix}-rg"
  location = var.location
}

resource "azurerm_service_plan" "asp" {
  name                = "${local.prefix}-asp"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "B1"
}

resource "azurerm_container_registry" "acr" {
  name                = replace(local.prefix, "-", "")
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = false
}

resource "azurerm_linux_web_app" "apps" {
  for_each = toset(var.microservices)

  name                = "${local.prefix}-${each.value}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.asp.id

  identity {
    type = "SystemAssigned"
  }

  site_config {
    always_on = true

    application_stack {
      docker_image_name   = "${azurerm_container_registry.acr.login_server}/${local.prefix}-${each.key}:latest"
      docker_registry_url = "https://${azurerm_container_registry.acr.login_server}"
    }
  }


  # app_settings = {
  #   "DOCKER_REGISTRY_SERVER_URL"      = azurerm_container_registry.acr.login_server
  #   # "DOCKER_REGISTRY_SERVER_USERNAME" = azurerm_container_registry.acr.admin_username
  #   # "DOCKER_REGISTRY_SERVER_PASSWORD" = azurerm_container_registry.acr.admin_password
  # }
  app_settings = {
    "DOCKER_REGISTRY_SERVER_URL" = "https://${azurerm_container_registry.acr.login_server}"
  }
}


resource "random_password" "pg_pass" {
  length           = 20
  override_special = "_%@"
}

resource "azurerm_postgresql_flexible_server" "postgres" {
  name                   = "${local.prefix}-pg"
  resource_group_name    = azurerm_resource_group.rg.name
  location               = azurerm_resource_group.rg.location
  version                = var.postgres_version
  administrator_login    = var.postgres_admin
  administrator_password = random_password.pg_pass.result
  sku_name               = "B_Standard_B1ms"
  storage_mb             = 32768
  backup_retention_days  = 7
  zone                   = "1"
  public_network_access_enabled = true
}

resource "azurerm_postgresql_flexible_server_database" "app_db" {
  name      = "${local.prefix}_db"
  server_id = azurerm_postgresql_flexible_server.postgres.id
  collation = "en_US.utf8"
  charset   = "UTF8"
}

resource "azurerm_role_assignment" "acr_pull" {
  for_each = azurerm_linux_web_app.apps

  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = each.value.identity[0].principal_id
  name                 = uuidv5("e4085f1d-0f2c-4809-88b4-528742b7864c", "${each.value.id}-${azurerm_container_registry.acr.id}")
}