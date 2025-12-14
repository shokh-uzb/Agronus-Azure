#!/bin/bash
# Helper script to configure Azure App Service environment variables
# Usage: ./setup-azure-env.sh <resource-group-name> <app-service-name>

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <resource-group-name> <app-service-name>"
    echo "Example: $0 myResourceGroup agronus-api"
    exit 1
fi

RESOURCE_GROUP=$1
APP_NAME=$2

echo "Configuring Azure App Service: $APP_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI is not installed."
    echo "Install it from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo "Please login to Azure first:"
    az login
fi

echo "Setting application settings..."
echo ""

# Prompt for Azure OpenAI settings
read -p "Enter Azure OpenAI API Key: " OPENAI_KEY
read -p "Enter Azure OpenAI Endpoint (e.g., https://your-resource.openai.azure.com/): " OPENAI_ENDPOINT
read -p "Enter Azure OpenAI Deployment Name (default: gpt-4o): " OPENAI_DEPLOYMENT
OPENAI_DEPLOYMENT=${OPENAI_DEPLOYMENT:-gpt-4o}

# Set all application settings at once
az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --settings \
    AZURE_OPENAI_API_KEY="$OPENAI_KEY" \
    AZURE_OPENAI_ENDPOINT="$OPENAI_ENDPOINT" \
    AZURE_OPENAI_DEPLOYMENT="$OPENAI_DEPLOYMENT" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
  --output table

echo ""
echo "Setting startup command..."
az webapp config set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --startup-file "bash startup.sh" \
  --output table

echo ""
echo "✅ Configuration complete!"
echo ""
echo "To verify, run:"
echo "  az webapp config appsettings list --resource-group $RESOURCE_GROUP --name $APP_NAME --output table"
