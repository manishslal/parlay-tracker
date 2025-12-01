import requests
import os

# API Key provided by user
API_KEY = "rnd_Sr7QSGI72ZEYaicB47UOZI0CDPyl"
SERVICE_ID = "srv-d3qlvdt6ubrc7382mah0"

def get_logs_via_deployment():
    # 1. Get deployments for the service
    # Verify service ID first
    deploy_url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }
    
    try:
        print(f"Fetching deployments from: {deploy_url}")
        response = requests.get(deploy_url, headers=headers, params={"limit": 1})
        if response.status_code != 200:
            print(f"Error fetching deployments: {response.status_code} - {response.text}")
            return

        deployments = response.json()
        if not deployments:
            print("No deployments found.")
            return
            
        # Inspect structure
        first_deploy = deployments[0]
        print(f"First deploy structure: {first_deploy.keys()}")
        
        # Adjust based on structure
        if 'deploy' in first_deploy:
            latest_deploy = first_deploy['deploy']
        elif 'deployment' in first_deploy:
            latest_deploy = first_deploy['deployment']
        else:
            latest_deploy = first_deploy
            
        deploy_id = latest_deploy['id']
        print(f"Latest deployment ID: {deploy_id} (Status: {latest_deploy.get('status')})")
        
        # 2. Get logs for the deployment
        # Try service-scoped URL
        logs_url = f"https://api.render.com/v1/services/{SERVICE_ID}/deploys/{deploy_id}/logs"
        
        print(f"Fetching logs for deployment {deploy_id} from {logs_url}...")
        log_response = requests.get(logs_url, headers=headers, params={"limit": 100})
        
        if log_response.status_code == 200:
            data = log_response.json()
            # Render API returns a list of log objects or an object with 'logs' key?
            # Docs say array of objects.
            logs = data if isinstance(data, list) else data.get('logs', [])
            print(f"Fetched {len(logs)} log entries:")
            for log in logs:
                ts = log.get('timestamp', '')
                msg = log.get('message', '')
                print(f"[{ts}] {msg}")
        else:
            print(f"Error fetching logs: {log_response.status_code} - {log_response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

def get_service_details():
    url = f"https://api.render.com/v1/services/{SERVICE_ID}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }
    try:
        print(f"Fetching service details from: {url}")
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("Service Details:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error fetching service: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    import json
    # list_services()
    # get_service_details()
    get_logs_via_deployment()
