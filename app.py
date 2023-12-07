from flask import Flask, render_template, request, jsonify
import json
import subprocess
from pythonping import ping
import threading
import datetime
import os
import shutil

app = Flask(__name__)

# Load servers and ports from config
def load_config():
    with open('config.json', 'r') as file:
        data = json.load(file)
    return data['servers'], data['available_ports']

# Function to ping a server
import subprocess
import ipaddress

def ping_server(server):
    try:
        # Validate the IP address
        ip = ipaddress.ip_address(server['ip'])

        # Execute the ping command
        response = subprocess.run(['ping', '-c', '1', '-t', '1', str(ip)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check if the ping command was successful
        if response.returncode == 0:
            return 'Online'
        else:
            return 'Offline'
    except ValueError:
        # If the IP address is invalid
        print(f"Invalid IP address: {server['ip']}")
        return "Error - Invalid IP"
    except Exception as e:
        # Other exceptions
        print(f"Error pinging {server['ip']}: {e}")
        return "Error"


@app.route('/', methods=['GET', 'POST'])
def home():
    servers, ports = load_config()
    test_result = None

    if request.method == 'POST':
        selected_server = request.form.get('server')
        selected_port = request.form.get('port')
        test_duration = request.form.get('duration', type=int)

        # Run iperf3 test
        try:
            command = f'iperf3 -c {selected_server} -p {selected_port} -t {test_duration}'
            test_result = subprocess.check_output(command, shell=True).decode('utf-8')
        except subprocess.CalledProcessError as e:
            test_result = e.output.decode('utf-8')

    for server in servers:
        server['status'] = 'Testing...'

   # write test_result to json file 
    if test_result == None:
        print('No test result')
    else:
        with open('result.txt', 'w') as file:
            file.write(test_result)
            print('Test result written to file')
        # rename result.json to current date and time
        now = datetime.datetime.now()
        now = now.strftime("%Y-%m-%d_%H-%M-%S")
        os.rename('result.txt', f'{now}.txt')

    
        # move result.json to results folder
        if not os.path.exists('results'):
            os.makedirs('results')
        shutil.move(f'{now}.txt', 'results')

    return render_template('app.html', servers=servers, ports=ports, test_result=test_result)

@app.route('/ping/<ip>')
def ping_route(ip):
    status = ping_server({'ip': ip})
    return jsonify(status=status)

if __name__ == '__main__':
    app.run(debug=True)
