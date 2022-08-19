from datetime import datetime
import json
import os
import requests
import subprocess
import time
from typing import List


def import_settings(settings_path:str):
    return json.load(open(settings_path, 'r'))


def get_current_nfs():
    results = subprocess.run(["kubectl", "get", "namespaces"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if results.stderr is None or results.stderr == "":
        current_nfs = []
        for line in results.stdout.split("\n"):
            # Discard empty strings
            if(line == ""):
                continue
            
            # Take just the name of each line, no need for status and age
            info = line.split()
            name = info[0]

            current_nfs.append(name)
        
        return current_nfs
    else:
        print(results.stderr)
        return None


def scan_for_nfs(namespaces:List[str], network_functions:List[str]):
    current_nfs = []
    for name in namespaces:
        applicable_nfs = []
        for nf in network_functions:
            # As long as the network function appears in the name,
            # take it to be that it is said network function
            if nf.casefold() in name.casefold():
                applicable_nfs.append(nf)
        if len(applicable_nfs) > 0:
            current_nfs.append({"kind":applicable_nfs, "namespace":name})

    out = {"timestamp":datetime.now().isoformat(), "network_functions":current_nfs}
    with open("current_nfs.json", 'w') as file:
        json.dump(out, file, indent=2)


def save_previous_nfs():
    try:
        results = subprocess.run(["cp", "current_nfs.json", "previous_nfs.json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if(results.stderr is not None and results.stderr != ""):
            print(results.stderr)
    except:
        pass


def diff():
    try:
        current_nfs = []
        temp = json.load(open("current_nfs.json", 'r'))
        for namespace in temp["network_functions"]:
            current_nfs.append(namespace["namespace"])
    except:
        # Can't find the file
        current_nfs = None
        current_nfs = []
    try:
        previous_nfs = []
        temp = json.load(open("previous_nfs.json", 'r'))
        for namespace in temp["network_functions"]:
            previous_nfs.append(namespace["namespace"])
    except:
        # Can't find the file
        previous_nfs = None
        previous_nfs = []
    
    logs = []
    # Compare current and previous namespaces
    added = set(current_nfs).difference(previous_nfs)
    removed = set(previous_nfs).difference(current_nfs)
    for i in added:
        logs.append(f"network function with namespace '{i}' was added")
    for i in removed:
        logs.append(f"network function with namespace '{i}' was removed")

    # Write the logs to a json file
    if len(logs) > 0:
        json.dump(logs, open("logs.json", 'w'), indent=2)
    
    # Remove the logs file if there are none
    else:
        if os.path.exists("logs.json"):
            os.remove("logs.json")


def upload_to_kafka(ip:str, topic:str):
    logs = json.load(open("logs.json", 'r'))
    payload = json.load(open("current_nfs.json", 'r'))
    payload["changes"] = logs
    print(json.dumps(payload, indent=2))
    response = requests.post(f"http://{ip}:8082/topics/{topic}", json={"records":[{"value":payload}]}, headers={"Content-Type": "application/vnd.kafka.json.v2+json"})
    return response


def run_local():
    while True:
        print("-----------------------------SCAN BEGAN AT {}------------------------------".format(datetime.now().isoformat()))
        settings = import_settings("settings.json")
        save_previous_nfs()

        print("\n-----------------------CURRENT NETWORK FUNCTIONS-----------------------")
        scan_for_nfs(get_current_nfs(), settings["network_functions"])
        with open("current_nfs.json", 'r') as file:
            print(file.read())

        print("\n-------------------------------LOGS----------------------------------")
        diff()
        try:
            with open("logs.json", 'r') as file:
                print(file.read())
                
            print("\nuploading logs to kafka...")
            upload_to_kafka(settings["kafka_config"]["api_ip"], settings["kafka_config"]["topic"])
            print("successfully uploaded logs to kafka")

        except FileNotFoundError:
            print("No changes since last update")

        print("\n------------------------------SCAN COMPLETE---------------------------\n\n\n")

        time.sleep(settings["scan_interval_minutes"]*60)



# MAIN
if __name__ == "__main__":
    run_local()
