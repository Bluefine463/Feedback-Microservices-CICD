variable "location" {
  description = "Azure region to use (centralindia, southindia, westindia)"
  type        = string
  default     = "centralindia"
}

variable "name_prefix" {
  description = "A prefix used for all resources in this example"
  type        = string
  default     = "cheker"
}

variable "microservices" {
  description = "List of names for webapp suffixes"
  type        = list(string)
  default = ["api-gateway","eureka-server","feedback-service","user-service","genai-service"]
}

variable "postgres_admin" {
  description = "The PostgreSQL Admin User"
  type        = string
  default     = "pgadminuser"
}

variable "postgres_version" {
  description = "The PostgreSQL version"
  type        = string
  default     = "13"
}