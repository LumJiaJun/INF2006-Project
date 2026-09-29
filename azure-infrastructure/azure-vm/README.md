# Azure VM Terraform

This Terraform root provisions the Azure VM used by the VM deployment path in `AZURE_MIGRATION.md`. It is separate from the AWS Terraform root under `src/infrastructure`.

## Usage

1. Install Terraform and Azure CLI.
2. Authenticate with Azure:

   ```powershell
   az login
   ```

3. Copy the example variables file and replace every placeholder, especially the subscription ID, administrator CIDR, and SSH public key:

   ```powershell
   Copy-Item terraform.tfvars.example terraform.tfvars
   ```

4. Format, initialize, validate, and plan:

   ```powershell
   terraform fmt
   terraform init
   terraform validate
   terraform plan -out tfplan
   ```

5. Review `tfplan`, then apply it:

   ```powershell
   terraform apply tfplan
   terraform output -raw public_ip
   ```

`terraform.tfvars`, `tfplan`, and Terraform state are local deployment artifacts and must not be committed. Configure an Azure Blob backend before using this root with a team or shared environment.

Terraform creates infrastructure only. Follow the VM application deployment steps in `AZURE_MIGRATION.md` to install Nginx, copy the source code, configure `config.js`, and start the API adapter.
