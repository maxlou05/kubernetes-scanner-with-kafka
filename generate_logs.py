from datetime import datetime
import json
import os
import requests
import subprocess
import time
from typing import List


def import_settings(settings_path:str):
    with open(settings_path, 'r') as settings:
        return json.load(settings)


def get_current_namespaces():
    results = subprocess.run(["kubectl", "get", "namespaces"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if results.stderr is None or results.stderr == "":
        current_namespaces = []
        for line in results.stdout.split("\n"):
            # Discard empty strings
            if(line == ""):
                continue
            
            # Take just the name of each line, no need for status and age
            info = line.split()
            name = info[0]

            current_namespaces.append(name)
        
        return current_namespaces
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

    out = {"timestamp":datetime.now().isoformat(), "record":current_nfs}
    with open("current_namespaces.json", 'w') as file:
        json.dump(out, file, indent=2)


def save_previous_nfs():
    try:
        results = subprocess.run(["cp", "current_namespaces.json", "previous_namespaces.json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if(results.stderr is not None and results.stderr != ""):
            print(results.stderr)
    except:
        pass


def diff():
    try:
        current_namespaces = []
        with open("current_namespaces.json", 'r') as current:
            current_nfs = json.load(current)
            for namespace in current_nfs["record"]:
                current_namespaces.append(namespace["namespace"])
    except:
        # Can't find the file
        current_nfs = None
        current_namespaces = []
    try:
        previous_namespaces = []
        with open("previous_namespaces.json", 'r') as previous:
            previous_nfs = json.load(previous)
            for namespace in previous_nfs["record"]:
                previous_namespaces.append(namespace["namespace"])
    except:
        # Can't find the file
        previous_nfs = None
        previous_namespaces = []
    
    logs = []
    # Compare current and previous namespaces
    added = set(current_namespaces).difference(previous_namespaces)
    removed = set(previous_namespaces).difference(current_namespaces)
    for i in added:
        logs.append(f"network function with namespace '{i}' was added")
    for i in removed:
        logs.append(f"network function with namespace '{i}' was removed")

    # Write the logs to a json file
    if len(logs) > 0:
        out = {"timestamp":datetime.now().isoformat(), "logs":logs}
        with open("logs.json", 'w') as log_file:
            json.dump(out, log_file, indent=2)
    
    # Remove the logs file if there are none
    else:
        if os.path.exists("logs.json"):
            os.remove("logs.json")


def upload_to_kafka(logs:List[str]):
    requests.post("http://localhost:8082/topics/myLogs", json={"records":[{"value":logs}]}, headers={"Content-Type": "application/vnd.kafka.json.v2+json"})


def run_local():
    while True:
        print("-----------------------------SCAN BEGAN AT {}------------------------------".format(datetime.now().isoformat()))
        settings = import_settings("settings.json")
        save_previous_nfs()

        print("\n-----------------------CURRENT NETWORK FUNCTIONS-----------------------")
        scan_for_nfs(get_current_namespaces(), settings["network_functions"])
        with open("current_namespaces.json", 'r') as file:
            print(file.read())

        print("\n-------------------------------LOGS----------------------------------")
        diff()
        try:
            with open("logs.json", 'r') as file:
                print(file.read())
                print("\nuploading logs to kafka...")
                upload_to_kafka(json.load(file))
                print("successfully uploaded logs to kafka")

        except FileNotFoundError:
            print("No changes since last update")

        print("\n------------------------------SCAN COMPLETE---------------------------\n\n\n")

        time.sleep(settings["scan_interval_minutes"]*60)



# MAIN
if __name__ == "__main__":
    run_local()
