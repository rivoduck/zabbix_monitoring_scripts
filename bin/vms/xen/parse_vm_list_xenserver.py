from subprocess import Popen, PIPE, STDOUT
import sys
import re
import json



def getValue(line=""):
    res=None
    line_arr = line.split(':')
    line_arr.pop(0)

    res=line_arr.pop(0)
    for el in line_arr:
        res = "%s:%s" % (res, el)

    return res.strip()



def createVmEntry(detailed=False, uuid="", vcpus="", name="", descr="", powerstate="", memory="", ports="", dom_id=""):
    vmEntry=None
    if uuid != "" and name[:22] != "Control domain on host":
        vmEntry={
            "VCPUs-number": vcpus,
            "uuid": uuid,
            "name-label": name,
            "name-description": descr,
            "power-state": powerstate,
            "memory-actual_mb": memory,
            "vnc-port": "",
            "ports": ports,
            "disks": [],
            "total-disk-space_mb": "0"
        }
        
        if detailed:
            # get info about storage (VDBs/VDIs)
            exec_command = 'xe vbd-list vm-uuid=%s type=Disk params=vdi-uuid' % uuid
            p = Popen(exec_command, shell=True, stdout=PIPE, stderr=STDOUT)
            vdi_uuids=[]
            for line in p.stdout.readlines():
                if not re.match("^\s*$", line):

                    # match uuid
                    if re.match("^vdi-uuid\s", line):
                        vdi_uuids.append(getValue(line))
            
            for vdi_uuid in vdi_uuids:
                exec_command = 'xe vdi-list uuid=%s params=uuid,name-label,sr-name-label,virtual-size' % vdi_uuid
                p = Popen(exec_command, shell=True, stdout=PIPE, stderr=STDOUT)
                
                disk_list=[]
                disk_uuid=""
                disk_name=""
                disk_sr_name=""
                disk_size=0
                total_disk_size_mb=0
                for line in p.stdout.readlines():
                    if not re.match("^\s*$", line):

                        # match uuid to identify start of VDI record
                        if re.match("^uuid\s", line):
                            # VDI record starts
                            # add a VDI if there is data from a previuos iteration
                            if disk_uuid and disk_uuid != "":
                                disk_entry={
                                    'label': "%s (%s)" % (disk_name, disk_sr_name),
                                    'size-mb': "%s" % disk_size
                                }
                                disk_list.append(disk_entry)
                            # acquire disk UUID
                            disk_uuid = getValue(line)
                                
                            
                        # match name-label line
                        if re.match("^\s*name-label\s", line):
                            disk_name = getValue(line)

                        # match sr-name-label line
                        if re.match("^\s*sr-name-label\s", line):
                            disk_sr_name = getValue(line)
                        
                        # match virtual-size line
                        if re.match("^\s*virtual-size\s", line):
                            try:
                                # convert to int and do a floor division to converto to MB
                                disk_size = int(getValue(line)) / 1048576
                                total_disk_size_mb += disk_size
                            except Exception:
                                disk_size = 0
                # add last disk
                if disk_uuid and disk_uuid != "":
                    disk_entry={
                        'label': "%s (%s)" % (disk_name, disk_sr_name),
                        'size-mb': "%s" % disk_size
                    }
                    disk_list.append(disk_entry)
            
            vmEntry["disks"] = disk_list
            vmEntry["total-disk-space_mb"] = "%s" % total_disk_size_mb
            
            # get VNC port for console
            vnc_port=""
            if dom_id and dom_id != "":
                exec_command = 'xenstore read /local/domain/%s/console/vnc-port' % dom_id
                p = Popen(exec_command, shell=True, stdout=PIPE, stderr=STDOUT)
                
                lines=p.stdout.readlines()
                if len(lines) > 0:
                    vnc_port=lines[0].strip()
            vmEntry["vnc-port"] = vnc_port

    return vmEntry


vm_name=""
command=""
carry_uuid=""

detailed_view=False

if len(sys.argv) > 1:
    vm_name=sys.argv[1]
if len(sys.argv) > 2:
    command=sys.argv[2]
if len(sys.argv) > 3:
    carry_uuid=sys.argv[3]



exec_command = 'xe vm-list params=uuid,dom-id,name-label,name-description,power-state,memory-static-max,VCPUs-max,networks'
if vm_name and vm_name != "":
    exec_command = '%s name-label="%s"' % (exec_command, vm_name)
    detailed_view=True

p = Popen(exec_command, shell=True, stdout=PIPE, stderr=STDOUT)

uuid=""
vcpus=""
name=""
descr=""
powerstate=""
dom_id=""
memory=""
ports=""

vms=[]

for line in p.stdout.readlines():
    if not re.match("^\s*$", line):

        # match domain start line
        if re.match("^uuid\s", line):
            # VM record starts
            # add a VM in case it has been acquired from previuos records
            vm=createVmEntry(detailed_view, uuid, vcpus, name, descr, powerstate, memory, ports, dom_id)
            if vm:
                vms.append(vm)

            # acquire UUID
            uuid = getValue(line)

        # match name-label line
        if re.match("^\s*name-label\s", line):
            name = getValue(line)
            
        # match name-description line
        if re.match("^\s*name-description\s", line):
            descr = getValue(line)

        # match power-state line
        if re.match("^\s*power-state\s", line):
            powerstate = getValue(line)

        # match memory-static-max line
        if re.match("^\s*memory-static-max\s", line):
            memory = int(getValue(line))
            # convert to Mbytes
            memory = memory / 1048576
            memory = str(memory)

        # match VCPUs-max line
        if re.match("^\s*VCPUs-max\s", line):
            vcpus = getValue(line)

        # match dom-id line
        if re.match("^\s*dom-id\s", line):
            dom_id = getValue(line)

        # match networks line
        # line looks like "0/ip: 194.116.76.130; 0/ipv6/0: fe80::d063:25ff:fe1d:7f79; 1/ip: 10.45.0.11; 1/ipv6/0: fe80::ac62:9dff:fed7:9e83"
        if re.match("^\s*networks\s", line):
            networks = getValue(line)

            ports={}
            # split list of IPs by ";"
            networks_arr = networks.split(';')
            for ip_entry in networks_arr:
                if ip_entry != "":
                    # separate intf string and address
                    ip_arr = ip_entry.split(':')

                    intf_string=ip_arr.pop(0)
                    # get intf number
                    intf_number=intf_string.split('/')[0].strip()
                    intf_name="vif%s" % intf_number

                    # create port entry
                    if not intf_name in ports:
                        ports[intf_name]={'name': intf_name, 'mac': "", 'ips': []}
            
                    if len(ip_arr) > 0:
                        address=ip_arr.pop(0)
                        for el in ip_arr:
                            address = "%s:%s" % (address, el)
                        address=address.strip()

                        ports[intf_name]['ips'].append(address)

            # convert to list
            ports=ports.values()

# add last VM
vm=createVmEntry(detailed_view, uuid, vcpus, name, descr, powerstate, memory, ports, dom_id)
if vm:
    vms.append(vm)


reply=""

if detailed_view:
    # generate details of specified VM
    if len(vms) > 0:
        vm=vms[0]
    else:
        vm=createVmEntry(detailed_view, carry_uuid, "0", vm_name, "", "deleted", "0", [])


    if command == 'state':
        reply=vm['power-state']
    else:
        reply=json.dumps(vm)

else:
    # generate discovery list of VMs (only name and uuid)
    data=[]
    for vm in vms:
        data.append({
            '{#VMNAME}': vm['name-label'],
            '{#VMUUID}': vm['uuid']
        })
    reply=json.dumps({'data': data})


    


print reply




