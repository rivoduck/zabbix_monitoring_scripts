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
        print("storCLI succeeded but an error was printed when executing '{}': {}".format(" ".join(cmd), err.strip()))

    return out


def disk_analysis(disk_name=None, command=None):
    """Return Raid array Status."""
    reply = []
    if disk_name:
        # check a specific disk in raid array
        cmd = ["storcli"]
        cmd += [disk_name]
        cmd += ["show"]
        cmd += ["all"]
        cmd += ["J"]
        try:
            out = _run_cmd(cmd)
        except Exception as e:
            print(e)
            exit(-1)
        try:
            data = json.loads(out.decode("utf-8"))
            controller = data["Controllers"][0]
            command_status = controller["Command Status"]["Status"]
            if command_status == "Failure" or len(controller["Response Data"]["Drive {}".format(disk_name)]) == 0:
                disk = {
                    "State": controller["Command Status"]["Detailed Status"][0]["Status"],
                    "ErrMsg": controller["Command Status"]["Detailed Status"][0]["ErrMsg"]
                }
            else:
                disk = controller["Response Data"]["Drive {}".format(disk_name)][0]
        except Exception as e:
            print(e)
            exit(-1)
        if command == 'state':
            # return state of specified disck
            reply = disk['State']
        else:
            # return whole disk
            reply = json.dumps(disk)
        return reply
    else:
        # start array discovery process
        cmd = ["storcli"]
        cmd += ["/c0"]
        cmd += ["show"]
        cmd += ["all"]
        cmd += ["J"]
        try:
            out = _run_cmd(cmd)
        except Exception as e:
            print(e)
            exit(-1)
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
            print(e)
            exit(-1)

        return json.dumps({'data': reply})


disk_name = ""
command = ""

if len(sys.argv) > 1:
    disk_name = sys.argv[1]
if len(sys.argv) > 2:
    command = sys.argv[2]

print disk_analysis(disk_name, command)
