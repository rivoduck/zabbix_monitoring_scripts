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



def createVmEntry(uuid="", vcpus="", name="", descr="", powerstate="", memory="", ports=""):
    vmEntry=None
    if uuid != "" and name[:22] != "Control domain on host":
        vmEntry={
            "VCPUs-number": vcpus,
            "uuid": uuid,
            "name-label": name,
            "name-description": descr,
            "power-state": powerstate,
            "memory-actual_mb": memory,
            "ports": ports
        }

    return vmEntry


vm_name=""
command=""
carry_uuid=""

if len(sys.argv) > 1:
    vm_name=sys.argv[1]
if len(sys.argv) > 2:
    command=sys.argv[2]
if len(sys.argv) > 3:
    carry_uuid=sys.argv[3]



exec_command = 'xe vm-list params=uuid,name-label,name-description,power-state,memory-static-max,VCPUs-max,networks'
if vm_name and vm_name != "":
    exec_command = "%s name-label=%s" % (exec_command, vm_name)

p = Popen(exec_command, shell=True, stdout=PIPE, stderr=STDOUT)

uuid=""
vcpus=""
name=""
descr=""
powerstate=""
memory=""
ports=""

vms=[]

for line in p.stdout.readlines():
    if not re.match("^\s*$", line):

        # match domain start line
        if re.match("^uuid\s", line):
            # VM record starts
            # add a VM in case it has been acquired from previuos records
            vm=createVmEntry(uuid, vcpus, name, descr, powerstate, memory, ports)
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

        # match networks line
        # line looks like "0/ip: 194.116.76.130; 0/ipv6/0: fe80::d063:25ff:fe1d:7f79; 1/ip: 10.45.0.11; 1/ipv6/0: fe80::ac62:9dff:fed7:9e83"
        if re.match("^\s*networks\s", line):
            networks = getValue(line)

            ports={}
            # split list of IPs by ";"
            networks_arr = networks.split(';')
            for ip_entry in networks_arr:
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
vm=createVmEntry(uuid, vcpus, name, descr, powerstate, memory, ports)
if vm:
    vms.append(vm)


reply=""

if vm_name == "":
    # generate discovery list of VMs (only name and uuid)
    data=[]
    for vm in vms:
        data.append({
            '{#VMNAME}': vm['name-label'],
            '{#VMUUID}': vm['uuid']
        })
    reply=json.dumps({'data': data})

else:
    # generate details of specified VM
    if len(vms) > 0:
        vm=vms[0]
    else:
        vm={
            "VCPUs-number": "0",
            "uuid": carry_uuid,
            "name-label": vm_name,
            "name-description": "",
            "power-state": "deleted",
            "memory-actual_mb": "0",
            "ports": []
        }

    if command == 'state':
        reply=vm['power-state']
    else:
        reply=json.dumps(vm)

    


print reply




