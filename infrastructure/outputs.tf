output "name_prefix" {
  description   = "Random prefix used for resource names"
  value         = random_pet.prefix.id
}

output "resource_group_name" {
  description   = "name of the resource group"
  value         = azurerm_resource_group.rg.name
}

output "acr_name" {
  description   = "The name of the container registry"
  value = azurerm_container_registry.acr.name
}

output "acr_login_server" {
  description = "Login to login to the container registry"
  value = azurerm_container_registry.acr.login_server
}


output "postgres_fqdn" {
  description   = "Connection string for the PostgreSQL Database endpoint JDBC: <host>.postgres.database.azure.com"
  value         = azurerm_postgresql_flexible_server.postgres.fqdn
}

output "postgres_admin_username" {
  description   = "The username for the PostgreSQL Admin user"
  value         = azurerm_postgresql_flexible_server.postgres.administrator_login
}

output "postgres_admin_password" {
  description   = "The password for the PostgreSQL Admin user"
  value         = azurerm_postgresql_flexible_server.postgres.administrator_password
  sensitive = true
}

output "postgres_database_name" {
  description   = "The name of the PostgreSQL database"
  value         =  azurerm_postgresql_flexible_server_database.app_db.name
}

output "webapp_hostnames" {
  description   = "The hostname for the Azure Web Apps"
  value         = {
    for k, v in azurerm_linux_web_app.apps : k => v.default_hostname
  }
}

output "webapp_names" {
  value = [for k, v in azurerm_linux_web_app.apps : v.name]
}

output "webapp_image_patterns" {
  value = { for k, v in azurerm_linux_web_app.apps : k => "${azurerm_container_registry.acr.login_server}/${random_pet.prefix.id}-${k}:<TAG>" }
}