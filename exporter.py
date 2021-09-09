import json
import os
import pdpyras
import socket
import subprocess
import time

from azure.storage.blob import BlobClient
from deepdiff import DeepDiff


def main():
    host = ''        # Symbolic name meaning all available interfaces
    exporter_port = int(os.getenv("EXPORTER_PORT", "12345"))
    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "10"))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, exporter_port))

    print("Host: ", host, "Port: ", exporter_port)
    temp_counter = 1
    while True:

        try:
            ps_script = "./test.ps1"
            host_config = ps_run(ps_script)
            if not host_config:
                break
            
            compare_config(host_config)
            # s.sendto(data, address)
            print("Success.")
            time.sleep(polling_interval_seconds)
            temp_counter += 1
            if temp_counter > 3:
                break

        except socket.error:
            print("Error Occured.")
            break


# Run powershell script
def ps_run(script_directory):
    proc = subprocess.Popen(["powershell.exe", script_directory], stdout=subprocess.PIPE)
    out = proc.communicate()[0]
    
    return out
    
def compare_config(host_config):
    conn_str = ""
    container_name = "config-test"
    blob_name = "standard_config_test.json"
    blob = BlobClient.from_connection_string(conn_str=conn_str, container_name=container_name, blob_name=blob_name)

    with open("./BlockDestination.json", "wb") as my_blob:
        blob_data = blob.download_blob()
        blob_data.readinto(my_blob)
        my_blob.close()

    with open("./BlockDestination.json", "r") as my_blob:
        my_blob = my_blob.read()
        my_blob = json.loads(my_blob)

    diff = DeepDiff(my_blob, host_config, ignore_order=False, verbose_level=1)
    # print(diff.pretty())
    with open("./diff.json", "w") as f:
        json.dump(diff.to_json(), f)
    
    # if not match alert pagerduty
    response = alert_pagerduty(diff)
    if response != 202:
        print("Unable to send alert to pagerduty. Response code: ", response)

def alert_pagerduty(diff):
    host_name = "snse-jbx0"
    routing_key = '0123456789abcdef0123456789abcdef'
    session = pdpyras.EventsAPISession(routing_key)
    summary = "Changes in Firewall rules detected on " + host_name
    # payload = diff.to_dict()
    dedup_key = session.trigger(summary, host_name, severity="warning")
    # try to see if trigger request was successful

if __name__ == "__main__":
    main()
