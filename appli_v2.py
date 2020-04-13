#! /usr/bin/python2

import sys
import time
import datetime
import configparser
import os.path
import json
import requests
import RPi.GPIO as GPIO
import lcddriver
import urllib2
import statistics
from hx711 import HX711

config = configparser.ConfigParser()
config.read('applt.cfg')

# thingspeak configurations
myAPI = config["default"]['myAPI']
baseURL = 'https://api.thingspeak.com/update?api_key=%s' % myAPI
myAPI = config["default"]['thingspeak']
print("thinkspeak {}".format(myAPI))
given = 0
eaten = 0 
last = 0
referenceUnit = 1  

# ubidots configurations
TOKEN =  config["default"]['ubidots']
print("ubidots {}".format(TOKEN))
DEVICE_LABEL = "Rasp_Cat"

VARIABLE_LABEL_1 = "bowel"  # Put your first variable label here
VARIABLE_LABEL_2 = "given"  # Put your second variable label here
VARIABLE_LABEL_3 = "eaten"  # Put your second variable label here


flag = datetime.datetime.now().strftime("%Y_%m_%d") # counter for today


def post_request(payload):
    # Creates the headers for the HTTP requests
    url = "http://industrial.api.ubidots.com"
    url = "{}/api/v1.6/devices/{}".format(url, DEVICE_LABEL)
    headers = {"X-Auth-Token": TOKEN, "Content-Type": "application/json"}

    # Makes the HTTP requests
    status = 400
    attempts = 0
    while status >= 400 and attempts <= 5:
        req = requests.post(url=url, headers=headers, json=payload)
        status = req.status_code
        attempts += 1
        time.sleep(1)

    # Processes results
    if status >= 400:
        print("[ERROR] Could not send data after 5 attempts, please check \
            your token credentials and internet connection")
        return False
    print("Status: {}".format(status))
    print("[INFO] request made properly, your device is updated")
    return True


def startup(flag):
        global val, last, given, eaten
        file= "./daily_logs/" + flag
	if os.path.exists(file):
      	    f = open(file) 
            data = f.read()
            print(data)
            data=json.loads(data)
            print(data["Given"])
            eaten = data["Eaten"]
            given = data["Given"]
            last = data["last"]
            print(data["Eaten"])
            print(data["last"])
            print(data)
	else:
      	    print(file)
      	    print("not found")
      	    val = 0
      	    last=0
      	    given=0
      	    eaten=0 


def cleanAndExit():
    print("Cleaning...")

    GPIO.cleanup()
    print("Bye!")
    sys.exit()


def monitor(val, last, eaten, given):
    delta = val - last
    #print(delta)
    
    if (abs(delta) > 0): # filter for the noise...
        if (delta > 2):
            given = given + delta
            print(given)
        elif (delta < 1):
            eaten = eaten - delta
        update_FS()
    return (eaten, given)


def daily_counter(flag):
    
    temp = datetime.datetime.now().strftime("%Y_%m_%d")
    if temp != flag:
        global eaten, given
        flag = temp
        eaten = 0
        given = 0
    return flag


def update_FS():
    payload = {'Eaten': eaten, 'Given': given, 'last':val,'Day': flag}
    f = open("./daily_logs/" + flag, "w")
    json.dump(payload, f)
    f.close()

    return 


hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceUnit)

hx.reset()

lcd = lcddriver.lcd()
counter = 0
startup(flag)
while True:
    try:
        counter = counter -1
	flag = daily_counter(flag)
        # Weight stabilaizer value...
        iterator = 15
        val_row =  []
        for i in range(iterator):
             val_ = hx.get_weight(5)
             val_row.append(val_)
             # print(i)
             # print(val_)
             # print(val_row)
             time.sleep(2)
        val = statistics.median(val_row)

        val = int(round(((val/ 1223.5)-1000)/.786))  #844.5 +123 int()
        val = max(0, val)
        
        print(val)
        print(counter)
        (eaten, given) = monitor(val, last, eaten, given)
        if counter < 1:
            f = urllib2.urlopen(baseURL +
                            "&field1=%s&field2=%s&field3=%s" % (val, abs(eaten), given))
       
            f.read()
            print("f: {}",format(f))
            f.close()
            
 	    payload = {"Bowel": val,  "Eaten": eaten, "Given": given}
            print(payload)
            print("[INFO] Attemping to send data")
            post_request(payload)
            print("[INFO] finished")
            counter = 0

        hx.power_down()
        hx.power_up()
        print("val {}".format(val))
        print("eaten {}".format(eaten))
        print("given {}".format(given))
       
        lcd.lcd_clear()
        lcd.lcd_display_string("Current {} gr".format(val), 1)
        lcd.lcd_display_string("Give {} Eat {}".format(given, abs(eaten)), 2)
       
        time.sleep(10)
        last = val
    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()

