from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
import json, subprocess, datetime, os, shutil, ipaddress, platform

def get_remote_address():
    return request.remote_addr

app = Flask(__name__)
limiter = Limiter(app=app, key_func=get_remote_address)

def validate_file_path(file_path):
    # Check if the file exists
    if not os.path.exists(file_path):
        raise ValueError("File does not exist")

    # Check if the path is a file
    if not os.path.isfile(file_path):
        raise ValueError("Path is not a file")

    # Check if the file is readable
    if not os.access(file_path, os.R_OK):
        raise ValueError("File is not readable")

    return True


# Load config location from settings.json file and set it as a variable
def load_settings():

 with open('settings.json', 'r') as file:
        data = json.load(file)
        config_file = data['serverconfig_file']
        default_config_file = data['default_config_file']

        # Validate the config file path
        try:
            validate_file_path(config_file)
            print('File exists')
            return config_file
        except ValueError:
            print('File does not exist or is not valid, using fallback')
            validate_file_path(default_config_file)
            return default_config_file
    

# Load servers and ports from config
def load_config():
    config_file_path = load_settings()
    try:
        validate_file_path(config_file_path)
    except ValueError as e:
        print(f"Invalid config file: {e}")
        return None, None

    with open(config_file_path, 'r', encoding='ISO-8859-1') as file:
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
    test_Result = ""
    local_ip = None
    local_port = None
    host_ip = None
    host_port = None
    end_Result = ""

    

    if request.method == 'POST':
        selected_server = request.form.get('server')
        selected_port = request.form.get('port')
        selected_protocol = request.form.get('protocol')
        test_duration = request.form.get('duration', type=int)

        # Run iperf3 test
        try:
            if not str(selected_port).isdigit() or not 1 <= int(selected_port) <= 65535:
                raise ValueError("Invalid port")

            # Validate the test duration
            if not str(test_duration).isdigit() or not 1 <= int(test_duration) <= 3600:  # Limit to 1 hour for example
                raise ValueError("Invalid test duration")

            if selected_protocol == 'udp':
                print('UDP got selected!')
                command = ['iperf3-darwin', '-c', str(selected_server), '-p', str(selected_port), '-t', str(test_duration), '--udp', '--json']
            else:
                print('TCP got selected!')
                command = ['iperf3-darwin', '-c', str(selected_server), '-p', str(selected_port), '-t', str(test_duration), '--json']
            test_Result = subprocess.check_output(command).decode('utf-8')
        except subprocess.CalledProcessError as e:
            test_Result = e.output.decode('utf-8')

    for server in servers:
        server['status'] = 'Testing...'


    if test_Result:
        try:
            resultJSON = json.loads(test_Result)

            local_ip = resultJSON['start']['connected'][0]['local_host']
            host_ip = resultJSON['start']['connected'][0]['remote_host']
            local_port = resultJSON['start']['connected'][0]['local_port']
            host_port = resultJSON['start']['connected'][0]['remote_port']

            # Initialize end_Result with connection information and headers
            end_Result = "Connecting to host {}, port {}\n".format(host_ip, host_port)
            end_Result += "[  4] local {} port {} connected to {} port {}\n\n".format(local_ip, local_port, host_ip, host_port)

            # Adding headers
            end_Result += "{:<8} {:<30} {:<40} {:<15}\n".format("[ ID]", "Interval", "Transfer", "Bandwidth")
            end_Result += "-" * 95 + "\n"  # Adjust the number of dashes according to your header width

            # Adding data for each interval
            for interval in resultJSON['intervals']:
                start = interval['streams'][0]['start']
                end = interval['streams'][0]['end']
                transfer = interval['sum']['bytes'] / 1000000  # Convert to MBytes and round to 0 decimals
                transfer = "{:.0f}".format(transfer)
                bandwidth = interval['sum']['bits_per_second'] / 1000000000  # Convert to Gbits/sec
                bandwidth = "{:.2f}".format(bandwidth)
                end_Result += "[  4] {:5.2f}-{:<5.2f} sec {:>18} MBytes {:>28} Gbits/sec\n".format(start, end, transfer, bandwidth)

            end_Result += "-" * 95 + "\n"  # Separator

            # Assuming sender and receiver total data is available in resultJSON
            sender_total_mbytes = resultJSON['end']['sum_sent']['bytes'] / 1000000
            sender_total_mbytes = "{:.0f}".format(sender_total_mbytes)
            sender_total_bandwidth_gbits = resultJSON['end']['sum_sent']['bits_per_second'] / 1000000000
            sender_total_bandwidth_gbits = "{:.2f}".format(sender_total_bandwidth_gbits)
            receiver_total_mbytes = resultJSON['end']['sum_received']['bytes'] / 1000000
            receiver_total_mbytes = "{:.0f}".format(receiver_total_mbytes)
            receiver_total_bandwidth_gbits = resultJSON['end']['sum_received']['bits_per_second'] / 1000000000
            receiver_total_bandwidth_gbits = "{:.2f}".format(receiver_total_bandwidth_gbits)

            # Adding summary rows
            end_Result += "{:<8} {:<30} {:<40} {:<15}\n".format("[ ID]", "Interval", "Transfer", "Bandwidth")
            end_Result += "[  4]   0.00- 3.00 sec   {:>14} MBytes   {:>27} Gbits/sec             sender\n".format(sender_total_mbytes, sender_total_bandwidth_gbits)
            end_Result += "[  4]   0.00- 3.00 sec   {:>14} MBytes   {:>27} Gbits/sec             receiver\n".format(receiver_total_mbytes, receiver_total_bandwidth_gbits)

            # Now end_Result contains the whole output
        except json.JSONDecodeError:
            print("Error: test_Result is not a valid JSON string.")

        # Write test result to file
        writeFile(test_Result)

        return render_template('app.html', servers=servers, ports=ports, test_result=end_Result)

    return render_template("app.html", servers=servers, ports=ports)

@app.route('/ping/<ip>')
@limiter.limit("5/minute")
def ping_route(ip):
    status = ping_server({'ip': ip})
    return jsonify(status=status)

@app.route('/run-settings-program', methods=['POST'])
def run_settings_program():
    # run settings_program.py here
    subprocess.run(['python3', 'settings_program.py'])
    return jsonify({"message": "Settings program executed successfully"})

if __name__ == '__main__':
    app.run(debug=True)
