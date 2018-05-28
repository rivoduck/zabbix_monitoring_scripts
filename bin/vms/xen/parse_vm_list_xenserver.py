# xe vm-list params=uuid,name-label,name-description,power-state,memory-static-max,VCPUs-max,networks


from subprocess import Popen, PIPE, STDOUT

p = Popen('xe vm-list params=uuid,name-label,name-description,power-state,memory-static-max,VCPUs-max,networks', shell=True, stdout=PIPE, stderr=STDOUT)
for line in p.stdout.readlines():
    print line,


retval = p.wait()
