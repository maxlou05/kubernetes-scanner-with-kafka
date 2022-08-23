from datetime import datetime
import generate_logs
from kubernetes import client, config
from kubernetes.client import CoreV1Api
import requests
import time
import json


def run(coreAPI:CoreV1Api):
    while True:
        print("--------------------SCAN BEGAN AT {}----------------------".format(datetime.now().isoformat()))
        
        # First, import settings, just in case they ever changed
        settings = generate_logs.import_settings("settings.json")
        
        # Save previous network functions so they can be compared later 
        generate_logs.save_previous_nfs()
        
        # Get all the current namespaces
        results = coreAPI.list_namespace()
        current_namespaces = []
        for i in results.items:
            current_namespaces.append(i.metadata.name)
        
        # scan the namespaces to see which one are network functions
        generate_logs.scan_for_nfs(current_namespaces, settings["network_functions"])
        
        print("\n-------------------------------LOGS----------------------------------")
        
        # Generate logs based on the difference between last iteration and this one
        generate_logs.diff()

        try:
            with open("logs.json", 'r') as file:
                print(file.read())
            # If there are changes, then upload the changes to the kafka topic
            print("\nuploading logs to kafka...")
            response = generate_logs.upload_to_kafka(settings["kafka_config"]["api_ip"], settings["kafka_config"]["topic"])
            print(response.status_code)
            print(json.dumps(response.json(), indent=2))
            print("successfully uploaded logs to kafka")
        
        # If no logs.json file, means no logs were needed/generated for this scan
        except FileNotFoundError:
            print("No changes since last update")

        print("\n----------------------------SCAN COMPLETE-------------------------------\n\n\n")

        # Wait until next scan
        time.sleep(settings["scan_interval_minutes"]*60)



# MAIN
config.load_incluster_config()
print("config is loaded")

v1 = client.CoreV1Api()
print("client is created, starting scan")

# Create a topic
print("checking if topic exists")
settings = generate_logs.import_settings("settings.json")
ip = settings["kafka_config"]["api_ip"]
response = requests.get(f"http://{ip}:8082/v3/clusters")
print(response.status_code)
data = response.json()
print(json.dumps(data, indent=2))
topic_url = data["data"][0]["topics"]["related"]
response = requests.get(topic_url)
print(response.status_code)
data = response.json()
print(json.dumps(data, indent=2))
# if len(data["data"]) < 1:
payload = {"topic_name": "my-logs-3", "partitions_count":3, "replication_factor":3}
response = requests.post(topic_url, json=payload, headers={"Content-Type": "application/json"})
print(response.status_code)
print(json.dumps(response.json(), indent=2))

run(v1)

# settings = generate_logs.import_settings("settings.json")
# upload_to_kafka(settings["kafka_config"], settings["kafka_topic"], ["log from k8 app"])
