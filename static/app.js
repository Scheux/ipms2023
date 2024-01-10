function updateStatus(ip, elementId) {
    fetch('/ping/' + ip)
        .then(response => response.json())
        .then(data => {
            var statusElement = document.getElementById(elementId);
            statusElement.innerText = 'Status: ' + data.status;
            if (data.status === 'Online') {
                statusElement.className = 'status-online';
            } else {
                statusElement.className = 'status-offline';
            }
        })
        .catch(error => {
            var statusElement = document.getElementById(elementId);
            statusElement.innerText = 'Status: Error';
            statusElement.className = 'status-error';
        });
}

function updateDurationDisplay(value) {
    document.getElementById('durationValue').innerText = value;
}

function runSettingsProgram() {
    fetch('/run-settings-program', { method: 'POST' })
        .then(response => response.json())
        .catch(error => {
            console.error('Error running settings program:', error);
        });
}

function runTest() {
    console.log('Running test...');
    var statusTextElement = document.getElementById('status-text');
    statusTextElement.innerText = 'Running test...';

}