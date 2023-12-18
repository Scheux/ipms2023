from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import subprocess
import datetime
import os
import shutil
import ipaddress
import platform

app = Flask(__name__)

# Load config location from settings.json file and set it as a variable
def load_settings():
    with open('settings.json', 'r') as file:
        data = json.load(file)
        # check if the file exists
        if os.path.isfile(data['serverconfig_file']):
            print('File exists')
            return data['serverconfig_file']
        else:
            print('File does not exist using Fallback')
            return data['default_config_file']
    

# Load servers and ports from config
def load_config():
    with open(load_settings(), 'r') as file:
        data = json.load(file)
    return data['servers'], data['available_ports']

# Function to ping a server

def ping_server(server):
    try:
        # Validate the IP address
        ip = ipaddress.ip_address(server['ip'])

        # Get the operating system
        os_name = platform.system()

        if ipaddress.ip_address(ip).is_loopback:
            return 'Online'

        # Execute the ping command based on the operating system
        if os_name == 'Windows':
            response = subprocess.run(['ping', '-n', '4', str(ip)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        else:
            response = subprocess.run(['ping', '-c', '4', str(ip)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check if the ping command was successful
        if response.returncode == 0:
            return 'Online'
        else:
            return 'Offline'
    except ValueError:
        # If the IP address is invalid
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
        selected_protocol = request.form.get('protocol')
        test_duration = request.form.get('duration', type=int)


        # Run iperf3 test
        try:
            if selected_protocol == 'udp':
                print('UDP got selected!')
                command = f'iperf3 -c {selected_server} -p {selected_port} -t {test_duration} --udp'
            else:
                print('TCP got selected!')
                command = f'iperf3 -c {selected_server} -p {selected_port} -t {test_duration}'
            test_result = subprocess.check_output(command, shell=True).decode('utf-8')
        except subprocess.CalledProcessError as e:
            test_result = e.output.decode('utf-8')

    for server in servers:
        server['status'] = 'Testing...'


    # check if test_result is None and if so, don't write to file also check if test_result is empty
    if test_result is None:
        print('Test result is None')
    elif test_result == '':
        print('No String in test result')
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

@app.route('/save_settings', methods=['POST'])
def save_settings():
    data = request.json
    servers_path = data.get('serversPath')

    # Default path to fall back to
    default_path = 'default_servers.json'

    # Update settings.json with the new servers_path
    try:
        # Check if the servers_path is provided and the file exists
        if servers_path and os.path.isfile(servers_path):
            new_path = servers_path
        else:
            new_path = default_path

        with open('settings.json', 'r') as file:
            settings = json.load(file)

        settings['serverconfig_file'] = new_path

        with open('settings.json', 'w') as file:
            json.dump(settings, file, indent=4)

        return jsonify({'status': 'Settings updated successfully', 'pathUsed': new_path})

    except Exception as e:
        return jsonify({'status': 'Error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
