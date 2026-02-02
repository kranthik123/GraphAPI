activationSchema.json:
======================

{
  "types": {
    "dynatrace.datasource.python:poly_trio-endpoint": {
      "type": "object",
      "displayName": "Poly Trio Endpoint",
      "summaryPattern": "Poly Trio {host}",
      "properties": {
        "host": {
          "displayName": "Host (IP or Hostname)",
          "type": "text",
          "nullable": false,
          "default": "",
          "constraints": [
            {
              "type": "LENGTH",
              "minLength": 1,
              "maxLength": 500
            }
          ],
          "maxItems": 1
        },
        "user": {
          "displayName": "User name",
          "type": "text",
          "nullable": false,
          "default": "admin",
          "constraints": [
            {
              "type": "LENGTH",
              "minLength": 1,
              "maxLength": 500
            }
          ],
          "maxItems": 1
        },
        "password": {
          "displayName": "Password",
          "type": "text",
          "nullable": false,
          "default": "",
          "constraints": [
            {
              "type": "LENGTH",
              "minLength": 1,
              "maxLength": 500
            }
          ],
          "maxItems": 1
        }
      }
    },
    "pythonRemote": {
      "type": "object",
      "properties": {
        "endpoints": {
          "displayName": "Poly Trio endpoint",
          "type": "list",
          "items": {
            "type": {
              "$ref": "#/types/dynatrace.datasource.python:poly_trio-endpoint"
            }
          },
          "nullable": false,
          "minItems": 1,
          "maxItems": 100,
          "metaData": {
            "addItemButton": "Add endpoint"
          }
        }
      }
    },
    "pythonLocal": {
      "type": "object",
      "properties": {
        "endpoints": {
          "displayName": "Poly Trio endpoint",
          "type": "list",
          "items": {
            "type": {
              "$ref": "#/types/dynatrace.datasource.python:poly_trio-endpoint"
            }
          },
          "nullable": false,
          "minItems": 1,
          "maxItems": 100,
          "metaData": {
            "addItemButton": "Add endpoint"
          }
        }
      }
    }
  },
  "dynatrace": "1",
  "description": "Poly Trio configuration",
  "schemaId": "python-extension.activation",
  "displayName": "Poly Trio configuration",
  "ownerProductManagement": "dynatrace",
  "ownerDevelopment": "dynatrace",
  "maturity": "GENERAL_AVAILABILITY",
  "allowedScopes": [
    "tenant"
  ],
  "multiObject": false,
  "properties": {
    "pythonLocal": {
      "displayName": "Python Local Extension",
      "type": {
        "$ref": "#/types/pythonLocal"
      }
    },
    "pythonRemote": {
      "displayName": "Python Remote Extension",
      "type": {
        "$ref": "#/types/pythonRemote"
      }
    }
  }
}


extension.yaml:
===============

# A descriptive name for your extension.
name: custom:cfs-poly-trio
# The version of the extension. It's good practice to increment this with changes.
version: 1.2.0
minDynatraceVersion: "1.285"
author:
  name: "Dynatrace"

python:
  runtime:
    # This must match the name of the folder containing your __main__.py
    module: poly_trio
    version:
      min: "3.10"

  activation:
    remote:
      path: activationSchema.json
    local:
      path: activationSchema.json

# Defines the custom device type that will be created in Dynatrace for each monitored endpoint.
topology:
  types:
    - key: custom:poly_trio_device
      displayName: Poly Trio Device
      properties:
        - key: endpoint
          displayName: Endpoint IP
          type: string
        - key: firmware_version
          displayName: Firmware Version
          type: string
        - key: poly_mac_address
          displayName: Poly MAC Address
          type: string
        - key: pairing_mode
          displayName: Pairing Mode
          type: string
        - key: provider_mode
          displayName: Provider Mode
          type: string
        - key: paired_device_mac
          displayName: Paired Device MAC
          type: string
      relations: []

# Defines all the metrics that this extension will report.
# Each key and dimension must exactly match what is sent by the Python script.
metrics:
  - key: poly_trio_device_up
    metadata:
      displayName: Poly Trio Device Up
      description: Indicates if the Poly Trio device is reachable (1 = Up, 0 = Down)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_cpu_usage
    metadata:
      displayName: Poly Trio CPU Usage
      description: CPU utilization of the Poly Trio device
      unit: Percent
    source:
      type: custom:poly_trio_device

  - key: poly_trio_memory_usage
    metadata:
      displayName: Poly Trio Memory Usage
      description: Memory utilization of the Poly Trio device
      unit: Percent
    source:
      type: custom:poly_trio_device

  - key: poly_trio_network_dhcp
    metadata:
      displayName: Poly Trio DHCP Status
      description: Indicates if DHCP is enabled (1 = Enabled, 0 = Disabled)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_wifi_connected
    metadata:
      displayName: Poly Trio WiFi Connected
      description: Indicates if WiFi is connected (1 = Connected, 0 = Disconnected)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_rx_packets
    metadata:
      displayName: Poly Trio RX Packets
      description: Number of received network packets
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_tx_packets
    metadata:
      displayName: Poly Trio TX Packets
      description: Number of transmitted network packets
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_uptime
    metadata:
      displayName: Poly Trio Uptime
      description: Device uptime in seconds
      unit: Second
    source:
      type: custom:poly_trio_device

  - key: poly_trio_device_status
    metadata:
      displayName: Poly Trio Device Status
      description: Current device status (0 = Idle, 1 = Active, 2 = Error)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_active_calls
    metadata:
      displayName: Poly Trio Active Calls
      description: Number of active calls on the device
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_total_call_logs
    metadata:
      displayName: Poly Trio Total Call Logs
      description: Total number of call logs
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_missed_calls
    metadata:
      displayName: Poly Trio Missed Calls
      description: Number of missed calls in call logs
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_microphone_muted
    metadata:
      displayName: Poly Trio Microphone Muted
      description: Indicates if microphone is muted (1 = Muted, 0 = Unmuted)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_audio_packet_loss
    metadata:
      displayName: Poly Trio Audio Packet Loss
      description: Audio packet loss percentage during active session
      unit: Percent
    source:
      type: custom:poly_trio_device

  # SIP/Protocol Metrics
  - key: poly_trio_sip_registered
    metadata:
      displayName: Poly Trio SIP Registration Status
      description: SIP registration status (1 = Registered, 0 = Not Registered)
      unit: Count
    source:
      type: custom:poly_trio_device

  # Configuration Metrics
  - key: poly_trio_provisioning_configured
    metadata:
      displayName: Poly Trio Provisioning Server Configured
      description: Indicates if provisioning server is configured (1 = Configured, 0 = Not Configured)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_qos_enabled
    metadata:
      displayName: Poly Trio QoS Enabled
      description: Quality of Service (QoS) enabled status (1 = Enabled, 0 = Disabled)
      unit: Count
    source:
      type: custom:poly_trio_device

  # Network Performance Metrics
  - key: poly_trio_link_status
    metadata:
      displayName: Poly Trio Link Status
      description: Ethernet link up/down status (1 = Up, 0 = Down)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_link_speed
    metadata:
      displayName: Poly Trio Link Speed
      description: Negotiated Ethernet link speed in Mbps
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_wifi_rssi
    metadata:
      displayName: Poly Trio WiFi Signal Strength
      description: WiFi signal strength (RSSI) in dBm
      unit: Count
    source:
      type: custom:poly_trio_device

  # Call Statistics - Detailed
  - key: poly_trio_received_calls
    metadata:
      displayName: Poly Trio Received Calls
      description: Number of received calls in call logs
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_placed_calls
    metadata:
      displayName: Poly Trio Placed Calls
      description: Number of placed calls in call logs
      unit: Count
    source:
      type: custom:poly_trio_device

  # VoIP Quality Metrics (RTP/SRTP)
  - key: poly_trio_jitter
    metadata:
      displayName: Poly Trio Jitter
      description: Inter-packet delay variation (jitter) in milliseconds
      unit: MilliSecond
    source:
      type: custom:poly_trio_device

  - key: poly_trio_latency
    metadata:
      displayName: Poly Trio Latency
      description: End-to-end audio latency in milliseconds
      unit: MilliSecond
    source:
      type: custom:poly_trio_device

  - key: poly_trio_mos_score
    metadata:
      displayName: Poly Trio MOS Score
      description: Mean Opinion Score for call quality (1.0-5.0, higher is better)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_r_factor
    metadata:
      displayName: Poly Trio R-Factor
      description: Quality rating factor (0-100, higher is better)
      unit: Count
    source:
      type: custom:poly_trio_device

  # RTP Stream Statistics
  - key: poly_trio_rtp_packets_sent
    metadata:
      displayName: Poly Trio RTP Packets Sent
      description: Total RTP packets transmitted
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_rtp_packets_received
    metadata:
      displayName: Poly Trio RTP Packets Received
      description: Total RTP packets received
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_audio_bitrate
    metadata:
      displayName: Poly Trio Audio Bitrate
      description: Current audio bitrate in kbps
      unit: KiloBitPerSecond
    source:
      type: custom:poly_trio_device

script.py:
==========
from typing import Optional, Any
from dynatrace_extension import Extension, Status, StatusValue
import requests
import json
import urllib3
from datetime import timedelta
from requests.auth import HTTPDigestAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)




class ExtensionImpl(Extension):
    # ============================================================================
    # LOGGING CONFIGURATION
    # ============================================================================
    # Adjust the logging level to control the verbosity of extension logs.
    # 
    # Available levels (from least to most verbose):
    #   - "ERROR"   : Only log errors and critical issues
    #   - "WARNING" : Log warnings and errors
    #   - "INFO"    : Log informational messages, warnings, and errors (DEFAULT)
    #   - "DEBUG"   : Log detailed debug information including API responses
    # 
    # Usage:
    #   - Set to "ERROR" or "WARNING" for production deployments
    #   - Set to "INFO" for normal monitoring with key status messages
    #   - Set to "DEBUG" for troubleshooting API issues or field mapping problems
    # 
    # Change the value below to adjust logging:
    LOG_LEVEL = "INFO"  # <-- Change this value to adjust logging verbosity
    # ============================================================================
    
    def initialize(self):
        """Initialize the extension and schedule the metrics collection to run every 5 minutes."""
        self.logger.info("Initializing poly-trio extension")
        self.schedule(self.poly_query, timedelta(minutes=1))
    
    def should_log(self, level):
        """Helper method to check if a message at the given level should be logged."""
        levels = {"ERROR": 0, "WARNING": 1, "INFO": 2, "DEBUG": 3}
        return levels.get(level, 2) <= levels.get(self.LOG_LEVEL, 2)

    def poly_query(self):
        """Scheduled to run every 5 minutes. Authenticates and fetches device status for each device, then reports metrics."""
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        self.logger.info(f"[{timestamp}] Poly query method started for poly-trio extension")
        devices = self.activation_config.get("endpoints", [])
        if not devices:
            self.logger.error("No devices configured for monitoring.")
            return

        for device in devices:
            try:
                device_host = device.get("host")
                if not device_host:
                    self.logger.error(f"Device missing host: {device}")
                    continue
                self.logger.info(f"Processing device: {device_host}")
            except Exception as e:
                self.logger.error(f"Error retrieving host for device {device}: {e}")
                continue

            try:
                device_username = device.get("user", "Polycom")
                device_password = device.get("password")
                if device_password is None:
                    self.logger.error(f"Password not found for device {device_host}")
                    continue
                self.logger.info(f"Got credentials for device {device_host}")
            except Exception as e:
                self.logger.error(f"Error retrieving credentials for device {device_host}: {e}")
                continue

            # Poly Trio uses Digest Auth, not session-based auth
            base_url = f"https://{device_host}"
            auth = HTTPDigestAuth(device_username, device_password)

            # Check if device is reachable by getting device info
            device_up = 0
            firmware_version = "Unknown"
            poly_mac_address = "Unknown"
            pairing_mode = "Unknown"  # "Hub" or "Device" 
            provider_mode = ""  # zoom, teams, otp, goto, genesys (only in Hub mode)
            paired_device_mac = ""  # MAC of paired device (when in Device mode)
            
            try:
                device_info_url = f"{base_url}/api/v2/mgmt/device/info"
                resp = requests.get(device_info_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                device_info = resp.json()
                device_up = 1
                device_data = device_info.get('data', {})
                self.logger.info(f"Device {device_host} is up. Model: {device_data.get('ModelNumber', 'Unknown')}")
                
                # ================================================================
                # Extract Firmware Version and Poly MAC Address
                # Based on actual API response from /api/v2/mgmt/device/info:
                # - Firmware: {"Application": "5.9.5.3153 29-Jan-21 09:12", "Updater": "5.9.5.3153", "BootBlock": "Unknown"}
                # - MACAddress: "48256719c936"
                # ================================================================
                fw_data = device_data.get('Firmware', {})
                if isinstance(fw_data, dict):
                    # Extract Application version: "5.9.5.3153 29-Jan-21 09:12" -> "5.9.5.3153"
                    app_version = fw_data.get('Application', '')
                    if app_version and ' ' in app_version:
                        firmware_version = app_version.split(' ')[0]
                    elif app_version:
                        firmware_version = app_version
                    else:
                        firmware_version = fw_data.get('Updater', 'Unknown')
                else:
                    firmware_version = str(fw_data) if fw_data else "Unknown"
                self.logger.info(f"Firmware version: {firmware_version} for {device_host}")
                
                # Poly MAC Address - field name is "MACAddress" (exact)
                # Format: "48256719c936" (12-char hex string without colons)
                mac_raw = device_data.get('MACAddress', '')
                if mac_raw and len(mac_raw) == 12 and ':' not in mac_raw:
                    poly_mac_address = ':'.join(mac_raw[i:i+2] for i in range(0, 12, 2)).upper()
                elif mac_raw:
                    poly_mac_address = str(mac_raw).upper()
                else:
                    poly_mac_address = "Unknown"
                self.logger.info(f"Poly MAC Address: {poly_mac_address} for {device_host}")
                
                # Note: device/info doesn't contain provider field based on actual API response
                # Provider info comes from systemInfo endpoint if available
                
                
                # Extract uptime from device info
                uptime_data = device_data.get('UpTime', {})
                if isinstance(uptime_data, dict):
                    try:
                        days = int(uptime_data.get('Days', 0))
                        hours = int(uptime_data.get('Hours', 0))
                        minutes = int(uptime_data.get('Minutes', 0))
                        seconds = int(uptime_data.get('Seconds', 0))
                        total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
                        self.report_metric("poly_trio_uptime", total_seconds, dimensions={
                            "endpoint": device_host,
                            "firmware_version": firmware_version,
                            "poly_mac_address": poly_mac_address
                        })
                        self.logger.info(f"Reported uptime: {total_seconds}s ({days}d {hours}h {minutes}m) for {device_host}")
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Unable to parse uptime: {e}")
            except Exception as e:
                self.logger.error(f"Error connecting to device {device_host}: {e}")
                self.report_metric("poly_trio_device_up", 0, dimensions={"endpoint": device_host})
                continue

            # ================================================================
            # Check Pairing Mode from V2 System Info
            # Note: /api/v2/mgmt/systemInfo endpoint returns 404 on most Poly Trio devices
            # When unavailable, default to "Standalone" mode
            # ================================================================
            try:
                system_info_url = f"{base_url}/api/v2/mgmt/systemInfo"
                resp = requests.get(system_info_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                system_info = resp.json()
                
                if self.should_log("DEBUG"):
                    self.logger.info(f"System Info Response: {json.dumps(system_info)}")
                
                sys_data = system_info.get("data", {})
                if isinstance(sys_data, dict):
                    # Check for provider field to determine Hub vs Device mode
                    provider_value = sys_data.get("provider", "")
                    if provider_value:
                        pairing_mode = "Hub"
                        provider_mode = str(provider_value).lower()
                        self.logger.info(f"Pairing Mode: Hub, Provider: {provider_mode} for {device_host}")
                    else:
                        pairing_mode = "Standalone"
                        self.logger.info(f"Pairing Mode: Standalone for {device_host}")
                                    
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    # systemInfo not available - device is in Standalone mode
                    pairing_mode = "Standalone"
                    self.logger.info(f"Pairing Mode: Standalone (systemInfo API not available) for {device_host}")
                else:
                    self.logger.warning(f"Error collecting System Info for {device_host}: {e}")
                    pairing_mode = "Standalone"
            except Exception as e:
                self.logger.warning(f"Error collecting System Info for {device_host}: {e}")
                pairing_mode = "Standalone"

            # Build common dimensions dict for all metrics
            common_dimensions = {
                "endpoint": device_host,
                "firmware_version": firmware_version,
                "poly_mac_address": poly_mac_address,
                "pairing_mode": pairing_mode
            }
            
            # Add provider_mode if in Hub mode (zoom, teams, otp, goto, genesys)
            if provider_mode:
                common_dimensions["provider_mode"] = provider_mode
            
            # Add paired_device_mac only if we have one (Device mode)
            if paired_device_mac:
                common_dimensions["paired_device_mac"] = paired_device_mac

            # Report device up status
            self.report_metric("poly_trio_device_up", device_up, dimensions=common_dimensions)

            # Get Device Stats (CPU and memory usage)
            # Actual API response: {"data": {"CPU": {"Current": "9.5", "Average": "9.7"}, 
            #                                "Memory": {"ComAS": "...", "SReclaim": "...", "Total": "2079477760"}}, ...}
            try:
                stats_url = f"{base_url}/api/v1/mgmt/device/stats"
                resp = requests.get(stats_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                stats_data = resp.json()
                if self.should_log("DEBUG"):
                    self.logger.info(f"Device Stats Response: {json.dumps(stats_data)}")
                
                data = stats_data.get("data", {})
                if isinstance(data, dict):
                    # CPU usage from CPU.Current field (string like "9.5")
                    cpu_data = data.get("CPU", {})
                    if isinstance(cpu_data, dict):
                        cpu_current = cpu_data.get("Current", "")
                        if cpu_current:
                            try:
                                cpu_usage = float(cpu_current)
                                self.report_metric("poly_trio_cpu_usage", cpu_usage, dimensions=common_dimensions)
                                self.logger.info(f"Reported CPU usage: {cpu_usage}% for {device_host}")
                            except (ValueError, TypeError):
                                self.logger.warning(f"Unable to parse CPU current: {cpu_current}")
                    
                    # Memory info - API provides Total, ComAS (committed), SReclaim (reclaimable)
                    # Since no explicit "Used" field, we'll report Total memory available
                    memory_data = data.get("Memory", {})
                    if isinstance(memory_data, dict):
                        memory_total = memory_data.get("Total", "")
                        memory_com_as = memory_data.get("ComAS", "")  # Committed_AS from /proc/meminfo
                        if memory_total and memory_com_as:
                            try:
                                total = float(memory_total)
                                committed = float(memory_com_as)
                                if total > 0:
                                    # Calculate usage as committed/total (approximate)
                                    memory_usage = (committed / total) * 100
                                    self.report_metric("poly_trio_memory_usage", memory_usage, dimensions=common_dimensions)
                                    self.logger.info(f"Reported Memory usage: {memory_usage:.2f}% for {device_host}")
                            except (ValueError, TypeError, ZeroDivisionError) as e:
                                self.logger.warning(f"Unable to calculate memory usage: {e}")
            except Exception as e:
                self.logger.error(f"Error collecting device stats for {device_host}: {e}")
            
            # Get Running Configuration for additional metrics
            try:
                config_url = f"{base_url}/api/v1/mgmt/device/runningConfig"
                resp = requests.get(config_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                config_data = resp.json()
                if self.should_log("DEBUG"):
                    self.logger.info(f"Running Config Response (truncated): {str(config_data)[:500]}...")
                
                # Extract configuration metrics
                if isinstance(config_data, dict):
                    data = config_data.get("data", {})
                    if isinstance(data, dict):
                        # Provisioning server configured - check Provisioning.Server field
                        prov_config = data.get("Provisioning", {})
                        if isinstance(prov_config, dict):
                            prov_server = prov_config.get("Server")
                            if prov_server is not None and prov_server != "":
                                self.report_metric("poly_trio_provisioning_configured", 1, dimensions=common_dimensions)
                                self.logger.info(f"Provisioning server configured for {device_host}")
                            else:
                                self.report_metric("poly_trio_provisioning_configured", 0, dimensions=common_dimensions)
                        
                        # DHCP feature status from running config
                        dhcp_config = data.get("DHCP", {})
                        if isinstance(dhcp_config, dict):
                            dhcp_feature = dhcp_config.get("Feature")
                            if dhcp_feature:
                                dhcp_enabled = 1 if str(dhcp_feature).lower() == "enabled" else 0
                                self.report_metric("poly_trio_qos_enabled", dhcp_enabled, dimensions=common_dimensions)
                                self.logger.info(f"DHCP feature status: {dhcp_feature} for {device_host}")
            except Exception as e:
                self.logger.error(f"Error collecting running config for {device_host}: {e}")

            # Get Network Info
            try:
                network_url = f"{base_url}/api/v1/mgmt/network/info"
                resp = requests.get(network_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                network_data = resp.json()
                if self.should_log("DEBUG"):
                    self.logger.info(f"Network Info Response: {json.dumps(network_data)}")
                
                # Extract comprehensive network status
                if isinstance(network_data, dict):
                    data = network_data.get("data", {})
                    if isinstance(data, dict):
                        # DHCP status - from DHCP field ("enabled" or "disabled")
                        dhcp_status_str = data.get("DHCP")
                        if dhcp_status_str is not None:
                            dhcp_status = 1 if str(dhcp_status_str).lower() == "enabled" else 0
                            self.report_metric("poly_trio_network_dhcp", dhcp_status, dimensions=common_dimensions)
                            self.logger.info(f"DHCP status: {dhcp_status_str} for {device_host}")
                        
                        # Link status - from LANPortStatus field
                        lan_port_status = data.get("LANPortStatus")
                        if lan_port_status is not None:
                            link_up = 1 if str(lan_port_status).lower() == "active" else 0
                            self.report_metric("poly_trio_link_status", link_up, dimensions=common_dimensions)
                            self.logger.info(f"Link status: {lan_port_status} for {device_host}")
                        
                        # Link speed - extract from LANSpeed field
                        lan_speed = data.get("LANSpeed")
                        if lan_speed:
                            try:
                                # LANSpeed comes as "100MB" or "1000MB", extract number
                                speed_str = str(lan_speed).replace("MB", "").replace("Mbps", "").strip()
                                speed_value = int(speed_str)
                                self.report_metric("poly_trio_link_speed", speed_value, dimensions=common_dimensions)
                                self.logger.info(f"Link speed: {speed_value} Mbps for {device_host}")
                            except (ValueError, TypeError):
                                self.logger.warning(f"Unable to parse link speed: {lan_speed}")

            except Exception as e:
                self.logger.error(f"Error collecting network info for {device_host}: {e}")

            # Get Network Statistics
            # Actual API response: {"data": {"UpTime": "0 day 2:00:48", "RxPackets": "88938", "TxPackets": "5547"}, "Status": "2000"}
            try:
                net_stats_url = f"{base_url}/api/v1/mgmt/network/stats"
                resp = requests.get(net_stats_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                net_stats_data = resp.json()
                
                data = net_stats_data.get("data", {})
                rx_packets = data.get("RxPackets", "")
                tx_packets = data.get("TxPackets", "")
                
                if rx_packets:
                    try:
                        rx_count = int(rx_packets)
                        self.report_metric("poly_trio_rx_packets", rx_count, dimensions=common_dimensions)
                    except (ValueError, TypeError):
                        self.logger.warning(f"Unable to parse RxPackets: {rx_packets}")
                
                if tx_packets:
                    try:
                        tx_count = int(tx_packets)
                        self.report_metric("poly_trio_tx_packets", tx_count, dimensions=common_dimensions)
                    except (ValueError, TypeError):
                        self.logger.warning(f"Unable to parse TxPackets: {tx_packets}")
            except Exception as e:
                self.logger.error(f"Error collecting network stats for {device_host}: {e}")

            # Poll for device status (Idle/Active/Error)
            # Actual API response: {"data": {"State": "Idle"}, "Status": "2000"}
            try:
                poll_url = f"{base_url}/api/v1/mgmt/pollForStatus"
                resp = requests.get(poll_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                poll_data = resp.json()
                
                # Extract State field from data
                data = poll_data.get("data", {})
                device_state = data.get("State", "Unknown")
                
                # Map state to numeric values
                status_map = {
                    "Idle": 0,
                    "Active": 1,
                    "InCall": 1,
                    "Ringing": 1,
                    "Error": 2
                }
                status_value = status_map.get(device_state, -1)
                
                if status_value >= 0:
                    self.report_metric("poly_trio_device_status", status_value, dimensions=common_dimensions)
                    self.logger.info(f"Device state: {device_state} (value: {status_value}) for {device_host}")
                else:
                    self.logger.warning(f"Unknown device state: {device_state} for {device_host}")
            except Exception as e:
                self.logger.error(f"Error polling device status for {device_host}: {e}")

            # Get Call Status (v2)
            # Actual API response: {"data": [...], "Status": "2000"} - empty array when no active calls
            try:
                call_status_url = f"{base_url}/api/v2/webCallControl/callStatus"
                resp = requests.get(call_status_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                call_data = resp.json()
                
                # Count active calls
                active_calls = 0
                if isinstance(call_data, dict) and "data" in call_data:
                    calls = call_data.get("data", [])
                    if isinstance(calls, list):
                        active_calls = len(calls)
                
                self.report_metric("poly_trio_active_calls", active_calls, dimensions=common_dimensions)
                self.logger.info(f"Active calls: {active_calls} for {device_host}")
            except Exception as e:
                self.logger.error(f"Error collecting call status for {device_host}: {e}")

            # Get Call Logs - All
            # Actual API response: {"data": {"Missed": [], "Received": [], "Placed": []}, "Status": "2000"}
            try:
                call_logs_url = f"{base_url}/api/v1/mgmt/callLogs"
                resp = requests.get(call_logs_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                call_logs_data = resp.json()
                
                # Count total call logs from all categories
                total_logs = 0
                if isinstance(call_logs_data, dict) and "data" in call_logs_data:
                    logs_data = call_logs_data.get("data", {})
                    if isinstance(logs_data, dict):
                        # Response format: {"Missed": [], "Received": [], "Placed": []}
                        missed = logs_data.get("Missed", [])
                        received = logs_data.get("Received", [])
                        placed = logs_data.get("Placed", [])
                        total_logs = len(missed) + len(received) + len(placed)
                
                self.report_metric("poly_trio_total_call_logs", total_logs, dimensions=common_dimensions)
            except Exception as e:
                self.logger.error(f"Error collecting call logs for {device_host}: {e}")

            # Get Call Logs - Missed
            try:
                missed_logs_url = f"{base_url}/api/v1/mgmt/callLogs/missed"
                resp = requests.get(missed_logs_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                missed_logs_data = resp.json()
                
                # Count missed call logs
                missed_logs = 0
                if isinstance(missed_logs_data, dict) and "data" in missed_logs_data:
                    logs = missed_logs_data.get("data", [])
                    if isinstance(logs, list):
                        missed_logs = len(logs)
                
                self.report_metric("poly_trio_missed_calls", missed_logs, dimensions=common_dimensions)
            except Exception as e:
                self.logger.error(f"Error collecting missed call logs for {device_host}: {e}")
            
            # Get Call Logs - Received
            try:
                received_logs_url = f"{base_url}/api/v1/mgmt/callLogs/received"
                resp = requests.get(received_logs_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                received_logs_data = resp.json()
                
                # Count received call logs
                received_logs = 0
                if isinstance(received_logs_data, dict) and "data" in received_logs_data:
                    logs = received_logs_data.get("data", [])
                    if isinstance(logs, list):
                        received_logs = len(logs)
                
                self.report_metric("poly_trio_received_calls", received_logs, dimensions=common_dimensions)
            except Exception as e:
                self.logger.error(f"Error collecting received call logs for {device_host}: {e}")
            
            # Get Call Logs - Placed
            try:
                placed_logs_url = f"{base_url}/api/v1/mgmt/callLogs/placed"
                resp = requests.get(placed_logs_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                placed_logs_data = resp.json()
                
                # Count placed call logs
                placed_logs = 0
                if isinstance(placed_logs_data, dict) and "data" in placed_logs_data:
                    logs = placed_logs_data.get("data", [])
                    if isinstance(logs, list):
                        placed_logs = len(logs)
                
                self.report_metric("poly_trio_placed_calls", placed_logs, dimensions=common_dimensions)
            except Exception as e:
                self.logger.error(f"Error collecting placed call logs for {device_host}: {e}")

            # Get Communication Info (mute states)
            # Actual API response: {"data": {"PhoneMuteState": "False", "CommunicationType": ["None"], "FarEndMuteState": []}, "Status": "2000"}
            try:
                comm_info_url = f"{base_url}/api/v1/mgmt/media/communicationInfo"
                resp = requests.get(comm_info_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                comm_data = resp.json()
                
                # Extract mute state from PhoneMuteState field ("True" or "False" string)
                data = comm_data.get("data", {})
                phone_mute_state = data.get("PhoneMuteState", "")
                if phone_mute_state:
                    mute_status = 1 if phone_mute_state.lower() == "true" else 0
                    self.report_metric("poly_trio_microphone_muted", mute_status, dimensions=common_dimensions)
            except Exception as e:
                self.logger.error(f"Error collecting communication info for {device_host}: {e}")

            # Get Line Info for SIP Registration Status
            # Actual API response: {"data": [{"Label": "Trio C60", "RegistrationStatus": "Unregistered", ...}], "Status": "2000"}
            try:
                line_info_url = f"{base_url}/api/v2/mgmt/lineInfo"
                resp = requests.get(line_info_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                line_info_data = resp.json()
                
                data = line_info_data.get("data", [])
                if isinstance(data, list) and len(data) > 0:
                    # Check the first line's registration status
                    first_line = data[0] if isinstance(data[0], dict) else {}
                    reg_status = first_line.get("RegistrationStatus", "")
                    sip_registered = 1 if reg_status.lower() == "registered" else 0
                    self.report_metric("poly_trio_sip_registered", sip_registered, dimensions=common_dimensions)
                    self.logger.info(f"SIP Registration Status: {reg_status} for {device_host}")
            except Exception as e:
                self.logger.error(f"Error collecting line info for {device_host}: {e}")

            # Get Session Stats (audio/video quality metrics)
            try:
                session_stats_url = f"{base_url}/api/v1/mgmt/media/sessionStats"
                resp = requests.get(session_stats_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                session_data = resp.json()
                
                if self.should_log("DEBUG"):
                    self.logger.info(f"Session Stats Response: {json.dumps(session_data)}")
                
                # Extract comprehensive audio/video quality metrics
                if isinstance(session_data, dict):
                    # Standard dict response
                    if "data" in session_data:
                        stats = session_data.get("data", {})
                        if isinstance(stats, dict):
                            # VoIP Quality Metrics
                            audio_packet_loss = stats.get("AudioPacketLoss")
                            jitter = stats.get("Jitter")
                            latency = stats.get("Latency")
                            mos_score = stats.get("MOS") or stats.get("MOScore")
                            r_factor = stats.get("RFactor")
                            
                            # Audio Stream Statistics
                            rtp_packets_sent = stats.get("RTPPacketsSent")
                            rtp_packets_received = stats.get("RTPPacketsReceived")
                            audio_codec = stats.get("AudioCodec")
                            audio_bitrate = stats.get("AudioBitrate")
                            
                            # Report metrics
                            if audio_packet_loss is not None:
                                self.report_metric("poly_trio_audio_packet_loss", audio_packet_loss, dimensions=common_dimensions)
                            
                            if jitter is not None:
                                try:
                                    jitter_value = float(jitter)
                                    self.report_metric("poly_trio_jitter", jitter_value, dimensions=common_dimensions)
                                except (ValueError, TypeError):
                                    self.logger.warning(f"Unable to parse jitter: {jitter}")
                            
                            if latency is not None:
                                try:
                                    latency_value = float(latency)
                                    self.report_metric("poly_trio_latency", latency_value, dimensions=common_dimensions)
                                except (ValueError, TypeError):
                                    self.logger.warning(f"Unable to parse latency: {latency}")
                            
                            if mos_score is not None:
                                try:
                                    mos_value = float(mos_score)
                                    self.report_metric("poly_trio_mos_score", mos_value, dimensions=common_dimensions)
                                except (ValueError, TypeError):
                                    self.logger.warning(f"Unable to parse MOS score: {mos_score}")
                            
                            if r_factor is not None:
                                try:
                                    r_value = float(r_factor)
                                    self.report_metric("poly_trio_r_factor", r_value, dimensions=common_dimensions)
                                except (ValueError, TypeError):
                                    self.logger.warning(f"Unable to parse R-Factor: {r_factor}")
                            
                            if rtp_packets_sent is not None:
                                self.report_metric("poly_trio_rtp_packets_sent", rtp_packets_sent, dimensions=common_dimensions)
                            
                            if rtp_packets_received is not None:
                                self.report_metric("poly_trio_rtp_packets_received", rtp_packets_received, dimensions=common_dimensions)
                            
                            if audio_bitrate is not None:
                                try:
                                    bitrate_value = float(audio_bitrate)
                                    self.report_metric("poly_trio_audio_bitrate", bitrate_value, dimensions=common_dimensions)
                                except (ValueError, TypeError):
                                    self.logger.warning(f"Unable to parse audio bitrate: {audio_bitrate}")
                            
                elif isinstance(session_data, list):
                    # List response (handle it if needed or just log it)
                    self.logger.info(f"Session data is a list with {len(session_data)} items")
                    for item in session_data:
                        if isinstance(item, dict):
                            packet_loss = item.get("AudioPacketLoss")
                            if packet_loss is not None:
                                self.report_metric("poly_trio_audio_packet_loss", packet_loss, dimensions=common_dimensions)
                                break
            except Exception as e:
                self.logger.error(f"Error collecting session stats for {device_host}: {e}")

        from datetime import datetime
        timestamp = datetime.now().isoformat()
        self.logger.info(f"[{timestamp}] Poly query method ended for poly-trio extension")

    def fastcheck(self) -> Status:
        """Health check for the extension."""
        return Status(StatusValue.OK)


def main():
    ExtensionImpl().run()


if __name__ == "__main__":
    main()

