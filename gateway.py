from __future__ import division
import sys
import psutil
import requests
import json
import time as tm
from datetime import *
import calendar
from settings import port
import urllib2
import subprocess


class Tracker:

    def __init__(self):
        print "----Gateway status logging started----"
        self.url = "http://lrsapis.herokuapp.com"
        # self.url = "http://0.0.0.0:5000"
        self.token = None

    def get_utilization(self,name=None):
        pid = subprocess.Popen("ps aux|grep "+name+"|awk '{print $2;exit}'", shell=True, stdout=subprocess.PIPE).stdout.read().strip()
        cpu = subprocess.Popen("ps aux|grep "+name+"|awk '{print $3;exit}'", shell=True, stdout=subprocess.PIPE).stdout.read().strip()
        memory = subprocess.Popen("ps aux|grep "+name+"|awk '{print $4;exit}'", shell=True, stdout=subprocess.PIPE).stdout.read().strip()
        # data = process.strip().split(' ')
        # print data
        # cpu = data[2]
        # memory = data[3]
        # process = ""

        # pid = subprocess.Popen("ps -ax|grep "+name+"|awk '{print $1;exit}'", shell=True, stdout=subprocess.PIPE).stdout.read()
        # pid = int(pid.strip())
        # p = psutil.Process(pid)
        # val_list = []

        # for i in range(10):
        #     data = p.get_cpu_percent()
        #     val_list.append(data)
        #     tm.sleep(0.1)

        # cpu = max(val_list)
        return {"pid":pid,"cpu":cpu,"memory":memory}  

    def get_api_token(self):
        try:
            res = requests.get(''.join([self.url,"/api/token"]), auth=('sharadvishe', 'password'))
        except:
            return None
        return res.json()['token']
        

    def get_device_id(self):
        import commands
        import os
        if os.path.exists("/sys/class/net/eth0/address"):
            tempFile = open("/sys/class/net/eth0/address")
        elif os.path.exists("/sys/class/net/eth1/address"): 
            tempFile = open("/sys/class/net/eth1/address")
        else:
            return "00:00:00:00:00:00"
            
        hwaddr = tempFile.read()
        tempFile.close()
        return hwaddr.strip()        

    def firmware_status(self):
        import socket;
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1',port))
        if result == 0:
           return "Running"
        else:
           return "Stopped"

    def internet_on(self):
        try:
            response=urllib2.urlopen('http://www.google.com',timeout=20)
            return True
        except urllib2.URLError as err: pass
        return False

    def get_cpu_temperature(self):
        import commands
        import os
        if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            tempFile = open("/sys/class/thermal/thermal_zone0/temp")
            cpu_temp = tempFile.read()
            tempFile.close()
            return float(cpu_temp)/1000 
        else:
            return 0

    def load_data(self):
        flag = 0
        device_id = self.get_device_id()

        while True:             

            try:
                firmware_usage = self.get_utilization("tracker*.zip")
            except:
                print "firmware is not running"
            else:
                print "Firmware usage:"+str(firmware_usage)

            app_usage = self.get_utilization("gateway_monitor*.zip")

            print "Monitoring app usage:"+json.dumps(app_usage)

            if self.internet_on():

                if self.token is None:
                    self.token = self.get_api_token()
                if flag >= 1:
                    flag = 0
                    to_timestamp = datetime.utcnow()

                    log = {
                        "device_id":device_id,
                        "from_timestamp":from_timestamp.strftime("%Y-%m-%d %I:%M:%S %p"),
                        "to_timestamp":to_timestamp.strftime("%Y-%m-%d %I:%M:%S %p"),
                        "status" : "Connection Lost",
                    }
                    log =  json.dumps(log,indent=4)
                    # print log

                    try:
                        requests.post(''.join([self.url,"/lrs/api/v1.0/gateway/internet/log"]),data=log,headers={'Content-Type':'application/json'}, auth=(self.token,''),verify=False,timeout=10) 
                    except:
                        pass

                cpu_utilization = psutil.cpu_percent()
                boot_time = datetime.utcfromtimestamp(psutil.get_boot_time())      
                uptime = datetime.now() - boot_time
                uptime = int(uptime.total_seconds())
                memstats = psutil.virtual_memory()
                mem_utilization = ((memstats.total-memstats.free)/memstats.total)*100               
                temperature = self.get_cpu_temperature()                
                firmware_status = self.firmware_status()        

                status = {
                    "timestamp":datetime.utcnow().strftime("%Y-%m-%d %I:%M:%S %p"),
                    "cpu_utilization":cpu_utilization,
                    "boot_time":boot_time.strftime("%Y-%m-%d %I:%M:%S %p"),
                    "uptime":uptime,
                    "mem_utilization":round(mem_utilization,2),
                    "temperature":temperature,
                    "device_id" : device_id,
                    "firmware_status":firmware_status
                }

                data =  json.dumps(status,indent=4)
                # print data

                try:
                    resp = requests.post(''.join([self.url,"/lrs/api/v1.0/statastic"]),data=data,headers={'Content-Type':'application/json'}, auth=(self.token,''),verify=False,timeout=10) 
                except requests.exceptions.Timeout:        
                    pass
                except requests.exceptions.TooManyRedirects:
                    sys.exit(1)
                except requests.exceptions.RequestException as e:
                    print e
                    sys.exit(1)

            elif flag == 0:
                flag = 1
                from_timestamp = datetime.utcnow()
            else:
                flag += 1                
            tm.sleep(5)

if __name__ == "__main__":
    tr = Tracker()
    tr.load_data()