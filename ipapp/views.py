from django.shortcuts import render
from .models import IPLog
from django.utils import timezone
import requests
import subprocess
import win32com.client
from win32com.client import Dispatch, gencache
import os

def scan_for_malicious_files(scan_directory):
    """Scan a directory for known malicious files."""
    # Define a list of known malicious file names (for demonstration)
    known_malicious_files = ['malware.exe', 'virus.bat', 'trojan.dll']
    found_files = []

    # Scan through the directory
    for root, dirs, files in os.walk(scan_directory):
        for file in files:
            if file in known_malicious_files:
                found_files.append(os.path.join(root, file))

    return found_files




def check_windows_security_status():
    try:
        wmi = Dispatch("WbemScripting.SWbemLocator").ConnectServer(".", "root\\SecurityCenter2")
        products = wmi.ExecQuery("Select * from AntiVirusProduct")
        for product in products:
            return product.productState
        return "Unknown"
    except Exception as e:
        return f"Error checking status: {str(e)}"


def check_firewall_status():
    try:
        # Run the command to check the Windows Firewall status
        command = "netsh advfirewall show allprofiles"
        result = subprocess.run(command, capture_output=True, text=True, shell=True)

        if result.returncode == 0:
            output = result.stdout
            if 'State ON' in output:
                return "Enabled"
            else:
                return "Disabled"
        else:
            return "Error checking firewall status"
    except Exception as e:
        return f"Error: {str(e)}"


def get_client_ip(request):
    """Retrieve the client IP address from the request object."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    if ip == '127.0.0.1':
        ip = get_public_ip() or '127.0.0.1' 
    return ip

def get_public_ip():
    """Fetch public IP using an external service."""
    try:
        response = requests.get('https://api.ipify.org?format=json')
        ip = response.json()['ip']
        return ip
    except requests.RequestException:
        return None

def log_ip(request):
    """Log the user's IP address and fetch geolocation data using IP-API."""
    ip_address = get_client_ip(request)
    
    # Log the IP in the database
    ip_log = IPLog.objects.create(ip_address=ip_address, timestamp=timezone.now())

    # Fetch location data using IP-API (no API key needed for free tier)
    response = requests.get(f'http://ip-api.com/json/{ip_address}')
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            location = f"{data['city']}, {data['regionName']}, {data['country']}"
            ip_log.location = location
            ip_log.save()

    # Check Windows Security Status
    windows_security_state = check_windows_security_status()
    if windows_security_state is None:
        windows_security_status = 'Not Found'
    elif windows_security_state in [397313, 397312]:
        windows_security_status = 'Enabled'
    else:
        windows_security_status = 'Disabled'

    # Scan for malicious files
    malicious_files_found = scan_for_malicious_files("C:\\")  # Scanning the entire C drive
    malicious_files_count = len(malicious_files_found)

    return render(request, 'ipapp/homepage.html', {
        'ip_log': ip_log,
        'firewall_status': 'Disabled',  # Placeholder; implement actual logic
        'windows_security_status': windows_security_status,
        'malicious_files_count': malicious_files_count,
    })

