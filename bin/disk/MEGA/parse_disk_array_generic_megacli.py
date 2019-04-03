from subprocess import Popen, PIPE, STDOUT
import subprocess
import json
import sys
import re




def disk_analysis(exec_name, disk_name=None, command=None):
    """Return Raid array Status."""
    reply = []
    out = ""
    
    cmd = "%s -PDList -aALL" % exec_name
    try:
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
        
        disks=[]
        reset_disk = {
            "state": "unknown",
            "medium": "unknown",
            "interface": "unknown",
            "model": "unknown",
            "size": "unknown",
            "smartstate": "unknown",
            "message": ""
        }
        disk = reset_disk
        cur_controller = None
        cur_enclosure_id = 0 # this is hardcoded, TODO: run an aditional command to find the enclosure id
        cur_slot = None
        cur_diskname = None
        
        disk_found=False
        
        for line in p.stdout.readlines():
            # identify line Adapter number
            if re.match("^Adapter #", line):
                line_arr = line.split('#')
                try:
                    cur_controller = line_arr[1].strip()
                except Exception:
                    pass
                    
            # identify line Enclosure Device ID (start of disk)
            if re.match("^Enclosure Device ID: ", line):
                # do something with the data about previous disk if available
                if disk_name:
                    if disk_name == cur_diskname:
                        # return details of specified disk
                        disk_found=True
                        break
                
                else:
                    # return list of disks
                    if cur_diskname:
                        reply.append({
                            '{#DISKNAME}': cur_diskname
                        })
                # reset values
                disk=reset_disk
                cur_diskname=None
                cur_slot = None
                
                
                
            # identify line Slot Number: 
            if re.match("^Slot Number: ", line):
                line_arr = line.split(':')
                try:
                    cur_slot = line_arr[1].strip()
                except Exception:
                    pass
                
                
            # identify line PD Type: 
            if re.match("^PD Type: ", line):
                line_arr = line.split(':')
                try:
                    disk['interface'] = line_arr[1].strip()
                except Exception:
                    pass
                
                
            # identify line Raw Size: 
            if re.match("^Raw Size: ", line):
                line_arr = line.split(':')
                try:
                    temp=line_arr[1].strip()
                    temp_arr = temp.split(' ')
                    disk['size'] = "%s %s" % (temp_arr[0], temp_arr[1])
                except Exception:
                    pass
                
            # identify line Media Type: 
            if re.match("^Media Type: ", line):
                line_arr = line.split(':')
                try:
                    temp = line_arr[1].strip()
                    if temp == "Solid State Device":
                        disk['medium'] = 'SSD'
                    else:
                        disk['medium'] = temp
                except Exception:
                    pass
                

            # identify line Firmware state: 
            if re.match("^Firmware state: ", line):
                line_arr = line.split(':')
                try:
                    temp = line_arr[1].strip()
                    temp_arr = temp.split(',')
                    if temp_arr[0] == "Online," or temp_arr[0] == "Online":
                        disk['state'] = 'online'
                    else:
                        disk['state'] = 'offline'
                except Exception:
                    pass

                
            # identify line S.M.A.R.T. alert: 
            if re.match("^Drive has flagged a S.M.A.R.T alert : ", line):
                line_arr = line.split(':')
                try:
                    temp = line_arr[1].strip()
                    if temp == "No":
                        disk['smartstate'] = 'OK'
                    else:
                        disk['smartstate'] = 'fail'
                except Exception:
                    pass
            
            
            # define disk name
            if cur_controller != None and cur_enclosure_id != None and cur_slot != None:
                cur_diskname = "/c%s/e%s/s%s" % (cur_controller, cur_enclosure_id, cur_slot)
            
    except Exception as e:
        print e
        exit(-1)
    
    
    if disk_name:
        # disk details
        if not disk_found:
            disk["state"] = "notfound"
            disk["message"] = "disk {} not found".format(disk_name)
        if command == 'state':
            # return state of specified disk
            reply = disk['state']
        elif command == 'smartstate':
            reply = disk['smartstate']
        else:
            # return whole disk
            reply = disk
            reply = json.dumps(reply)
    else:
        # disk discovery
        
        # add last disk
        if cur_diskname:
            reply.append({
                '{#DISKNAME}': cur_diskname
            })
        
            reply = {'data': reply}
            
            reply = json.dumps(reply)
        
    return reply
    


disk_name = ""
command = ""

if len(sys.argv) > 1:
    executable_name = sys.argv[1]

if len(sys.argv) > 2:
    disk_name = sys.argv[2]
if len(sys.argv) > 3:
    command = sys.argv[3]

print disk_analysis(executable_name, disk_name, command)
