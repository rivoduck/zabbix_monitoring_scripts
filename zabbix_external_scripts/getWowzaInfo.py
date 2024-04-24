#!/usr/bin/python3
# Vicente Dominguez
# -a conn - Global connections
# -a appnum - Global application(streaming) num

#import urllib2, base64, sys, getopt
import urllib.request, base64, sys, getopt
import xml.etree.ElementTree as ET

# Default values
username = "admin"
password = "admin"
host = "localhost"
port = "8086"
realm = "Wowza Media Systems"
getInfo = "None"

##

def Usage ():
        print ("Usage: getWowzaInfo.py -u user -p password -h 127.0.0.1 -P 8086 -a [conn|appnum]")
        sys.exit(2)

def getCurrentConnections():
        print (xmlroot[0].text)

def getCurrentStreams():
        Application =  xmlroot.findall('VHost/Application')
        print (len(Application))

def unknown():
        print ("unknown")

##


def main (username,password,host,port,getInfo):

    global xmlroot    
    argv = sys.argv[1:]	
    
    if (len(argv) < 1):
        Usage()   
    
    try :
        opts, args = getopt.getopt(argv, "u:p:h:P:a:")

        # Assign parameters as variables
        for opt, arg in opts :
            if opt == "-u" :
                username = arg
            if opt == "-p" :
                password = arg
            if opt == "-h" :
                host = arg
            if opt == "-P" :
                port = arg
            if opt == "-a" :
                getInfo = arg
    except :
            Usage()


    url="http://" + host + ":" + port + "/connectioncounts/"

    request = urllib.request.Request(url)
    authinfo = '%s:%s' % (username, password)
    base64string = base64.b64encode(authinfo.encode("utf-8"))
    request.add_header("Authorization", "Basic %s" % str(base64string, "utf-8"))
    page_content = urllib.request.urlopen(request)

    xmlroot = ET.fromstring(page_content.read())	



    if ( getInfo == "conn"):
        getCurrentConnections()
    elif ( getInfo == "appnum"):
        getCurrentStreams()
    else:
        unknown()
        sys.exit(1)



if __name__ == "__main__":

    main(username,password,host,port,getInfo)

