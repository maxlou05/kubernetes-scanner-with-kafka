from datetime import datetime
import json
import os
import subprocess
from typing import List


def import_settings(settings_path:str):
    return json.load(open(settings_path, 'r'))


def get_current_nfs(debug:bool = False):
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
    elif debug:
        print(results.stderr)
        return None


def scan_for_nfs(namespaces:List[str], network_functions:List[str], debug:bool = False):
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
    json.dump(out, open("current_nfs.json", 'w'), indent=2)
    if debug:
        print(json.dumps(out, indent=2))


def save_previous_nfs(debug:bool = False):
    try:
        results = subprocess.run(["cp", "current_nfs.json", "previous_nfs.json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if(results.stderr is not None and results.stderr != "" and debug):
            print(results.stderr)
    except:
        # If there's nothing to copy, that's ok
        pass


def diff(debug:bool = False):
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
        if debug:
            print(json.dumps(logs, indent=2))
        return True
    
    # Remove the logs file if there are none
    else:
        if os.path.exists("logs.json"):
            os.remove("logs.json")
        if debug:
            print("No changes since last update")
        return False
