import subprocess
import json
import sys


def _run_cmd(cmd):
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if proc.returncode != 0:
        err_msg = "storCLI exit code is {}".format(proc.returncode)
        if err is not None and err.strip():
            err_msg += ", stderr: {}".format(err)
        raise ValueError(err_msg)

    if err is not None and err.strip():
        err_msg = "storCLI succeeded but an error was printed when executing '{}': {}".format(" ".join(cmd), err.strip())
        raise ValueError(err_msg)

    return out


def disk_analysis(exec_name, disk_name=None, command=None):
    """Return Raid array Status."""
    reply = []
    out = ""
    
    cmd = [ exec_name ]
    if disk_name and disk_name != '':
        cmd += [disk_name]
    else:
        cmd += ["/c0"] # TODO: controller is hardcoded to 0
    cmd += ["show"]
    cmd += ["all"]
    cmd += ["J"]
    try:
        out = _run_cmd(cmd)
        
    except Exception as e:
        exit(-1)
        
        
        
    if disk_name and disk_name != '':
        # check a specific disk in raid array
        disk = {
            "state": "unknown",
            "medium": "unknown",
            "interface": "unknown",
            "model": "unknown",
            "size": "unknown",
            "smartstate": "unknown",
            "message": ""
        }
        try:
            data = json.loads(out.decode("utf-8"))
            controller = data["Controllers"][0]
            command_status = controller["Command Status"]["Status"]
            
            if command_status != "Success" or len(controller["Response Data"]["Drive {}".format(disk_name)]) == 0:
                # problems getting data about drive
                disk["state"]="problem"
                disk["message"] = controller["Command Status"]["Detailed Status"][0]["ErrMsg"]
            else:
                # got data from command
                # get state, medium, interface, model
                info=controller["Response Data"]["Drive {}".format(disk_name)][0]
                if info["State"] == "Onln":
                    disk["state"] = "online"
                else:
                    disk["state"] = "offline"
                disk["medium"]=info["Med"]
                disk["interface"]=info["Intf"]
                disk["model"]=info["Model"]
                disk["size"]=info["Size"]
                
                # get predictive Failure Count and SMART state
                info_det=controller["Response Data"]["Drive {} - Detailed Information".format(disk_name)]["Drive {} State".format(disk_name)]
                if info_det["S.M.A.R.T alert flagged by drive"] != "No":
                    disk["smartstate"] = "fail"
                else:
                    disk["smartstate"] = "OK"
                
        except Exception as e:
            disk["state"] = "notfound"
            disk["message"] = "disk {} not found".format(disk_name)
            
        if command == 'state':
            # return state of specified disk
            reply = disk['state']
        elif command == 'smartstate':
            reply = disk['smartstate']
        else:
            # return whole disk
            reply = json.dumps(disk)
            
        return reply
    else:
        # start array discovery process
        try:
            data = json.loads(out.decode("utf-8"))
            controller = data["Controllers"][0]
            controller_number = controller["Command Status"]["Controller"]
            physical_drives = controller["Response Data"]["PD LIST"]
            for drive in physical_drives:
                eid, slot = drive["EID:Slt"].split(":")
                drive_name = "/c{}/e{}/s{}".format(controller_number, eid, slot)
                reply.append({
                    '{#DISKNAME}': drive_name
                })
        except Exception as e:
            # in case of exception return empty discovery list
            pass

        return json.dumps({'data': reply})


disk_name = ""
command = ""

if len(sys.argv) > 1:
    executable_name = sys.argv[1]

if len(sys.argv) > 2:
    disk_name = sys.argv[2]
if len(sys.argv) > 3:
    command = sys.argv[3]

print disk_analysis(executable_name, disk_name, command)
