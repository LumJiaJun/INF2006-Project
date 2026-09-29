output "public_ip" {
  description = "Static public IP address of the VM."
  value       = azurerm_public_ip.app.ip_address
}

output "ssh_command" {
  description = "SSH command template for the VM."
  value       = "ssh ${var.admin_username}@${azurerm_public_ip.app.ip_address}"
}
