from flask import Flask, render_template, request, jsonify
import json, subprocess, datetime, os, shutil, ipaddress, platform

app = Flask(__name__)

# Load config location from settings.json file and set it as a variable
def load_settings():
    with open('settings.json', 'r') as file:
        data = json.load(file)
        # check if the file exists and check if file is json file
        if os.path.isfile(data['serverconfig_file']) and data['serverconfig_file'].endswith('.json'):
            print('File exists')
            return data['serverconfig_file']
        else:
            print('File does not exist using Fallback')
            return data['default_config_file']
    

# Load servers and ports from config
def load_config():
    with open(load_settings(), 'r', encoding='ISO-8859-1') as file:
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

def writeFile(test_result):
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
                command = f'iperf3-darwin -c {selected_server} -p {selected_port} -t {test_duration} --udp'
            else:
                print('TCP got selected!')
                command = f'iperf3-darwin -c {selected_server} -p {selected_port} -t {test_duration} '
            test_result = subprocess.check_output(command, shell=True).decode('utf-8')
        except subprocess.CalledProcessError as e:
            test_result = e.output.decode('utf-8')

    for server in servers:
        server['status'] = 'Testing...'

    writeFile(test_result)

    return render_template('app.html', servers=servers, ports=ports, test_result=test_result)

@app.route('/ping/<ip>')
def ping_route(ip):
    status = ping_server({'ip': ip})
    return jsonify(status=status)

@app.route('/run-settings-program', methods=['POST'])
def run_settings_program():
    # run settings_program.py here
    subprocess.run(['python', 'settings_program.py'])
    return jsonify({"message": "Settings program executed successfully"})

if __name__ == '__main__':
    app.run(debug=True)
