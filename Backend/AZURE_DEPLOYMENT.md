# Azure App Service Deployment Guide for Agronus Backend

## Prerequisites

1. Azure App Service created with:
   - **Runtime stack**: Python 3.11
   - **Operating System**: Linux
   - **App Service Plan**: Standard or higher (for better performance)

## Required Azure Configuration

### 1. Application Settings (Environment Variables)

You need to configure these environment variables. Here are multiple ways to do it:

#### Method 1: Azure Portal (Recommended)

**Step-by-step navigation:**

1. Go to [Azure Portal](https://portal.azure.com)
2. In the search bar at the top, type: `agronus-api` (or your app service name)
3. Click on your App Service from the results
4. In the left sidebar menu, look for **"Settings"** section
5. Click on **"Configuration"** (it might also be labeled as **"App settings"** or **"Environment variables"**)
6. You should see two tabs: **"Application settings"** and **"General settings"**
7. Click on the **"Application settings"** tab
8. Click **"+ New application setting"** to add each variable

**If you can't find "Configuration":**
- Look in the left sidebar for **"Settings"** → **"Configuration"**
- Or try: Left sidebar → **"Settings"** → **"Application settings"**
- Or use the search box in the left sidebar and type "Configuration"

**Add these application settings:**

- **Name**: `AZURE_OPENAI_API_KEY`, **Value**: Your Azure OpenAI API key
- **Name**: `AZURE_OPENAI_ENDPOINT`, **Value**: Your Azure OpenAI endpoint URL
- **Name**: `AZURE_OPENAI_DEPLOYMENT`, **Value**: `gpt-4o` (or your deployment name)
- **Name**: `SCM_DO_BUILD_DURING_DEPLOYMENT`, **Value**: `true`

**Note**: Do NOT set `PORT` - Azure sets this automatically.

After adding each setting, click **"Save"** at the top of the page.

#### Method 2: Azure CLI (Alternative)

If you have Azure CLI installed, you can set these using commands:

```bash
# Set Azure OpenAI API Key
az webapp config appsettings set \
  --resource-group <your-resource-group-name> \
  --name agronus-api \
  --settings AZURE_OPENAI_API_KEY="your-api-key-here"

# Set Azure OpenAI Endpoint
az webapp config appsettings set \
  --resource-group <your-resource-group-name> \
  --name agronus-api \
  --settings AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/"

# Set Deployment Name
az webapp config appsettings set \
  --resource-group <your-resource-group-name> \
  --name agronus-api \
  --settings AZURE_OPENAI_DEPLOYMENT="gpt-4o"

# Enable build during deployment
az webapp config appsettings set \
  --resource-group <your-resource-group-name> \
  --name agronus-api \
  --settings SCM_DO_BUILD_DURING_DEPLOYMENT="true"
```

Replace `<your-resource-group-name>` with your actual resource group name.

#### Method 3: Using Helper Scripts (Easiest)

We've provided helper scripts to automate this process:

**For Linux/Mac/Git Bash:**
```bash
cd Backend
chmod +x setup-azure-env.sh
./setup-azure-env.sh <your-resource-group-name> agronus-api
```

**For Windows PowerShell:**
```powershell
cd Backend
.\setup-azure-env.ps1 -ResourceGroupName <your-resource-group-name> -AppServiceName agronus-api
```

The script will prompt you for your Azure OpenAI credentials and configure everything automatically.

#### Method 4: Direct URL

You can also navigate directly to the configuration page:
```
https://portal.azure.com/#@<your-tenant>/resource/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.Web/sites/agronus-api/config
```

Replace the placeholders with your actual values.

### 2. Startup Command

**Navigation in Azure Portal:**

1. Go to your App Service in Azure Portal
2. In the left sidebar, click **"Settings"** → **"Configuration"**
3. Click on the **"General settings"** tab (next to "Application settings")
4. Scroll down to find **"Startup Command"** field
5. Enter: `bash startup.sh`
6. Click **"Save"** at the top

**Alternative:** You can leave the Startup Command empty - Azure will automatically detect and run `startup.sh` if it's present in the root directory of your deployment.

**Using Azure CLI:**
```bash
az webapp config set \
  --resource-group <your-resource-group-name> \
  --name agronus-api \
  --startup-file "bash startup.sh"
```

### 3. GitHub Secrets

Ensure your GitHub repository has the following secret configured:

- `AZURE_WEBAPP_PUBLISH_PROFILE`: Your Azure App Service publish profile
  - Get this from: Azure Portal → Your App Service → Get publish profile

## Deployment Process

The GitHub Actions workflow (`.github/workflows/deploy-backend.yml`) will automatically:

1. Install Python dependencies from `requirements-azure.txt`
2. Make `startup.sh` executable
3. Create a deployment package (zip file)
4. Deploy to Azure App Service

## Quick Reference: Finding Configuration in Azure Portal

If you're having trouble finding the Configuration page, try these steps:

1. **Search Method (Easiest):**
   - Click the search box at the top of Azure Portal
   - Type: `agronus-api configuration` or just `agronus-api`
   - Select your app service
   - Look for "Configuration" in the left sidebar under "Settings"

2. **Direct Navigation:**
   - All Resources → Search for `agronus-api` → Click it
   - Left sidebar → Under "Settings" section → Click "Configuration"

3. **Alternative Names:**
   - Some Azure Portal versions show it as "App settings" instead of "Configuration"
   - Look for "Environment variables" or "Application settings" in the left sidebar

4. **If Still Can't Find:**
   - Use Azure CLI method (Method 2 above) - it's often faster
   - Or use the Azure Portal search: Type "web app" and filter by your app name

## Troubleshooting

### Can't Find Application Settings/Configuration Page

If you cannot locate the Configuration page:
- **Use Azure CLI** (see Method 2 above) - it's the most reliable way
- **Check your permissions** - You need "Contributor" or "Owner" role on the App Service
- **Try different browser** - Sometimes Azure Portal UI varies by browser
- **Use Azure Portal mobile app** - Sometimes the mobile app has different navigation

### Application Not Starting

1. **Check Logs**: Azure Portal → Your App Service → Log stream
2. **Verify Startup Command**: Ensure `startup.sh` is in the root of your deployment
3. **Check Port**: The app should listen on the `PORT` environment variable (Azure sets this automatically)

### Dependencies Not Installing

1. Verify `SCM_DO_BUILD_DURING_DEPLOYMENT` is set to `true`
2. Check `requirements-azure.txt` for any missing dependencies
3. Review deployment logs in GitHub Actions

### Vector Database Not Loading

1. Ensure `agronus_vdb` directory and all its contents are included in the deployment
2. Check file permissions - the app needs read/write access to the vector database directory

### Model File Not Found

1. Verify `crop_recommendation_model_v1.pkl` is included in the deployment package
2. Check the file path in `app.py` matches the deployment structure

## Manual Deployment (Alternative)

If GitHub Actions deployment fails, you can deploy manually:

1. Zip the Backend directory (excluding unnecessary files):
   ```bash
   cd Backend
   zip -r ../backend.zip . -x "*.pyc" -x "__pycache__/*" -x "*.ipynb" -x ".git/*" -x "venv/*" -x ".env"
   ```

2. Deploy using Azure CLI:
   ```bash
   az webapp deployment source config-zip \
     --resource-group <your-resource-group> \
     --name agronus-api \
     --src backend.zip
   ```

## Health Check

After deployment, verify the application is running:

```bash
curl https://agronus-api.azurewebsites.net/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Agronus API",
  "model_loaded": true,
  "vector_store_loaded": true,
  "llm_configured": true
}
```
