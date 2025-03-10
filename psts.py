#!/usr/bin/env python3
import http.server
import socketserver
import threading
import json
import subprocess
import re
import platform

PORT = 27315

def read_temperatures():
    """Detect OS and get temperatures from sensors (Linux) or sysctl (BSD)."""
    os_name = platform.system()
    if os_name == "Linux":
        try:
            output = subprocess.check_output(["sensors"], text=True)
        except Exception as e:
            return {"error": f"Failed to run sensors: {e}"}
        return parse_sensors_output(output)
    elif os_name in ["FreeBSD", "OpenBSD", "NetBSD"]:
        try:
            output = subprocess.check_output(["sysctl", "-a"], text=True)
        except Exception as e:
            return {"error": f"Failed to run sysctl: {e}"}
        return parse_sysctl_output(output)
    else:
        return {"error": f"Unsupported OS: {os_name}"}

def parse_sensors_output(output):
    """
    Parse the output of the `sensors` command.
    It groups temperature readings under sensor group names.
    """
    sensors_data = {}
    current_sensor = None
    # Regex to match temperature lines. It matches lines like:
    # "Core 0:        +46.0°C  (high = +80.0°C, crit = +100.0°C)"
    temp_regex = re.compile(r'^\s*([\w\s\.\-]+):\s+([+-]?\d+\.\d+)[°º]([CF])')
    
    # Process output line by line.
    for line in output.splitlines():
        line = line.strip()
        if not line:
            # Blank line: reset current sensor block
            current_sensor = None
            continue
        # If the line does not contain a colon, treat it as a sensor group header.
        if ":" not in line:
            current_sensor = line
            sensors_data[current_sensor] = {}
            continue
        # Skip lines that identify the adapter.
        if line.startswith("Adapter"):
            continue
        # If we haven't set a sensor group, try to guess one.
        if current_sensor is None:
            current_sensor = line.split()[0]
            sensors_data[current_sensor] = {}

        # Look for a temperature reading in the line.
        match = temp_regex.match(line)
        if match:
            label = match.group(1).strip()
            temperature = float(match.group(2))
            unit = match.group(3)
            sensors_data[current_sensor][label] = {"temperature": temperature, "unit": unit}
    return sensors_data

def parse_sysctl_output(output):
    """
    Parse the output of `sysctl -a` on BSD systems.
    It looks for lines like:
    "dev.cpu.0.temperature: 33.6C"
    """
    temps = {}
    temp_regex = re.compile(r'^dev\.cpu\.(\d+)\.temperature:\s+([\d\.]+)C')
    for line in output.splitlines():
        match = temp_regex.match(line)
        if match:
            cpu = match.group(1)
            temperature = float(match.group(2))
            temps[f"cpu{cpu}"] = {"temperature": temperature, "unit": "C"}
    return temps

class TempHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Print the client's IP address to the console
        print(f"Access from {self.client_address[0]}")
        # When a GET request is received, get temperatures and return as JSON.
        temps = read_temperatures()
        response = json.dumps(temps).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)
    
    # Override logging to reduce DOS-friendly verbosity.
    def log_message(self, format, *args):
        return

def run_server():
    # Using a threaded TCP server to spawn a new thread for each request.
    with socketserver.ThreadingTCPServer(("", PORT), TempHTTPRequestHandler) as httpd:
        print(f"Serving temperatures on port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    # Spawn the HTTP server in a separate daemon thread.
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # The main thread can perform other tasks or simply wait.
    try:
        while True:
            pass  # Replace with other tasks if necessary.
    except KeyboardInterrupt:
        print("\nShutting down.")
