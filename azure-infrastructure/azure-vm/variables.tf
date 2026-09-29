variable "subscription_id" {
  description = "Azure subscription ID used for this deployment."
  type        = string
}

variable "resource_group_name" {
  description = "Resource group for the VM and its networking resources."
  type        = string
  default     = "inf2006-azure-rg"
}

variable "location" {
  description = "Azure region for the VM."
  type        = string
  default     = "southeastasia"
}

variable "vm_name" {
  description = "Name of the Linux VM."
  type        = string
  default     = "inf2006-vm"
}

variable "vm_size" {
  description = "Azure VM size. Confirm quota and regional availability first."
  type        = string
  default     = "Standard_B2s"
}

variable "admin_username" {
  description = "Linux administrator username."
  type        = string
  default     = "azureuser"
}

variable "admin_cidr" {
  description = "Public IPv4 CIDR allowed to connect over SSH, for example 203.0.113.10/32."
  type        = string
}

variable "admin_ssh_public_key" {
  description = "OpenSSH public key for the VM administrator."
  type        = string
}

variable "tags" {
  description = "Tags applied to Azure resources."
  type        = map(string)
  default = {
    project     = "INF2006"
    environment = "development"
    managed_by  = "terraform"
  }
}
