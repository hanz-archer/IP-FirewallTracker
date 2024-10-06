from django.shortcuts import render
from .models import IPLog
from django.utils import timezone
import requests
import subprocess

def check_firewall_status():
    try:
        # Run the command to check the Windows Firewall status
        command = "netsh advfirewall show allprofiles"
        result = subprocess.run(command, capture_output=True, text=True, shell=True)

        if result.returncode == 0:
            output = result.stdout
            # Check if the output contains 'State ON' to determine if the firewall is enabled
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

    # Check if IP is localhost and fetch public IP for testing (optional for dev environments)
    if ip == '127.0.0.1':
        ip = get_public_ip() or '127.0.0.1'  # Fallback to public IP for testing
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
            ip_log.latitude = data.get('lat')  # Add latitude if needed
            ip_log.longitude = data.get('lon')  # Add longitude if needed
            ip_log.timezone = data.get('timezone')  # Add timezone if needed
            ip_log.isp = data.get('isp')  # Add ISP if needed
            ip_log.save()

    # Check the firewall status
    firewall_status = check_firewall_status()

    # Render the template with IP log and firewall status
    return render(request, 'ipapp/homepage.html', {
        'ip_log': ip_log,
        'firewall_status': firewall_status  # Pass the firewall status to the template
    })
