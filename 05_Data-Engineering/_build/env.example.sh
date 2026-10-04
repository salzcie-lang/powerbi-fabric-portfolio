# Copy to env.sh, fill in the ids for your own workspace, then: source _build/env.sh
# Tokens come from the Azure CLI login (az login); nothing is stored.
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1
export FAB_TOKEN=$(az account get-access-token --resource https://analysis.windows.net/powerbi/api --query accessToken -o tsv 2>/dev/null | tr -d '\r\n')
export FAB_TOKEN_ONELAKE=$(az account get-access-token --resource https://storage.azure.com --query accessToken -o tsv 2>/dev/null | tr -d '\r\n')
export FABRIC_TOKEN=$(az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv 2>/dev/null | tr -d '\r\n')
export SQL_TOKEN=$(az account get-access-token --resource https://database.windows.net --query accessToken -o tsv 2>/dev/null | tr -d '\r\n')

export WS="<workspace name>.Workspace"
export WS_ID=<workspace guid>
export LH_ID=<lakehouse guid>
export LH_SQL_ID=<lakehouse SQL endpoint guid>
export WH_ID=<warehouse guid>
export SQL_HOST=<warehouse>.datawarehouse.fabric.microsoft.com
export PROJ="<absolute path to this folder>"
