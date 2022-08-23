from datetime import datetime
import generate_logs
from kubernetes import client, config
from kubernetes.client import CoreV1Api
import requests
import time
import json


def create_topic_if_not_exists(ip:str, topic:str, debug:bool = False):
    if debug:
        print("Creating a topic if not already exists...")
    # Get cluster id to be able to create a topic
    response = requests.get(f"http://{ip}:8082/v3/clusters")
    data = response.json()
    if debug:
        print("Cluster list:")
        print(response.status_code)
        print(json.dumps(data, indent=2))
    # Currently the API only supports returning 1 cluster
    topic_url = data["data"][0]["topics"]["related"]

    # Create a topic if not already exists
    payload = {"topic_name": topic, "partitions_count":1, "replication_factor":3}
    response = requests.post(topic_url, json=payload, headers={"Content-Type": "application/json"})
    if debug:
        print(response.status_code)
        print(json.dumps(response.json(), indent=2))
        if response.status_code == 201:
            print("Topic created")
        else:
            print("Topic already exists")


def upload_to_kafka(ip:str, topic:str, debug:bool = False):
    logs = json.load(open("logs.json", 'r'))
    payload = json.load(open("current_nfs.json", 'r'))
    payload["changes"] = logs
    if debug:
        print("Payload:")
        print(json.dumps(payload, indent=2))
    response = requests.post(f"http://{ip}:8082/topics/{topic}", json={"records":[{"value":payload, "partition":0}]}, headers={"Content-Type": "application/vnd.kafka.json.v2+json"})
    if debug:
        print(response.status_code)
        print(json.dumps(response.json(), indent=2))


def run(coreAPI:CoreV1Api):
    while True:
        print("--------------------SCAN BEGAN AT {}----------------------".format(datetime.now().isoformat()))

        # First, import settings, just in case they ever changed
        settings = generate_logs.import_settings("settings.json")
        ip = settings["kafka_config"]["api_ip"]
        topic = settings["kafka_config"]["topic"]
        debug = settings["debug"]
        create_topic_if_not_exists(ip, topic, debug)
        
        # Save previous network functions so they can be compared later 
        generate_logs.save_previous_nfs(debug=debug)
        
        # Get all the current namespaces
        results = coreAPI.list_namespace()
        current_namespaces = []
        for i in results.items:
            current_namespaces.append(i.metadata.name)
        
        # scan the namespaces to see which one are network functions
        generate_logs.scan_for_nfs(current_namespaces, settings["network_functions"], debug=debug)
        
        print("\n-------------------------------LOGS----------------------------------")
        
        # Generate logs based on the difference between last iteration and this one
        diff = generate_logs.diff(debug=True)

        # If there are changes, then upload the changes to the kafka topic
        if diff:
            print("\nuploading logs to kafka...")
            upload_to_kafka(ip, topic, debug=debug)
            print("successfully uploaded logs to kafka")

        print("\n------------------SCAN COMPLETE, WAITING {} MINUTES-------------------\n\n\n".format(settings["scan_interval_minutes"]))

        # Wait until next scan
        time.sleep(settings["scan_interval_minutes"]*60)



# MAIN
# Setup kubernetes client
config.load_incluster_config()
print("Config is loaded")
v1 = client.CoreV1Api()
print("Client is created")

# Load settings
settings = generate_logs.import_settings("settings.json")
ip = settings["kafka_config"]["api_ip"]
topic = settings["kafka_config"]["topic"]
debug = settings["debug"]
print("Settings loaded")

# Create a topic
create_topic_if_not_exists(ip, topic, debug)
print("Topic exists")

print("Beginning scanning...")
run(v1)
