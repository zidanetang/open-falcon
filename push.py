#! -*- coding:utf-8 -*-
import os
import json
import time
import re
import requests
import telnetlib
from datetime import datetime
adb = '/work/deploy/res/android-sdk-tinypace/adb'
#path_adb = '/work/deploy/adb'
falcon_agent = "http://127.0.0.1:1988/v1/push"
def get_ip():    #获取主机IP
    ip = os.popen("ifconfig | grep 172.16 | awk -F: '{print $2}'| awk '{print $1}'").readline()
    return ip.strip()
def get_cputemp():  #获取主机cpu温度
    t = os.popen('cat /sys/class/thermal/thermal_zone0/temp').readline()
    temp = float(t)
    return temp/1000
def get_gputemp(): #获取主机GPU温度
    t = os.popen("/opt/vc/bin/vcgencmd measure_temp|cut -d = -f2|cut -d \\' -f1").readline()
    temp = float(t)
    return  temp
def get_devices(adb):  #获取usb的设备uuid和数量
    adb_list = os.popen('%s devices -l' % (adb)).readlines()
    match_string = re.compile("(^.+)device usb")
    #print(adb_list)
    try:
        devices = []
        for device in adb_list:
            devs = match_string.findall(device)
            for count in range(len(devs)):
                a = devices.append(devs[count].split()[0])
    except:
        print("error!")
    return devices,len(devices)
def get_jar_usecpu(): #获取jar的cpu使用率
    usecpu = os.popen("ps aux |grep controller | grep -v grep | tail -n1 | awk '{print $3}'").readline()
    if usecpu == "":
        return usecpu == -1
    else:
        jar_usecpu = float(usecpu,)
        return jar_usecpu
def hostname():   #获取主机名
    try:
        name = os.popen("hostname").readline()
    except:
        print("get hostname wrong!")
    return name.strip()
def systime(): #获取系统时间
    try:
        host_time = int(time.time())
    except:
        print("get sys_time wrong!")
    return host_time
def http_post(server,pushdata,json=json):   #post数据
    try:
        res = requests.post(url=server,data=pushdata)
        print(res)
        return res.text
    except:
        print("post fail!")
        return 0
    finally:
        res.close()
def get_mobile_battery(adb,*list):
    battery = {}
    try:
        for device in list:
            status = os.popen("%s -s %s shell dumpsys battery|grep level|awk '{print$2}'" % (adb,device)).readline().strip()
            #name = os.popen("%s -s %s shell cat /system/build.prop|grep product.model|cut -d = -f2" % (adb,device)).readline().strip() + '.battery'
            battery["%s.batterystatus" % (device.lower())] = status
    except:
        print("error!")
    finally:
        return battery
def push_data(name,currtime,**monitor):
    try:
        for key,value in monitor.items():
            #tag1 = key.split(".")[0]     #获取tag的目标字段
            tag2 = "place=sisdc,project="
            tag3 = "%s%s" % (tag2,key)
            count = [
                    {
                        "endpoint": name,
                        "metric": key ,
                        "timestamp": currtime,
                        "step": 60,
                        "value": value,
                        "counterType": "GAUGE",
                        "tags": tag3
                    }
                        ]
            res = json.dumps(count)
            http_post(falcon_agent,res)
    except:
        print("error!")
    finally:
        print("post ok!")
def vnc_check(adb,*list):
    #./adb forward --list|grep 4df7775f002abfbb |grep 5901|awk {'print $2'}|awk -F':' '{print$2}'
    #vnc = telnetlib.Telnet('127.0.0.1',port,).read_some().strip()
    vnc_status = {}
    try:
        for device in list:
            #name = os.popen("%s -s %s shell cat /system/build.prop|grep product.model|cut -d = -f2" % (adb,device)).readline().strip() + '.vnc.status'
            port = os.popen("%s forward --list |grep %s |grep 5901|awk {'print $2'}|awk -F ':' {'print$2'}" % (adb,device)).readline().strip()
            tn = telnetlib.Telnet('127.0.0.1',port,5)
            vnc = tn.read_some().strip()
            if vnc == 'RFB 003.008':
                vnc_status["%s.vncstatus" % (device.lower())] = 1
            else:
                vnc_status["%s.vncstatus" % (device.lower())] = -1
            tn.close()
    except:
        print("telnet error")
    finally:
        return vnc_status


while True:
    #now = list(time.localtime())[5]
    start_time = datetime.now()
    now = start_time.second
    if now == 0:
        name = get_ip()
        collect_time = systime()
        devices_list,count = get_devices(adb)
        monitor1 = {"mobile.count":count,"cputemp":get_cputemp(),"gputemp":get_gputemp(),"jar.cpu.used":get_jar_usecpu()}
        push_data(name,collect_time,**monitor1)
        if count > 0:
            monitor2 = get_mobile_battery(adb,*devices_list)
            monitor3 = vnc_check(adb,*devices_list)
            list1 = [monitor2,monitor3]
            for a in list1:
                push_data(name,collect_time,**a)
            #print(monitor2)
        end_time = datetime.now()
        diff = end_time - start_time
        sleep_time = abs(60-diff.total_seconds())
        time.sleep(sleep_time)
    else:
        continue






'''
while True:
    now = list(time.localtime())[5]
    if now == 0:
        host_ip = get_ip()
        cputemp = get_cputemp()
        gputemp = get_gputemp()
        devices_list,count = get_devices()
        jar_uescpu = get_jar_usecpu()
        host_name = hostname()
        host_time = systime()
        monitor_dict = {"mobile.count":count,"cputemp.count":cputemp,"gputemp.count":gputemp,"jar.cpu.used.count":jar_uescpu}
        for key,value in monitor_dict.items():
            tag1 = key.split(".")[0]     #获取tag的目标字段
            tag2 = "place=sisdc,project="
            tag3 = "%s%s" % (tag2,tag1)      #拼接最后的目标tag字段
            print(tag3)
            count = [
                {
                    "endpoint": host_ip,
                    "metric": key,
                    "timestamp": host_time,
                    "step": 60,
                    "value": value,
                    "counterType": "GAUGE",
                    "tags": tag3
                }
                    ]
            res = json.dumps(count)
            http_post(falcon_agent,res)
            print(res)
        time.sleep(2)
    else:
        continue


'''
'''
host_ip = get_ip()
temp = get_temp()
devices_list,count = get_devices()
jar_uescpu = get_jar_usecpu()
host_name = hostname()
host_time = systime()
mobile_count = [
    {
        "endpoint": host_ip,
        "metric": "mobile.count",
        "timestamp": host_time,
        "step": 60,
        "value": count,
        "counterType": "GAUGE",
        "tags": "place=sisdc,project=mobilecount"
    }
]
box_temp = [
    {
        "endpoint": host_ip,
        "metric": "temp.count",
        "timestamp": host_time,
        "step": 60,
        "value": temp,
        "counterType": "GAUGE",
        "tags": "place=sisdc,project=tempcount"
    }
]
jar_use_count = [
    {
        "endpoint": host_ip,
        "metric": "jar.used.cpu.count",
        "timestamp": host_time,
        "step": 60,
        "value": jar_uescpu,
        "counterType": "GAUGE",
        "tags": "place=sisdc,project=jarcpucount"
    }
]
res = json.dumps(mobile_count)
res1 = json.dumps(box_temp)
res2 = json.dumps(jar_use_count)
http_post(falcon_agent,res)
http_post(falcon_agent,res1)
http_post(falcon_agent,res2)
#print(host_time,data1)
#r = json.dumps(mobile_count)
print(res)
print(res1)
print(res2)
'''
'''
def battery():
    devices_list,count = get_devices()
    try:
        count > 0

    except:
        print("errot!")
'''
