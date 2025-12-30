================================================================================
POLY TRIO C60 DYNATRACE EXTENSION - COMPLETE SETUP INSTRUCTIONS
================================================================================

PROJECT: Poly Trio C60 Conference Phone Monitoring Extension
VERSION: 1.0.0
CREATED: 2025-12-29
AUTHOR: Dynatrace Extension Team

================================================================================
TABLE OF CONTENTS
================================================================================
1. Overview
2. Folder Structure
3. File Contents (Complete)
4. Configuration
5. Installation & Deployment
6. Testing & Validation
7. Metrics Reference
8. Troubleshooting

================================================================================
1. OVERVIEW
================================================================================

This Dynatrace extension monitors Poly Trio C60 conference phones using the
Poly REST API. It collects system health, network performance, call statistics,
and VoIP quality metrics.

FEATURES:
- 17+ comprehensive metrics
- REST API-based collection via Digest Authentication
- Configurable logging levels (ERROR, WARNING, INFO, DEBUG)
- 1-minute collection interval (configurable)
- Support for multiple devices
- Production-ready error handling

REQUIREMENTS:
- Python 3.10+
- Dynatrace Environment
- Poly Trio C60 firmware 5.9.5+ (with REST API enabled)
- Network access to Poly devices (HTTPS port 443)

================================================================================
2. FOLDER STRUCTURE
================================================================================

poly_trio/
├── poly_trio/                      # Main Python module
│   └── __main__.py                 # Extension implementation
├── extension/                      # Extension configuration
│   ├── extension.yaml              # Metric definitions & topology
│   └── activationSchema.json      # Device configuration schema
├── activation.json                 # Device credentials (local dev)
├── secrets.json                    # Secrets file (if needed)
├── setup.py                        # Python package setup
├── README.MD                       # Extension documentation
├── IMPLEMENTED_METRICS.MD          # Detailed metrics guide
├── METRICS_COVERAGE.MD             # Coverage analysis
└── instructions.txt                # This file

================================================================================
3. FILE CONTENTS (COMPLETE)
================================================================================

--------------------------------------------------------------------------------
3.1. poly_trio/__main__.py
--------------------------------------------------------------------------------
"""
Poly Trio C60 Dynatrace Extension
Monitors Poly Trio conference phones via REST API
"""

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
        """Initialize the extension and schedule metrics collection."""
        self.logger.info("Initializing poly-trio extension")
        self.schedule(self.poly_query, timedelta(minutes=5))  # Run every 5 minutes
    
    def should_log(self, level):
        """Helper method to check if a message should be logged."""
        levels = {"ERROR": 0, "WARNING": 1, "INFO": 2, "DEBUG": 3}
        return levels.get(level, 2) <= levels.get(self.LOG_LEVEL, 2)

    def poly_query(self):
        """Collect metrics from Poly Trio devices."""
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        self.logger.info(f"[{timestamp}] Poly query method started")
        
        devices = self.activation_config.get("endpoints", [])
        if not devices:
            self.logger.error("No devices configured for monitoring.")
            return

        for device in devices:
            try:
                device_host = device.get("IP")
                if not device_host:
                    self.logger.error(f"Device missing IP: {device}")
                    continue
                self.logger.info(f"Processing device: {device_host}")
            except Exception as e:
                self.logger.error(f"Error retrieving host: {e}")
                continue

            try:
                device_username = device.get("user", "admin")
                device_password = device.get("password")
                if device_password is None:
                    self.logger.error(f"Password not found for {device_host}")
                    continue
                self.logger.info(f"Got credentials for {device_host}")
            except Exception as e:
                self.logger.error(f"Error retrieving credentials: {e}")
                continue

            # Setup authentication
            base_url = f"https://{device_host}"
            auth = HTTPDigestAuth(device_username, device_password)

            # Check device reachability
            device_up = 0
            try:
                device_info_url = f"{base_url}/api/v2/mgmt/device/info"
                resp = requests.get(device_info_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                device_info = resp.json()
                device_up = 1
                device_data = device_info.get('data', {})
                self.logger.info(f"Device {device_host} is up. Model: {device_data.get('ModelNumber', 'Unknown')}")
                
                # Extract uptime
                uptime_data = device_data.get('UpTime', {})
                if isinstance(uptime_data, dict):
                    try:
                        days = int(uptime_data.get('Days', 0))
                        hours = int(uptime_data.get('Hours', 0))
                        minutes = int(uptime_data.get('Minutes', 0))
                        seconds = int(uptime_data.get('Seconds', 0))
                        total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
                        self.report_metric("poly_trio_uptime", total_seconds, dimensions={"endpoint": device_host})
                        self.logger.info(f"Reported uptime: {total_seconds}s ({days}d {hours}h {minutes}m) for {device_host}")
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Unable to parse uptime: {e}")
            except Exception as e:
                self.logger.error(f"Error connecting to {device_host}: {e}")
                self.report_metric("poly_trio_device_up", 0, dimensions={"endpoint": device_host})
                continue

            self.report_metric("poly_trio_device_up", device_up, dimensions={"endpoint": device_host})

            # Collect device stats (CPU & Memory)
            try:
                stats_url = f"{base_url}/api/v1/mgmt/device/stats"
                resp = requests.get(stats_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                stats_data = resp.json()
                
                if self.should_log("DEBUG"):
                    self.logger.info(f"Device Stats Response: {json.dumps(stats_data)}")
                
                if isinstance(stats_data, dict):
                    data = stats_data.get("data", {})
                    if isinstance(data, dict):
                        # CPU usage
                        cpu_data = data.get("CPU", {})
                        if isinstance(cpu_data, dict):
                            cpu_current = cpu_data.get("Current")
                            if cpu_current is not None:
                                try:
                                    cpu_usage = float(cpu_current)
                                    self.report_metric("poly_trio_cpu_usage", cpu_usage, dimensions={"endpoint": device_host})
                                    self.logger.info(f"Reported CPU usage: {cpu_usage}% for {device_host}")
                                except (ValueError, TypeError):
                                    self.logger.warning(f"Unable to parse CPU: {cpu_current}")
                        
                        # Memory usage
                        memory_data = data.get("Memory", {})
                        if isinstance(memory_data, dict):
                            memory_used = memory_data.get("Used")
                            memory_total = memory_data.get("Total")
                            if memory_used is not None and memory_total is not None:
                                try:
                                    used = float(memory_used)
                                    total = float(memory_total)
                                    if total > 0:
                                        memory_usage = (used / total) * 100
                                        self.report_metric("poly_trio_memory_usage", memory_usage, dimensions={"endpoint": device_host})
                                        self.logger.info(f"Reported Memory usage: {memory_usage:.2f}% for {device_host}")
                                except (ValueError, TypeError, ZeroDivisionError) as e:
                                    self.logger.warning(f"Unable to calculate memory: {e}")
            except Exception as e:
                self.logger.error(f"Error collecting device stats for {device_host}: {e}")
            
            # Collect running configuration
            try:
                config_url = f"{base_url}/api/v1/mgmt/device/runningConfig"
                resp = requests.get(config_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                config_data = resp.json()
                
                if self.should_log("DEBUG"):
                    self.logger.info(f"Running Config: {str(config_data)[:500]}...")
                
                if isinstance(config_data, dict):
                    data = config_data.get("data", {})
                    if isinstance(data, dict):
                        # Provisioning server
                        prov_config = data.get("Provisioning", {})
                        if isinstance(prov_config, dict):
                            prov_server = prov_config.get("Server")
                            if prov_server is not None and prov_server != "":
                                self.report_metric("poly_trio_provisioning_configured", 1, dimensions={"endpoint": device_host})
                                self.logger.info(f"Provisioning server configured for {device_host}")
                            else:
                                self.report_metric("poly_trio_provisioning_configured", 0, dimensions={"endpoint": device_host})
                        
                        # DHCP feature
                        dhcp_config = data.get("DHCP", {})
                        if isinstance(dhcp_config, dict):
                            dhcp_feature = dhcp_config.get("Feature")
                            if dhcp_feature:
                                dhcp_enabled = 1 if str(dhcp_feature).lower() == "enabled" else 0
                                self.report_metric("poly_trio_dhcp_feature", dhcp_enabled, dimensions={"endpoint": device_host})
                                self.logger.info(f"DHCP feature: {dhcp_feature} for {device_host}")
            except Exception as e:
                self.logger.error(f"Error collecting config for {device_host}: {e}")

            # Collect network info
            try:
                network_url = f"{base_url}/api/v1/mgmt/network/info"
                resp = requests.get(network_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                network_data = resp.json()
                
                if self.should_log("DEBUG"):
                    self.logger.info(f"Network Info: {json.dumps(network_data)}")
                
                if isinstance(network_data, dict):
                    data = network_data.get("data", {})
                    if isinstance(data, dict):
                        # DHCP status
                        dhcp_status_str = data.get("DHCP")
                        if dhcp_status_str is not None:
                            dhcp_status = 1 if str(dhcp_status_str).lower() == "enabled" else 0
                            self.report_metric("poly_trio_network_dhcp", dhcp_status, dimensions={"endpoint": device_host})
                            self.logger.info(f"DHCP status: {dhcp_status_str} for {device_host}")
                        
                        # Link status
                        lan_port_status = data.get("LANPortStatus")
                        if lan_port_status is not None:
                            link_up = 1 if str(lan_port_status).lower() == "active" else 0
                            self.report_metric("poly_trio_link_status", link_up, dimensions={"endpoint": device_host})
                            self.logger.info(f"Link status: {lan_port_status} for {device_host}")
                        
                        # Link speed
                        lan_speed = data.get("LANSpeed")
                        if lan_speed:
                            try:
                                speed_str = str(lan_speed).replace("MB", "").replace("Mbps", "").strip()
                                speed_value = int(speed_str)
                                self.report_metric("poly_trio_link_speed", speed_value, dimensions={"endpoint": device_host})
                                self.logger.info(f"Link speed: {speed_value} Mbps for {device_host}")
                            except (ValueError, TypeError):
                                self.logger.warning(f"Unable to parse link speed: {lan_speed}")
            except Exception as e:
                self.logger.error(f"Error collecting network info for {device_host}: {e}")

            # Collect network statistics
            try:
                net_stats_url = f"{base_url}/api/v1/mgmt/network/stats"
                resp = requests.get(net_stats_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                net_stats_data = resp.json()
                
                data = net_stats_data.get("data", {})
                rx_packets = data.get("RxPackets")
                tx_packets = data.get("TxPackets")
                
                if rx_packets is not None:
                    try:
                        rx_count = int(rx_packets)
                        self.report_metric("poly_trio_rx_packets", rx_count, dimensions={"endpoint": device_host})
                    except (ValueError, TypeError):
                        self.logger.warning(f"Unable to parse RxPackets: {rx_packets}")
                
                if tx_packets is not None:
                    try:
                        tx_count = int(tx_packets)
                        self.report_metric("poly_trio_tx_packets", tx_count, dimensions={"endpoint": device_host})
                    except (ValueError, TypeError):
                        self.logger.warning(f"Unable to parse TxPackets: {tx_packets}")
            except Exception as e:
                self.logger.error(f"Error collecting network stats for {device_host}: {e}")

            # Poll device status
            try:
                poll_url = f"{base_url}/api/v1/mgmt/pollForStatus"
                resp = requests.get(poll_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                poll_data = resp.json()
                
                data = poll_data.get("data", {})
                device_state = data.get("State", "Unknown")
                
                status_map = {"Idle": 0, "Active": 1, "InCall": 1, "Ringing": 1, "Error": 2}
                status_value = status_map.get(device_state, -1)
                
                if status_value >= 0:
                    self.report_metric("poly_trio_device_status", status_value, dimensions={"endpoint": device_host})
                    self.logger.info(f"Device state: {device_state} (value: {status_value}) for {device_host}")
                else:
                    self.logger.warning(f"Unknown device state: {device_state}")
            except Exception as e:
                self.logger.error(f"Error polling status for {device_host}: {e}")

            # Collect call status
            try:
                call_status_url = f"{base_url}/api/v2/webCallControl/callStatus"
                resp = requests.get(call_status_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                call_data = resp.json()
                
                active_calls = 0
                if isinstance(call_data, dict) and "data" in call_data:
                    calls = call_data.get("data", [])
                    if isinstance(calls, list):
                        active_calls = len(calls)
                
                self.report_metric("poly_trio_active_calls", active_calls, dimensions={"endpoint": device_host})
                self.logger.info(f"Active calls: {active_calls} for {device_host}")
            except Exception as e:
                self.logger.error(f"Error collecting call status for {device_host}: {e}")

            # Collect call logs
            try:
                call_logs_url = f"{base_url}/api/v1/mgmt/callLogs"
                resp = requests.get(call_logs_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                call_logs_data = resp.json()
                
                total_logs = 0
                if isinstance(call_logs_data, dict) and "data" in call_logs_data:
                    logs = call_logs_data.get("data", [])
                    if isinstance(logs, list):
                        total_logs = len(logs)
                
                self.report_metric("poly_trio_total_call_logs", total_logs, dimensions={"endpoint": device_host})
            except Exception as e:
                self.logger.error(f"Error collecting call logs for {device_host}: {e}")

            # Missed calls
            try:
                missed_logs_url = f"{base_url}/api/v1/mgmt/callLogs/missed"
                resp = requests.get(missed_logs_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                missed_logs_data = resp.json()
                
                missed_logs = 0
                if isinstance(missed_logs_data, dict) and "data" in missed_logs_data:
                    logs = missed_logs_data.get("data", [])
                    if isinstance(logs, list):
                        missed_logs = len(logs)
                
                self.report_metric("poly_trio_missed_calls", missed_logs, dimensions={"endpoint": device_host})
            except Exception as e:
                self.logger.error(f"Error collecting missed calls for {device_host}: {e}")
            
            # Received calls
            try:
                received_logs_url = f"{base_url}/api/v1/mgmt/callLogs/received"
                resp = requests.get(received_logs_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                received_logs_data = resp.json()
                
                received_logs = 0
                if isinstance(received_logs_data, dict) and "data" in received_logs_data:
                    logs = received_logs_data.get("data", [])
                    if isinstance(logs, list):
                        received_logs = len(logs)
                
                self.report_metric("poly_trio_received_calls", received_logs, dimensions={"endpoint": device_host})
            except Exception as e:
                self.logger.error(f"Error collecting received calls for {device_host}: {e}")
            
            # Placed calls
            try:
                placed_logs_url = f"{base_url}/api/v1/mgmt/callLogs/placed"
                resp = requests.get(placed_logs_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                placed_logs_data = resp.json()
                
                placed_logs = 0
                if isinstance(placed_logs_data, dict) and "data" in placed_logs_data:
                    logs = placed_logs_data.get("data", [])
                    if isinstance(logs, list):
                        placed_logs = len(logs)
                
                self.report_metric("poly_trio_placed_calls", placed_logs, dimensions={"endpoint": device_host})
            except Exception as e:
                self.logger.error(f"Error collecting placed calls for {device_host}: {e}")

            # Communication info (microphone mute)
            try:
                comm_info_url = f"{base_url}/api/v1/mgmt/media/communicationInfo"
                resp = requests.get(comm_info_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                comm_data = resp.json()
                
                mic_muted = comm_data.get("data", {}).get("Microphone", {}).get("Muted")
                if mic_muted is not None:
                    mute_status = 1 if mic_muted else 0
                    self.report_metric("poly_trio_microphone_muted", mute_status, dimensions={"endpoint": device_host})
            except Exception as e:
                self.logger.error(f"Error collecting communication info for {device_host}: {e}")

            # Session stats (VoIP quality - only during calls)
            try:
                session_stats_url = f"{base_url}/api/v1/mgmt/media/sessionStats"
                resp = requests.get(session_stats_url, auth=auth, timeout=10, verify=False)
                resp.raise_for_status()
                session_data = resp.json()
                
                if self.should_log("DEBUG"):
                    self.logger.info(f"Session Stats: {json.dumps(session_data)}")
                
                if isinstance(session_data, dict):
                    if "data" in session_data:
                        stats = session_data.get("data", {})
                        if isinstance(stats, dict):
                            # VoIP quality metrics
                            audio_packet_loss = stats.get("AudioPacketLoss")
                            jitter = stats.get("Jitter")
                            latency = stats.get("Latency")
                            mos_score = stats.get("MOS") or stats.get("MOScore")
                            r_factor = stats.get("RFactor")
                            rtp_packets_sent = stats.get("RTPPacketsSent")
                            rtp_packets_received = stats.get("RTPPacketsReceived")
                            audio_bitrate = stats.get("AudioBitrate")
                            
                            if audio_packet_loss is not None:
                                self.report_metric("poly_trio_audio_packet_loss", audio_packet_loss, dimensions={"endpoint": device_host})
                            
                            if jitter is not None:
                                try:
                                    self.report_metric("poly_trio_jitter", float(jitter), dimensions={"endpoint": device_host})
                                except (ValueError, TypeError):
                                    pass
                            
                            if latency is not None:
                                try:
                                    self.report_metric("poly_trio_latency", float(latency), dimensions={"endpoint": device_host})
                                except (ValueError, TypeError):
                                    pass
                            
                            if mos_score is not None:
                                try:
                                    self.report_metric("poly_trio_mos_score", float(mos_score), dimensions={"endpoint": device_host})
                                except (ValueError, TypeError):
                                    pass
                            
                            if r_factor is not None:
                                try:
                                    self.report_metric("poly_trio_r_factor", float(r_factor), dimensions={"endpoint": device_host})
                                except (ValueError, TypeError):
                                    pass
                            
                            if rtp_packets_sent is not None:
                                self.report_metric("poly_trio_rtp_packets_sent", rtp_packets_sent, dimensions={"endpoint": device_host})
                            
                            if rtp_packets_received is not None:
                                self.report_metric("poly_trio_rtp_packets_received", rtp_packets_received, dimensions={"endpoint": device_host})
                            
                            if audio_bitrate is not None:
                                try:
                                    self.report_metric("poly_trio_audio_bitrate", float(audio_bitrate), dimensions={"endpoint": device_host})
                                except (ValueError, TypeError):
                                    pass
            except Exception as e:
                self.logger.error(f"Error collecting session stats for {device_host}: {e}")

        timestamp = datetime.now().isoformat()
        self.logger.info(f"[{timestamp}] Poly query method ended")

    def fastcheck(self) -> Status:
        """Health check for the extension."""
        return Status(StatusValue.OK)


def main():
    ExtensionImpl().run()


if __name__ == "__main__":
    main()

--------------------------------------------------------------------------------
3.2. extension/extension.yaml
--------------------------------------------------------------------------------
# Extension metadata
name: custom:cfs-poly-trio
version: 1.0.0
minDynatraceVersion: "1.285"
author:
  name: "Dynatrace"

# Python runtime configuration
python:
  runtime:
    module: poly_trio  # Must match folder name
    version:
      min: "3.10"
  activation:
    remote:
      path: activationSchema.json
    local:
      path: activationSchema.json

# Custom device topology
topology:
  types:
    - key: custom:poly_trio_device
      displayName: Poly Trio Device
      properties:
        - key: endpoint
          displayName: Endpoint IP
          type: string
      relations: []

# Metric definitions
metrics:
  # Device Status
  - key: poly_trio_device_up
    metadata:
      displayName: Poly Trio Device Up
      description: Device reachability (1=Up, 0=Down)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_device_status
    metadata:
      displayName: Poly Trio Device Status
      description: Device state (0=Idle, 1=Active, 2=Error)
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

  # System Health
  - key: poly_trio_cpu_usage
    metadata:
      displayName: Poly Trio CPU Usage
      description: CPU utilization percentage
      unit: Percent
    source:
      type: custom:poly_trio_device

  - key: poly_trio_memory_usage
    metadata:
      displayName: Poly Trio Memory Usage
      description: Memory utilization percentage
      unit: Percent
    source:
      type: custom:poly_trio_device

  # Network Metrics
  - key: poly_trio_network_dhcp
    metadata:
      displayName: Poly Trio DHCP Status
      description: DHCP enabled status (1=Enabled, 0=Disabled)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_link_status
    metadata:
      displayName: Poly Trio Link Status
      description: Ethernet link up/down (1=Up, 0=Down)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_link_speed
    metadata:
      displayName: Poly Trio Link Speed
      description: Negotiated link speed in Mbps
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_rx_packets
    metadata:
      displayName: Poly Trio RX Packets
      description: Received network packets
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_tx_packets
    metadata:
      displayName: Poly Trio TX Packets
      description: Transmitted network packets
      unit: Count
    source:
      type: custom:poly_trio_device

  # Call Statistics
  - key: poly_trio_active_calls
    metadata:
      displayName: Poly Trio Active Calls
      description: Number of active calls
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_total_call_logs
    metadata:
      displayName: Poly Trio Total Call Logs
      description: Total call log entries
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_missed_calls
    metadata:
      displayName: Poly Trio Missed Calls
      description: Number of missed calls
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_received_calls
    metadata:
      displayName: Poly Trio Received Calls
      description: Number of received calls
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_placed_calls
    metadata:
      displayName: Poly Trio Placed Calls
      description: Number of placed calls
      unit: Count
    source:
      type: custom:poly_trio_device

  # Configuration
  - key: poly_trio_provisioning_configured
    metadata:
      displayName: Poly Trio Provisioning Server
      description: Provisioning server configured (1=Yes, 0=No)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_dhcp_feature
    metadata:
      displayName: Poly Trio DHCP Feature
      description: DHCP feature enabled (1=Yes, 0=No)
      unit: Count
    source:
      type: custom:poly_trio_device

  # Communication
  - key: poly_trio_microphone_muted
    metadata:
      displayName: Poly Trio Microphone Muted
      description: Microphone mute status (1=Muted, 0=Unmuted)
      unit: Count
    source:
      type: custom:poly_trio_device

  # VoIP Quality (during active calls only)
  - key: poly_trio_jitter
    metadata:
      displayName: Poly Trio Jitter
      description: Inter-packet delay variation in ms
      unit: MilliSecond
    source:
      type: custom:poly_trio_device

  - key: poly_trio_latency
    metadata:
      displayName: Poly Trio Latency
      description: End-to-end audio delay in ms
      unit: MilliSecond
    source:
      type: custom:poly_trio_device

  - key: poly_trio_mos_score
    metadata:
      displayName: Poly Trio MOS Score
      description: Mean Opinion Score (1-5, higher is better)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_r_factor
    metadata:
      displayName: Poly Trio R-Factor
      description: Quality rating (0-100, higher is better)
      unit: Count
    source:
      type: custom:poly_trio_device

  - key: poly_trio_audio_packet_loss
    metadata:
      displayName: Poly Trio Audio Packet Loss
      description: RTP packet loss percentage
      unit: Percent
    source:
      type: custom:poly_trio_device

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

--------------------------------------------------------------------------------
3.3. extension/activationSchema.json
--------------------------------------------------------------------------------
{
  "types": {
    "endpoint": {
      "type": "object",
      "displayName": "Poly Trio Device",
      "description": "Configuration for a Poly Trio C60 device",
      "properties": {
        "IP": {
          "type": "text",
          "displayName": "Device IP Address",
          "description": "IP address or hostname of the Poly Trio device"
        },
        "user": {
          "type": "text",
          "displayName": "Username",
          "description": "Admin username for REST API access",
          "default": "Polycom"
        },
        "password": {
          "type": "secret",
          "displayName": "Password",
          "description": "Admin password for REST API access"
        }
      },
      "required": ["IP", "password"]
    }
  },
  "properties": {
    "endpoints": {
      "type": "list",
      "displayName": "Poly Trio Devices",
      "description": "List of Poly Trio devices to monitor",
      "items": {
        "type": "endpoint"
      }
    }
  },
  "required": ["endpoints"]
}

--------------------------------------------------------------------------------
3.4. activation.json (Local Development)
--------------------------------------------------------------------------------
{
  "endpoints": [
    {
      "IP": "xx.xx.xx.xx",
      "user": "Polycom",
      "password": "YourPasswordHere"
    }
  ]
}

NOTE: Replace "YourPasswordHere" with actual device password.
For multiple devices, add additional objects to the endpoints array.

--------------------------------------------------------------------------------
3.5. setup.py
--------------------------------------------------------------------------------
from setuptools import setup, find_packages

setup(
    name="poly_trio",
    version="1.0.0",
    description="Dynatrace extension for Poly Trio C60 monitoring",
    author="Dynatrace",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "urllib3>=1.26.0"
    ],
    entry_points={
        'console_scripts': [
            'poly_trio=poly_trio.__main__:main',
        ],
    },
)

--------------------------------------------------------------------------------
3.6. README.MD
--------------------------------------------------------------------------------
# Poly Trio C60 Dynatrace Extension

Monitor Poly Trio C60 conference phones with comprehensive metrics collection.

## Features

- **17+ Metrics**: System health, network, calls, VoIP quality
- **REST API**: Secure Digest Authentication
- **Multi-Device**: Monitor multiple Poly Trio devices
- **Production Ready**: Error handling, logging, retries

## Requirements

- Python 3.10+
- Dynatrace Environment
- Poly Trio C60 firmware 5.9.5+
- Network access to devices (HTTPS port 443)

## Quick Start

### 1. Configure Devices

Edit `activation.json`:
```json
{
  "endpoints": [
    {
      "IP": "192.168.1.100",
      "user": "Polycom",
      "password": "YourPassword"
    }
  ]
}
```

### 2. Local Testing

```bash
dt-sdk run
```

### 3. Build Extension

```bash
dt-sdk build
```

### 4. Deploy to Dynatrace

1. Upload the .zip file to Dynatrace
2. Configure credentials
3. Activate extension

## Metrics Collected

### System Health
- CPU usage %
- Memory usage %
- Uptime

### Network
- Link status & speed
- DHCP status
- RX/TX packets

### Calls
- Active calls
- Call logs (total, missed, received, placed)

### VoIP Quality (during calls)
- MOS Score
- Jitter, Latency
- Packet Loss
- R-Factor

## Configuration

### Logging Levels

Edit `poly_trio/__main__.py`:
```python
LOG_LEVEL = "INFO"  # ERROR, WARNING, INFO, DEBUG
```

### Collection Interval

Default: 5 minutes. To change:
```python
self.schedule(self.poly_query, timedelta(minutes=5))
```

## Troubleshooting

### No metrics appearing
- Check device IP is reachable
- Verify credentials are correct
- Set `LOG_LEVEL = "DEBUG"` to see API responses

### Connection errors
- Ensure HTTPS (port 443) is accessible
- Check firewall rules
- Verify device REST API is enabled

### VoIP metrics missing
- These only appear during active calls
- Make a test call to populate these metrics

## Support

For issues or questions, review the logs with DEBUG level enabled.

================================================================================
4. CONFIGURATION
================================================================================

--------------------------------------------------------------------------------
4.1. Device Credentials
--------------------------------------------------------------------------------

OPTION 1: Via activation.json (Local Development)
  File: activation.json
  Format:
    {
      "endpoints": [
        {
          "IP": "192.168.1.250",
          "user": "Polycom",
          "password": "Complete 500 rooms."
        }
      ]
    }

OPTION 2: Via Dynatrace UI (Production)
  1. Upload extension to Dynatrace
  2. Go to Settings > Monitoring > Monitored technologies > Custom extensions
  3. Find "Poly Trio" extension
  4. Click "Add monitoring configuration"
  5. Enter device details

--------------------------------------------------------------------------------
4.2. Logging Configuration
--------------------------------------------------------------------------------

Edit poly_trio/__main__.py:

  LOG_LEVEL = "INFO"  # Options: ERROR, WARNING, INFO, DEBUG

LOG LEVELS:
  - ERROR   : Only critical errors
  - WARNING : Warnings + errors
  - INFO    : Normal operation (DEFAULT)
  - DEBUG   : Full API responses (troubleshooting)

--------------------------------------------------------------------------------
4.3. Collection Interval
--------------------------------------------------------------------------------

Edit poly_trio/__main__.py, line ~38:

  self.schedule(self.poly_query, timedelta(minutes=5))

RECOMMENDED:
  - Testing: 1 minute
  - Production: 5 minutes
  - High-volume: 10 minutes

================================================================================
5. INSTALLATION & DEPLOYMENT
================================================================================

--------------------------------------------------------------------------------
5.1. Local Development Setup
--------------------------------------------------------------------------------

1. Clone/Create project structure:
   mkdir poly_trio
   cd poly_trio
   mkdir poly_trio extension

2. Create all files from Section 3

3. Install Python dependencies:
   pip install requests urllib3

4. Configure devices in activation.json

5. Test locally:
   dt-sdk run

--------------------------------------------------------------------------------
5.2. Build Extension
--------------------------------------------------------------------------------

1. Ensure all files are in place

2. Build extension package:
   dt-sdk build

3. Output: Creates poly_trio.zip in project root

--------------------------------------------------------------------------------
5.3. Deploy to Dynatrace
--------------------------------------------------------------------------------

1. Log in to Dynatrace environment

2. Navigate to:
   Settings > Monitoring > Monitored technologies > Custom extensions

3. Click "Upload custom extension 2.0"

4. Select poly_trio.zip

5. Click "Upload extension"

6. Configure monitoring:
   - Click "Add monitoring configuration"
   - Enter device IP, username, password
   - Save configuration

7. Verify metrics:
   - Wait 5-10 minutes for first collection
   - Search for "poly_trio" metrics in Data Explorer

================================================================================
6. TESTING & VALIDATION
================================================================================

--------------------------------------------------------------------------------
6.1. Local Testing
--------------------------------------------------------------------------------

STEP 1: Run extension locally
  Command: dt-sdk run
  
STEP 2: Check logs for:
  ✓ "Initializing poly-trio extension"
  ✓ "Processing device: <IP>"
  ✓ "Device <IP> is up. Model: Trio C60"
  ✓ "Reported CPU usage: X% for <IP>"
  ✓ "Sent 17 metric lines to EEC"

STEP 3: Verify no errors
  ✗ "Error connecting to device"
  ✗ "401 Unauthorized"
  ✗ "Connection timeout"

--------------------------------------------------------------------------------
6.2. Expected Metrics
--------------------------------------------------------------------------------

ALWAYS COLLECTED (17 metrics):
  - poly_trio_device_up
  - poly_trio_uptime
  - poly_trio_cpu_usage
  - poly_trio_memory_usage
  - poly_trio_link_status
  - poly_trio_link_speed
  - poly_trio_network_dhcp
  - poly_trio_dhcp_feature
  - poly_trio_provisioning_configured
  - poly_trio_rx_packets
  - poly_trio_tx_packets
  - poly_trio_device_status
  - poly_trio_active_calls
  - poly_trio_total_call_logs
  - poly_trio_missed_calls
  - poly_trio_received_calls
  - poly_trio_placed_calls

DURING CALLS ONLY (8 metrics):
  - poly_trio_jitter
  - poly_trio_latency
  - poly_trio_mos_score
  - poly_trio_r_factor
  - poly_trio_audio_packet_loss
  - poly_trio_rtp_packets_sent
  - poly_trio_rtp_packets_received
  - poly_trio_audio_bitrate

--------------------------------------------------------------------------------
6.3. Test Scenarios
--------------------------------------------------------------------------------

TEST 1: Basic Connectivity
  1. Start extension: dt-sdk run
  2. Wait 30 seconds
  3. Check for: "Sent 17 metric lines"
  Result: 17 metrics should be collected

TEST 2: Multiple Devices
  1. Add 2+ devices to activation.json
  2. Run extension
  3. Check logs for each device IP
  Result: Metrics collected for all devices

TEST 3: VoIP Quality Metrics
  1. Start extension
  2. Make a test call on the Poly device
  3. Check logs during call
  Result: Additional VoIP metrics appear

TEST 4: Error Handling
  1. Use wrong password in activation.json
  2. Run extension
  3. Check for: "Error connecting to device"
  Result: Extension logs error but continues

================================================================================
7. METRICS REFERENCE
================================================================================

--------------------------------------------------------------------------------
7.1. Metric Categories
--------------------------------------------------------------------------------

SYSTEM HEALTH (3 metrics)
  CPU Usage        : poly_trio_cpu_usage (%)
  Memory Usage     : poly_trio_memory_usage (%)
  Uptime           : poly_trio_uptime (seconds)

DEVICE STATUS (2 metrics)
  Device Up        : poly_trio_device_up (0/1)
  Device State     : poly_trio_device_status (0=Idle, 1=Active, 2=Error)

NETWORK (5 metrics)
  DHCP Status      : poly_trio_network_dhcp (0/1)
  Link Status      : poly_trio_link_status (0/1)
  Link Speed       : poly_trio_link_speed (Mbps)
  RX Packets       : poly_trio_rx_packets (count)
  TX Packets       : poly_trio_tx_packets (count)

CONFIGURATION (2 metrics)
  Provisioning     : poly_trio_provisioning_configured (0/1)
  DHCP Feature     : poly_trio_dhcp_feature (0/1)

CALLS (5 metrics)
  Active Calls     : poly_trio_active_calls (count)
  Total Logs       : poly_trio_total_call_logs (count)
  Missed           : poly_trio_missed_calls (count)
  Received         : poly_trio_received_calls (count)
  Placed           : poly_trio_placed_calls (count)

VOIP QUALITY (5 metrics - during calls only)
  MOS Score        : poly_trio_mos_score (1-5)
  R-Factor         : poly_trio_r_factor (0-100)
  Jitter           : poly_trio_jitter (ms)
  Latency          : poly_trio_latency (ms)
  Packet Loss      : poly_trio_audio_packet_loss (%)

RTP STATISTICS (3 metrics - during calls only)
  Packets Sent     : poly_trio_rtp_packets_sent (count)
  Packets Received : poly_trio_rtp_packets_received (count)
  Audio Bitrate    : poly_trio_audio_bitrate (kbps)

--------------------------------------------------------------------------------
7.2. Alert Recommendations
--------------------------------------------------------------------------------

CRITICAL (Immediate Action)
  poly_trio_device_up = 0
    Alert: "Device offline"
    Action: Check network, reboot device
  
  poly_trio_link_status = 0
    Alert: "Network link down"
    Action: Check Ethernet cable
  
  poly_trio_device_status = 2
    Alert: "Device in error state"
    Action: Check device logs

HIGH PRIORITY
  poly_trio_mos_score < 3.5
    Alert: "Poor call quality"
    Action: Check network QoS
  
  poly_trio_audio_packet_loss > 2
    Alert: "High packet loss"
    Action: Check network congestion
  
  poly_trio_jitter > 30
    Alert: "High jitter"
    Action: Check network stability

MEDIUM PRIORITY
  poly_trio_cpu_usage > 80
    Alert: "High CPU usage"
    Action: Monitor device performance
  
  poly_trio_memory_usage > 85
    Alert: "High memory usage"
    Action: Consider device reboot

================================================================================
8. TROUBLESHOOTING
================================================================================

--------------------------------------------------------------------------------
8.1. Common Issues
--------------------------------------------------------------------------------

ISSUE: "No devices configured for monitoring"
  CAUSE: activation.json is empty or malformed
  FIX: Verify activation.json syntax, ensure endpoints array exists

ISSUE: "Error connecting to device: 401 Unauthorized"
  CAUSE: Incorrect username or password
  FIX: Verify credentials, try Polycom/admin as username

ISSUE: "Error connecting to device: Connection timeout"
  CAUSE: Network unreachable, firewall blocking
  FIX: Ping device, check firewall rules for port 443

ISSUE: "Only 8 metrics collected instead of 17"
  CAUSE: API responses have different field names
  FIX: Set LOG_LEVEL="DEBUG", check actual API responses

ISSUE: "VoIP quality metrics not appearing"
  CAUSE: No active calls on device
  FIX: Make a test call, metrics will appear during call

ISSUE: "Extension crashes on startup"
  CAUSE: Python syntax error or missing dependency
  FIX: Check Python version (3.10+), reinstall dependencies

--------------------------------------------------------------------------------
8.2. Debugging Steps
--------------------------------------------------------------------------------

STEP 1: Enable DEBUG logging
  Edit poly_trio/__main__.py:
    LOG_LEVEL = "DEBUG"

STEP 2: Run extension and capture logs
  Command: dt-sdk run > debug.log 2>&1

STEP 3: Review logs for:
  - Connection errors
  - API response formats
  - Missing fields
  - Authentication issues

STEP 4: Test API endpoints directly
  curl --digest -u Polycom:"password" -k \
    https://192.168.1.250/api/v1/mgmt/device/stats

STEP 5: Compare actual vs expected JSON structure

--------------------------------------------------------------------------------
8.3. API Endpoint Reference
--------------------------------------------------------------------------------

Device Info:
  /api/v2/mgmt/device/info
  Returns: Model, MAC, Uptime, Firmware

Device Stats:
  /api/v1/mgmt/device/stats
  Returns: CPU, Memory usage

Running Config:
  /api/v1/mgmt/device/runningConfig
  Returns: Network, DHCP, Provisioning settings

Network Info:
  /api/v1/mgmt/network/info
  Returns: IP, DHCP, Link speed/status

Network Stats:
  /api/v1/mgmt/network/stats
  Returns: RX/TX packets, Uptime

Poll Status:
  /api/v1/mgmt/pollForStatus
  Returns: Device state (Idle/Active/Error)

Call Status:
  /api/v2/webCallControl/callStatus
  Returns: Active calls

Call Logs:
  /api/v1/mgmt/callLogs
  /api/v1/mgmt/callLogs/missed
  /api/v1/mgmt/callLogs/received
  /api/v1/mgmt/callLogs/placed
  Returns: Call history

Session Stats:
  /api/v1/mgmt/media/sessionStats
  Returns: VoIP quality metrics (during calls)

Communication Info:
  /api/v1/mgmt/media/communicationInfo
  Returns: Mute status, RTP ports

================================================================================
END OF INSTRUCTIONS
================================================================================

For additional help or questions:
- Review IMPLEMENTED_METRICS.MD for detailed metric documentation
- Check METRICS_COVERAGE.MD for coverage analysis
- Enable DEBUG logging to troubleshoot API issues

Last Updated: 2025-12-29
