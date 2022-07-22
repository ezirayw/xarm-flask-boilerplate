import sys, time, datetime, threading, os, json, serial
import yaml
from flask import Flask, render_template, request, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import numpy as np
import aiohttp
import asyncio
import requests
import shutil

############# FLASK INITIALIZATION CODE ##################

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    "k2": generate_password_hash("pCh3HhLhHyMqw2ZEY6UrXqoM9eU*")
}

# get settings from yaml file to setup server
SERVER_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SERVER_PATH, 'server_conf.yml')
DILUTIONS_PATH = os.path.join(SERVER_PATH)
CALIBRATION_PATH = os.path.join(SERVER_PATH, 'calibrations.json')

with open(CONFIG_PATH,'r') as config:
    settings = yaml.safe_load(config)
XARM_IP = settings['xarm_ip']
RPI_IP = settings['rpi_ip']
API_KEY = settings['octoprint_api_key']
BASE_OCTOPRINT_PATH = settings['base_octoprint_path']
PUMP_SETTINGS = settings['pump_settings']

# create urls for each octoprint server instance (1 per syringe pump)
# create necessary gcode directories for each syringe pump
OCTOPRINT_URLS = {}
for smoothie in PUMP_SETTINGS['smoothies']:
    url = "http://" + RPI_IP + str(PUMP_SETTINGS['smoothies'][smoothie]['port'])
    OCTOPRINT_URLS[smoothie] = url
    gcode_dir_exist = os.path.exists(PUMP_SETTINGS['smoothies'][smoothie]['gcode_path'])
    if gcode_dir_exist:
        shutil.rmtree(PUMP_SETTINGS['smoothies'][smoothie]['gcode_path'])
    os.makedirs(PUMP_SETTINGS['smoothies'][smoothie]['gcode_path'])

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username

@app.route('/route_check_status', methods=['POST'])
@auth.login_required
def route_check_status():
    with open(CONFIG_PATH,'r') as config:
        if (yaml.safe_load(config)['arm_status'] != 'ready'):
            return 'busy'
        else:
            return 'ready'

############### END FLASK INIT ##################
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

arm = XArmAPI(XARM_IP)
arm.clean_warn()
arm.clean_error()
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(state=0)
arm.reset(wait=True)

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
