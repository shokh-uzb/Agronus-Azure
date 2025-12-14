# PowerShell script to configure Azure App Service environment variables
# Usage: .\setup-azure-env.ps1 -ResourceGroupName <resource-group-name> -AppServiceName <app-service-name>

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$AppServiceName
)

Write-Host "Configuring Azure App Service: $AppServiceName" -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroupName" -ForegroundColor Green
Write-Host ""

# Check if Azure CLI is installed
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Azure CLI is not installed." -ForegroundColor Red
    Write-Host "Install it from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    exit 1
}

# Check if logged in
try {
    az account show | Out-Null
} catch {
    Write-Host "Please login to Azure first..." -ForegroundColor Yellow
    az login
}

Write-Host "Setting application settings..." -ForegroundColor Cyan
Write-Host ""

# Prompt for Azure OpenAI settings
$OpenAIKey = Read-Host "Enter Azure OpenAI API Key"
$OpenAIEndpoint = Read-Host "Enter Azure OpenAI Endpoint (e.g., https://your-resource.openai.azure.com/)"
$OpenAIDeployment = Read-Host "Enter Azure OpenAI Deployment Name (default: gpt-4o)"
if ([string]::IsNullOrWhiteSpace($OpenAIDeployment)) {
    $OpenAIDeployment = "gpt-4o"
}

# Set all application settings at once
az webapp config appsettings set `
  --resource-group $ResourceGroupName `
  --name $AppServiceName `
  --settings `
    AZURE_OPENAI_API_KEY="$OpenAIKey" `
    AZURE_OPENAI_ENDPOINT="$OpenAIEndpoint" `
    AZURE_OPENAI_DEPLOYMENT="$OpenAIDeployment" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" `
  --output table

Write-Host ""
Write-Host "Setting startup command..." -ForegroundColor Cyan
az webapp config set `
  --resource-group $ResourceGroupName `
  --name $AppServiceName `
  --startup-file "bash startup.sh" `
  --output table

Write-Host ""
Write-Host "✅ Configuration complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To verify, run:" -ForegroundColor Yellow
Write-Host "  az webapp config appsettings list --resource-group $ResourceGroupName --name $AppServiceName --output table" -ForegroundColor Gray
