from subprocess import Popen, PIPE, STDOUT
import sys
import re
import json
import socket
import time
import os


# Configuration: set to True to fetch UUID and description during generic discovery
FETCH_UUID_IN_DISCOVERY = False
FETCH_NETWORK_INFO_FROM_AGENT = False


def get_proxmox_node():
    """
    Get the current node name from /etc/hostname
    """
    try:
        with open('/etc/hostname', 'r') as f:
            return f.read().strip().split('.')[0]
    except:
        return "pve"  # default fallback


def log_message(message):
    """
    Log messages to stderr for debugging
    """
    if os.environ.get('DEBUG_PROXMOX', '0') == '1':
        import traceback
        # Get caller information
        stack = traceback.extract_stack()
        # Get the caller (2 frames up: log_message -> caller -> actual function)
        caller_frame = stack[-2]
        # caller_info = "%s:%d in %s()" % (caller_frame.filename.split('/')[-1], caller_frame.lineno, caller_frame.name)
        # caller_info = "%s():%d" % (caller_frame.name, caller_frame.lineno)
        # print("[DEBUG] [%s] %s" % (caller_info, message), file=sys.stderr)
        print("[DEBUG] %s" % (message), file=sys.stderr)


def execute_pvesh(path):
    """
    Execute pvesh command and parse JSON output
    """
    try:
        exec_command = 'pvesh get %s --output-format json' % path
        log_message("Executing: %s" % exec_command)
        
        start_time = time.time()
        p = Popen(exec_command, shell=True, stdout=PIPE, stderr=STDOUT)
        output = p.stdout.read().decode('utf-8', errors='ignore')
        elapsed = time.time() - start_time
        
        log_message("pvesh command completed in %.2f seconds: %s" % (elapsed, path))
        
        if output.strip():
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                # If output is not JSON (e.g., error message), log it and return error dict
                log_message("pvesh returned non-JSON output: %s" % output.strip())
                return {'error': output.strip()}
        return {}
    except Exception as e:
        log_message("Error executing pvesh: %s" % str(e))
        print("Error executing pvesh: %s" % str(e), file=sys.stderr)
        return {}


def get_vm_config(node, vmid):
    """
    Get VM configuration (cached single fetch)
    """
    # log_message("[get_vm_config] calling execute_pvesh for config")
    return execute_pvesh('/nodes/%s/qemu/%s/config' % (node, vmid))


def get_storage_info(vm_config):
    """
    Get disk information for a VM from config
    """
    disk_list = []
    total_disk_size_mb = 0
    
    try:
        log_message("[get_storage_info] Extracting storage info")
        
        # Parse disk entries (sata0, sata1, scsi0, scsi1, virtio0, etc.)
        for key in vm_config:
            if key.startswith(('sata', 'scsi', 'virtio', 'ide')):
                disk_info = vm_config[key]
                
                # Parse disk string like "local:100/vm-100-disk-1.qcow2,size=10G"
                if isinstance(disk_info, str):
                    parts = disk_info.split(',')
                    disk_spec = parts[0]
                    
                    # Extract storage and disk name
                    if ':' in disk_spec:
                        storage, disk_name = disk_spec.split(':', 1)
                    else:
                        storage = "unknown"
                        disk_name = disk_spec
                    
                    # Get size from the second part
                    disk_size = 0
                    for part in parts[1:]:
                        if part.startswith('size='):
                            size_str = part.replace('size=', '')
                            # Convert size to MB
                            disk_size = int(convert_size_to_mb(size_str))
                            total_disk_size_mb += disk_size
                            break
                    
                    # Only add disk if it has a size > 0
                    if disk_size > 0:
                        disk_entry = {
                            'label': "%s (%s)" % (disk_name, storage),
                            'size-mb': "%s" % disk_size
                        }
                        disk_list.append(disk_entry)
    except Exception as e:
        pass
    
    return disk_list, str(total_disk_size_mb)

def convert_size_to_mb(size_str):
    """
    Convert size string (like 10G, 512M) to MB
    """
    size_str = size_str.strip().upper()
    
    multipliers = {
        'K': 1024**1 / (1024**2),
        'M': 1,
        'G': 1024,
        'T': 1024**2
    }
    
    for suffix, multiplier in multipliers.items():
        if suffix in size_str:
            try:
                value = float(size_str.replace(suffix, ''))
                return value * multiplier
            except:
                pass
    
    try:
        return int(size_str)
    except:
        return 0


def get_network_info(vm_config, node, vmid):
    """
    Get network interface information for a VM.
    If FETCH_NETWORK_INFO_FROM_AGENT is True: uses only agent data
    If FETCH_NETWORK_INFO_FROM_AGENT is False: uses only config data
    """
    port_list = []
    
    try:
        if FETCH_NETWORK_INFO_FROM_AGENT:
            log_message("[get_network_info] Extracting network interfaces details (querying agent)")
            
            try:
                agent_data = execute_pvesh('/nodes/%s/qemu/%s/agent/network-get-interfaces' % (node, vmid))
                
                if 'result' in agent_data and isinstance(agent_data['result'], list):
                    for iface in agent_data['result']:
                        mac = iface.get('hardware-address', '').lower()
                        iface_name = iface.get('name', '')
                        ip_addresses = []
                        
                        if 'ip-addresses' in iface:
                            for ip_info in iface['ip-addresses']:
                                # Only include IPv4 addresses
                                if ip_info.get('ip-address-type') == 'ipv4':
                                    ip_address = ip_info.get('ip-address', '')
                                    if ip_address and ip_address not in ['127.0.0.1']:  # Skip loopback
                                        ip_addresses.append(ip_address)
                        
                        # Build VIF entry from agent data only
                        vif_entry = {
                            'descr': iface_name,
                            'name': iface_name,
                            'mac': mac,
                            'ips': ip_addresses
                        }
                        port_list.append(vif_entry)
                elif 'errors' in agent_data or 'error' in agent_data:
                    log_message("[get_network_info] guest agent not available: %s" % agent_data.get('errors', agent_data.get('error', 'unknown error')))
            except Exception as e:
                log_message("[get_network_info] could not fetch agent interfaces: %s" % str(e))
        else:
            log_message("[get_network_info] Extracting network interfaces details (using config data only)")
            
            # Parse network entries (net0, net1, net2, etc.)
            net_idx = 0
            while 'net%d' % net_idx in vm_config:
                net_info = vm_config['net%d' % net_idx]
                
                if isinstance(net_info, str):
                    # Parse network string like "virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0,tag=759"
                    parts = {}
                    for part in net_info.split(','):
                        if '=' in part:
                            k, v = part.split('=', 1)
                            parts[k] = v
                    
                    # Extract MAC address from virtio, e1000, or rtl8139 field
                    mac = parts.get('virtio', parts.get('e1000', parts.get('rtl8139', ''))).lower()
                    
                    # Extract interface name from bridge field
                    iface_name = parts.get('bridge', 'net%d' % net_idx)
                    
                    # Build description from tag value
                    tag = parts.get('tag', '')
                    if tag:
                        descr = tag
                    else:
                        descr = iface_name
                    
                    vif_entry = {
                        'descr': descr,
                        'name': iface_name,
                        'mac': mac,
                        'ips': []
                    }
                    port_list.append(vif_entry)
                
                net_idx += 1
    except Exception as e:
        pass
    
    return port_list


def get_console_port(node, vmid):
    """
    Get VNC/SPICE console port for a VM
    """
    return "n/a"



def get_uuid(vm_config):
    """
    Extract UUID from vmgenid field in VM config
    vmgenid format: <uuid>
    """
    try:
        log_message("[get_uuid] Extracting VM UUID")
        
        if 'vmgenid' in vm_config:
            return vm_config['vmgenid']
    except:
        pass
    
    return ""


def get_description(vm_config):
    """
    Extract description from VM config
    """
    try:
        log_message("[get_description] Extracting VM description")
        
        if 'description' in vm_config:
            description = vm_config['description']
            return description
    except:
        pass
    
    return ""


def createVmEntry(detailed=False, node="", vmid="", name="", status="", memory="", vcpus="", description="", vm_config=None):
    """
    Create a VM entry with information from Proxmox
    """
    vmEntry = None
    
    if vmid and vmid != "":
        vmEntry = {
            "power-state": "running" if status == "running" else "halted",
            "name-description": description,
            "name-label": name,
            "vnc-port": "",
            "vmid": vmid,
            "node": node,
            "memory-actual_mb": memory,
            "VCPUs-number": vcpus,
            "ports": [],
            "disks": [],
            "total-disk-space_mb": "0"
        }
        
        if detailed and vm_config:
            # Get disk information
            disk_list, total_disk_size_mb = get_storage_info(vm_config)
            vmEntry["disks"] = disk_list
            vmEntry["total-disk-space_mb"] = "%s" % total_disk_size_mb
            
            # Get network information
            port_list = get_network_info(vm_config, node, vmid)
            vmEntry["ports"] = port_list
            
            # Get console port
            vnc_port = get_console_port(node, vmid)
            vmEntry["vnc-port"] = vnc_port
    
    return vmEntry


vm_name = ""
command = ""
carry_vmid = ""

detailed_view = False

global_start_time = time.time()

if len(sys.argv) > 1:
    vm_name = sys.argv[1]
if len(sys.argv) > 2:
    command = sys.argv[2]
if len(sys.argv) > 3:
    carry_vmid = sys.argv[3]

# Get current node (still needed for detailed queries)
node = get_proxmox_node()
log_message("Starting VM discovery on node: %s" % node)

# Get list of all VMs from current node only
vms = []
start_list = time.time()
vms_data = execute_pvesh('/nodes/%s/qemu' % node)
log_message("VM list fetched in %.2f seconds, found %d VMs" % (time.time() - start_list, len(vms_data) if isinstance(vms_data, list) else 0))

target_vmid = None
target_vmid_data = None

if isinstance(vms_data, list):
    for vm in vms_data:
        # Parse cluster resource format: name is like "qemu/110", id is vmid
        vmid = str(vm.get('vmid', ''))
        name = vm.get('name', '')
        status = vm.get('status', 'running' if vm.get('uptime') else 'stopped')
        cpus  = int(vm.get('cpus', 1))
        node = vm.get('node', get_proxmox_node())  # Get node from resource data
        
        maxmem = vm.get('maxmem', 0)
        memory_mb = str(int(maxmem / (1024 * 1024) if maxmem else 0))
        
        # Check if this is the VM we're searching for
        is_target_vm = False
        if vm_name and vm_name != "":
            if name.lower() == vm_name.lower():
                is_target_vm = True
                target_vmid = vmid
                target_vmid_data = vm
        
        # Only process VMs that match our criteria
        # If searching for a specific VM, only add that VM
        # If doing generic discovery, add all VMs
        should_process = False
        if vm_name and vm_name != "":
            # Searching for specific VM - only process target VM
            should_process = is_target_vm
        else:
            # Generic discovery - process all VMs
            should_process = True
        
        if should_process:
            # Only fetch config for target VM (detailed view) or if FETCH_UUID_IN_DISCOVERY is enabled
            uuid = ""
            description = ""
            vm_config = None
            if (is_target_vm or FETCH_UUID_IN_DISCOVERY) and command != 'state':
                log_message("Fetching config for VM %s (id=%s)" % (name, vmid))
                vm_config = get_vm_config(node, vmid)
                uuid = get_uuid(vm_config)
                description = get_description(vm_config)
            
            # Create VM entry - only with detailed data for target VM
            vm_entry = createVmEntry(is_target_vm, node, vmid, name, status, memory_mb, cpus, description, vm_config)
            # log_message("vm_entry1 %s" % json.dumps(vm_entry))
            if vm_entry:
                vm_entry['uuid'] = uuid
                vms.append(vm_entry)
    
    # Set detailed_view if target VM was found
    if target_vmid:
        detailed_view = True



reply = ""

# log_message("Processing results (detailed_view=%s)" % detailed_view)

if detailed_view:
    # Generate details of specified VM
    # log_message("detailed_view %s" % json.dumps(vms))
    # log_message("vms_data %s" % json.dumps(vms_data))


    if len(vms) > 0:
        vm = vms[0]
    else:
        vm = createVmEntry(detailed_view, node, carry_vmid, vm_name, "stopped", "0", "0")
        # log_message("vm (detailed_view) %s" % json.dumps(vm))

    if command == 'state':
        try:
            reply = vm['power-state']
        except:
            reply = "deleted"
    else:
        reply = json.dumps(vm)
else:
    # Generate discovery list of VMs (only name, vmid and uuid)
    data = []
    for vm in vms:
        try:
            entry = {
                '{#VMNAME}': vm['name-label'],
                '{#VMID}': vm['vmid'],
                '{#VMUUID}': vm.get('uuid', '')
            }
            data.append(entry)
        except:
            pass
    reply = json.dumps({'data': data})

global_elapsed = time.time() - global_start_time
log_message("Script execution completed in %.2f seconds" % global_elapsed)

print(reply)
