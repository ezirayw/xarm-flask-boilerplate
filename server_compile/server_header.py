import sys, time, datetime, threading, os, json, yaml, serial
import RPi.GPIO as GPIO
from flask import Flask, render_template, request, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import numpy as np


############# FLASK INITIALIZATION CODE ##################

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    "k2": generate_password_hash("pCh3HhLhHyMqw2ZEY6UrXqoM9eU*")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username

config_file = os.path.dirname(os.path.abspath(__file__)) + "/conf.yml"
@app.route('/route_check_status', methods=['POST'])
@auth.login_required
def route_check_status():
    with open(config_file,'r') as config:
        if (yaml.safe_load(config)['status'] != 'ready'):
            return 'busy'
        else:
            return 'ready'

def changeStatus(status):
    with open(config_file,'r') as config:
        current_conf = yaml.safe_load(config)
    current_conf['status'] = status
    with open(config_file,'w') as config:
        yaml.dump(current_conf,config)
    time.sleep(.1)

############### END FLASK INIT ##################


############## SMOOTHIE/PI HAT INITIALIZATION CODE ##################
with open(config_file,'r') as config:
    current_conf = yaml.safe_load(config)
    s = serial.Serial(current_conf['smoothie_port'],115200)
s.write("\r\n\r\n".encode('ascii'))
time.sleep(.2)
s.flushInput()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(29, GPIO.OUT)
GPIO.setup(31, GPIO.OUT)

GPIO.output(29, GPIO.LOW)
time.sleep(.1)
GPIO.output(31, GPIO.LOW)
time.sleep(.1)

############### END SMOOTHIE/PI HAT INIT ##################


############## xARM INITIALIZATION CODE ##################

"""
# xArm-Python-SDK: https://github.com/xArm-Developer/xArm-Python-SDK
# git clone git@github.com:xArm-Developer/xArm-Python-SDK.git
# cd xArm-Python-SDK
# python setup.py install
"""
from xarm import version
from xarm.wrapper import XArmAPI

print('xArm-Python-SDK Version:{}'.format(version.__version__))

arm = XArmAPI('10.241.32.169')
arm.clean_warn()
arm.clean_error()
arm.motion_enable(True)
arm.set_mode(0)
arm.set_state(0)
time.sleep(1)

params = {'speed': 100, 'acc': 2000, 'angle_speed': 20, 'angle_acc': 500, 'events': {}, 'variables': {}, 'quit': False}


# Register error/warn changed callback
def error_warn_change_callback(data):
    if data and data['error_code'] != 0:
        arm.set_state(4)
        params['quit'] = True
        print('err={}, quit'.format(data['error_code']))
        arm.release_error_warn_changed_callback(error_warn_change_callback)
arm.register_error_warn_changed_callback(error_warn_change_callback)


# Register state changed callback
def state_changed_callback(data):
    if data and data['state'] == 4:
        if arm.version_number[0] >= 1 and arm.version_number[1] >= 1 and arm.version_number[2] > 0:
            params['quit'] = True
            print('state=4, quit')
            arm.release_state_changed_callback(state_changed_callback)
arm.register_state_changed_callback(state_changed_callback)


# Register counter value changed callback
if hasattr(arm, 'register_count_changed_callback'):
    def count_changed_callback(data):
        print('counter val: {}'.format(data['count']))
    arm.register_count_changed_callback(count_changed_callback)

############### END xARM INIT ##################
