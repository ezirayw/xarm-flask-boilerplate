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
def quad_1_location():
    print('Running ' + 'quad_1_location' + '...')    
    
    # Register connect changed callback
    def connect_changed_callback(data):
        if data and not data['connected']:
            params['quit'] = True
            pprint('disconnect, connected={}, reported={}, quit'.format(data['connected'], data['reported']))
            arm.release_connect_changed_callback(error_warn_change_callback)
    arm.register_connect_changed_callback(connect_changed_callback)
    
    if not params['quit']:
        params['speed'] = 5
    if not params['quit']:
        params['acc'] = 100
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_servo_angle(angle=[-81.9, -4.2, -63.8, 68.0, -180.0], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=None)
        if code != 0:
            params['quit'] = True
            pprint('set_servo_angle, code={}'.format(code))
    
    # release all event
    if hasattr(arm, 'release_count_changed_callback'):
        arm.release_count_changed_callback(count_changed_callback)

def above_to_zero():
    print('Running ' + 'above_to_zero' + '...')    
    
    # Register connect changed callback
    def connect_changed_callback(data):
        if data and not data['connected']:
            params['quit'] = True
            pprint('disconnect, connected={}, reported={}, quit'.format(data['connected'], data['reported']))
            arm.release_connect_changed_callback(error_warn_change_callback)
    arm.register_connect_changed_callback(connect_changed_callback)
    
    if not params['quit']:
        params['speed'] = 5
    if not params['quit']:
        params['acc'] = 1
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_servo_angle(angle=[-81.2, -27.8, -60.9, 88.8, -81.2], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=20.0)
        if code != 0:
            params['quit'] = True
            pprint('set_servo_angle, code={}'.format(code))
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_servo_angle(angle=[0.0, -53.0, -46.1, 99.1, 0.0], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=20.0)
        if code != 0:
            params['quit'] = True
            pprint('set_servo_angle, code={}'.format(code))
    if arm.error_code == 0 and not params['quit']:
        arm.reset()
    
    # release all event
    if hasattr(arm, 'release_count_changed_callback'):
        arm.release_count_changed_callback(count_changed_callback)

def quad_2_location():
    print('Running ' + 'quad_2_location' + '...')    
    
    # Register connect changed callback
    def connect_changed_callback(data):
        if data and not data['connected']:
            params['quit'] = True
            pprint('disconnect, connected={}, reported={}, quit'.format(data['connected'], data['reported']))
            arm.release_connect_changed_callback(error_warn_change_callback)
    arm.register_connect_changed_callback(connect_changed_callback)
    
    if not params['quit']:
        params['speed'] = 5
    if not params['quit']:
        params['acc'] = 100
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_servo_angle(angle=[-100.7, -3.7, -64.3, 68.0, 0.0], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=None)
        if code != 0:
            params['quit'] = True
            pprint('set_servo_angle, code={}'.format(code))
    
    # release all event
    if hasattr(arm, 'release_count_changed_callback'):
        arm.release_count_changed_callback(count_changed_callback)

def enter_vial_80():
    print('Running ' + 'enter_vial_80' + '...')    
    
    # Register connect changed callback
    def connect_changed_callback(data):
        if data and not data['connected']:
            params['quit'] = True
            pprint('disconnect, connected={}, reported={}, quit'.format(data['connected'], data['reported']))
            arm.release_connect_changed_callback(error_warn_change_callback)
    arm.register_connect_changed_callback(connect_changed_callback)
    
    if not params['quit']:
        params['speed'] = 50
    if not params['quit']:
        params['acc'] = 25
    if not params['quit']:
        params['variables']['x_loc_1'] = 83.3
    if not params['quit']:
        params['variables']['x_loc_2'] = 78
    if not params['quit']:
        params['variables']['y_loc'] = -322.9
    if not params['quit']:
        params['variables']['z_loc_1'] = 450.4
    if not params['quit']:
        params['variables']['z_loc_2'] = 424.3
    for i in range(int(3)):
        if params['quit']:
            break
        for i in range(int(7)):
            if params['quit']:
                break
            for i in range(int(1)):
                if params['quit']:
                    break
                if arm.error_code == 0 and not params['quit']:
                    code = arm.set_position(*[params['variables'].get('x_loc_1', 0),params['variables'].get('y_loc', 0),params['variables'].get('z_loc_1', 0),180,0,0], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
                    if code != 0:
                        params['quit'] = True
                        pprint('set_position, code={}'.format(code))
                if arm.error_code == 0 and not params['quit']:
                    code = arm.set_position(*[params['variables'].get('x_loc_2', 0),params['variables'].get('y_loc', 0),params['variables'].get('z_loc_2', 0),180,0,0], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
                    if code != 0:
                        params['quit'] = True
                        pprint('set_position, code={}'.format(code))
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_position(*[params['variables'].get('x_loc_1', 0),params['variables'].get('y_loc', 0),params['variables'].get('z_loc_1', 0),180,0,0.1], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_position, code={}'.format(code))
            if not params['quit']:
                params['variables']['y_loc'] += 18
            if arm.error_code == 0 and not params['quit']:
                code = arm.set_position(*[params['variables'].get('x_loc_1', 0),params['variables'].get('y_loc', 0),params['variables'].get('z_loc_1', 0),180,0,0.1], speed=params['speed'], mvacc=params['acc'], radius=-1, wait=True)
                if code != 0:
                    params['quit'] = True
                    pprint('set_position, code={}'.format(code))
        if not params['quit']:
            params['variables']['y_loc'] += -108
        if not params['quit']:
            params['variables']['x_loc_1'] += 18
        if not params['quit']:
            params['variables']['x_loc_2'] += 18
    
    # release all event
    if hasattr(arm, 'release_count_changed_callback'):
        arm.release_count_changed_callback(count_changed_callback)

def quad_0_location():
    print('Running ' + 'quad_0_location' + '...')    
    
    # Register connect changed callback
    def connect_changed_callback(data):
        if data and not data['connected']:
            params['quit'] = True
            pprint('disconnect, connected={}, reported={}, quit'.format(data['connected'], data['reported']))
            arm.release_connect_changed_callback(error_warn_change_callback)
    arm.register_connect_changed_callback(connect_changed_callback)
    
    if not params['quit']:
        params['speed'] = 5
    if not params['quit']:
        params['acc'] = 100
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_servo_angle(angle=[-77.5, -36.0, -36.3, 72.3, -180.0], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=None)
        if code != 0:
            params['quit'] = True
            pprint('set_servo_angle, code={}'.format(code))
    
    # release all event
    if hasattr(arm, 'release_count_changed_callback'):
        arm.release_count_changed_callback(count_changed_callback)

def enter_vial():
    print('Running ' + 'enter_vial' + '...')    
    
    # Register connect changed callback
    def connect_changed_callback(data):
        if data and not data['connected']:
            params['quit'] = True
            pprint('disconnect, connected={}, reported={}, quit'.format(data['connected'], data['reported']))
            arm.release_connect_changed_callback(error_warn_change_callback)
    arm.register_connect_changed_callback(connect_changed_callback)
    
    if not params['quit']:
        params['speed'] = 10
    if not params['quit']:
        params['angle_speed'] = 1
    if not params['quit']:
        params['acc'] = 1
    if not params['quit']:
        params['angle_acc'] = 1
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_servo_angle(angle=[18.2, -9.1, -22.6, 31.7, 18.2], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=-1.0)
        if code != 0:
            params['quit'] = True
            pprint('set_servo_angle, code={}'.format(code))
    for i in range(int(8)):
        if params['quit']:
            break
        if arm.error_code == 0 and not params['quit']:
            code = arm.set_position(x=-1, speed=params['speed'], mvacc=params['acc'], relative=True, wait=True)
            if code != 0:
                params['quit'] = True
                pprint('set_position, code={}'.format(code))
        if arm.error_code == 0 and not params['quit']:
            code = arm.set_position(z=-3.5, speed=params['speed'], mvacc=params['acc'], relative=True, wait=True)
            if code != 0:
                params['quit'] = True
                pprint('set_position, code={}'.format(code))
    
    # release all event
    if hasattr(arm, 'release_count_changed_callback'):
        arm.release_count_changed_callback(count_changed_callback)

def quad_3_location():
    print('Running ' + 'quad_3_location' + '...')    
    
    # Register connect changed callback
    def connect_changed_callback(data):
        if data and not data['connected']:
            params['quit'] = True
            pprint('disconnect, connected={}, reported={}, quit'.format(data['connected'], data['reported']))
            arm.release_connect_changed_callback(error_warn_change_callback)
    arm.register_connect_changed_callback(connect_changed_callback)
    
    if not params['quit']:
        params['speed'] = 5
    if not params['quit']:
        params['acc'] = 100
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_servo_angle(angle=[-106.2, -35.4, -36.8, 72.2, -180.0], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=None)
        if code != 0:
            params['quit'] = True
            pprint('set_servo_angle, code={}'.format(code))
    
    # release all event
    if hasattr(arm, 'release_count_changed_callback'):
        arm.release_count_changed_callback(count_changed_callback)

def above_evolver():
    print('Running ' + 'above_evolver' + '...')    
    
    # Register connect changed callback
    def connect_changed_callback(data):
        if data and not data['connected']:
            params['quit'] = True
            pprint('disconnect, connected={}, reported={}, quit'.format(data['connected'], data['reported']))
            arm.release_connect_changed_callback(error_warn_change_callback)
    arm.register_connect_changed_callback(connect_changed_callback)
    
    if not params['quit']:
        params['acc'] = 10
    if not params['quit']:
        params['speed'] = 5
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_servo_angle(angle=[0.0, -53.0, -46.1, 99.1, 0.0], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=False, radius=20.0)
        if code != 0:
            params['quit'] = True
            pprint('set_servo_angle, code={}'.format(code))
    if arm.error_code == 0 and not params['quit']:
        code = arm.set_servo_angle(angle=[-81.2, -27.8, -60.9, 88.8, -81.2], speed=params['angle_speed'], mvacc=params['angle_acc'], wait=True, radius=20.0)
        if code != 0:
            params['quit'] = True
            pprint('set_servo_angle, code={}'.format(code))
    
    # release all event
    if hasattr(arm, 'release_count_changed_callback'):
        arm.release_count_changed_callback(count_changed_callback)

## This script is to define smoothieboard related functions, such as priming fluidic lines or dispensing volumes into vials
def convert_to_steps(volume, test=False):
    if test:
        return 0
    else:
        return 100

def write_gcode(mode, instructions, gcode='', gcode_path=''):
    """ Write gcode file for dispensing volumes into vials """
    # use motor connection settings from config to map pump instructions to proper smoothieboards
    smoothie_instructions_map = {}
    for smoothie in PUMP_SETTINGS['smoothies']:
        smoothie_instructions = {}
        for pump_target in instructions:
            if pump_target in PUMP_SETTINGS['pumps'] and PUMP_SETTINGS['pumps'][pump_target]['smoothie'] == smoothie:
                smoothie_instructions[pump_target] = instructions[pump_target]
        smoothie_instructions_map[smoothie] = smoothie_instructions

    for smoothie in smoothie_instructions_map:
        plunger_in_commands = ['' , '']
        plunger_out_commands = ['' , '']
        prime_commands = ['' , '']
        valve_commands = {'on': ['' , ''] , 'off': ['', ''], 'steps': 0 }
        count = 0

        if mode == "fill_tubing_in" or mode == 'volume_in':
            for pump in smoothie_instructions_map[smoothie]:
                # get pump port settings
                plunger = PUMP_SETTINGS['pumps'][pump]['motor_connections']['plunger']
                plunger_in_commands[count] = '{0}{1}'.format(plunger, smoothie_instructions_map[smoothie][pump])
                count = count + 1

            # combine gcode commands
            command = plunger_in_commands[0] + ' ' + plunger_in_commands[1]
            gcode = "G91\nG1 {0} F15000\nM18".format(command)

        if mode == "fill_tubing_out" or mode =='volume_out':
            for pump in smoothie_instructions_map[smoothie]:
                plunger = PUMP_SETTINGS['pumps'][pump]['motor_connections']['plunger']
                valve = PUMP_SETTINGS['pumps'][pump]['motor_connections']['valve']
                valve_steps_on = PUMP_SETTINGS['pumps'][pump]['motor_connections']['valve_steps']
                valve_steps_off = PUMP_SETTINGS['pumps'][pump]['motor_connections']['valve_steps'] * -1

                if mode == "fill_tubing_out":
                    plunger_out_commands[count] = '{0}-{1}'.format(plunger, smoothie_instructions_map[smoothie][pump])
                if mode == "volume_out":
                    plunger_out_commands[count] = '{0}-{1}'.format(plunger, smoothie_instructions_map[smoothie][pump] + PUMP_SETTINGS['priming_steps'])
                prime_commands[count] = '{0}{1}'.format(plunger, PUMP_SETTINGS['priming_steps'])
                valve_commands['on'][count] = '{0}{1}'.format(valve, valve_steps_on)
                valve_commands['off'][count] = '{0}{1}'.format(valve, valve_steps_off)
                count = count + 1

            # combine gcode commands
            valve_on = valve_commands['on'][0] + ' ' + valve_commands['on'][1]
            valve_off = valve_commands['off'][0] + ' ' + valve_commands['off'][1]
            plunger_out = plunger_out_commands[0] + ' ' + plunger_out_commands[1]
            prime_out = prime_commands[0] + ' ' + prime_commands[1]

            if mode == "fill_tubing_out":
                gcode = "G91\nG1 {0} F20000\nG1 {1} F15000\nG1 {2} F20000\nM18".format(valve_on, plunger_out, valve_off)
            if mode == "volume_out":
                gcode = "G91\nG1 {0} F20000\nG1 {1} F15000\nG4 P100\nG1 {2} F20000\nG1 {3} F20000\nM18".format(valve_on, plunger_out, prime_out, valve_off)

        if mode == "prime_pumps":
            for pump in smoothie_instructions_map[smoothie]:
                plunger = PUMP_SETTINGS['pumps'][pump]['motor_connections']['plunger']
                valve = PUMP_SETTINGS['pumps'][pump]['motor_connections']['valve']
                valve_steps_on = PUMP_SETTINGS['pumps'][pump]['motor_connections']['valve_steps']
                valve_steps_off = PUMP_SETTINGS['pumps'][pump]['motor_connections']['valve_steps'] * -1

                plunger_in_commands[count] = '{0}{1}'.format(plunger, smoothie_instructions_map[smoothie][pump])
                valve_commands['on'][count] = '{0}{1}'.format(valve, valve_steps_on)
                valve_commands['off'][count] = '{0}{1}'.format(valve, valve_steps_off)
                count = count + 1

            # combine gcode commands
            plunger_in = plunger_in_commands[0] + ' ' + plunger_in_commands[1]
            valve_on = valve_commands['on'][0] + ' ' + valve_commands['on'][1]
            valve_off = valve_commands['off'][0] + ' ' + valve_commands['off'][1]

            gcode = 'G91\nG1 {0} F20000\nG1 {1} F15000\nG1 {2} F20000\nM18'.format(valve_on, plunger_in_commands, valve_off)
        else:
            gcode = gcode

        # write command to gcode file
        filename = mode + '.gcode'
        gcode_path = os.path.join(PUMP_SETTINGS['smoothies'][smoothie]['gcode_path'], filename)
        f = open(gcode_path, 'w')
        f.write(gcode)
        f.close()

def media_transform(fluid_command, test=False):
    """ Convert fluid_command from eVOLVER server to pump motor steps for vial dilutions. Information will be stored in an read accessible JSON file """
    dilutions = {}

    # scan through fluid command and convert dilution volumes to stepper motor steps based on volume --> steps calibration
    for pump in fluid_command:
        pump_json = {}

        for quad in range(len(fluid_command[pump])):
            quad_name = 'quad_{0}'.format(quad)
            pump_json[quad_name] = {}

            for vial in range(18):
                vial_name = 'vial_{0}'.format(vial)
                pump_json[quad_name][vial_name] = convert_to_steps(fluid_command[pump][quad][vial], test)
        dilutions[pump] = pump_json

    # save dilutiion steps to JSON
    dilutions_path = os.path.join(DILUTIONS_PATH, 'dilutions.json')
    with open(dilutions_path, 'w') as f:
        json.dump(dilutions, f)
    return dilutions

async def post_gcode_async(session, gcode_path, smoothie):
    """ Return response status of POST request to Ocotprint server for actuating syringe pump """
    payload = {'file': open(gcode_path, 'rb'), 'print':'true'}

    # get url for target smoothie server and make API request to send gcode file to actuate pumps
    url = OCTOPRINT_URLS[smoothie] + '/api/files/local'
    header={'X-Api-Key': API_KEY }
    try:
        async with session.post(url, headers=header, data=payload) as response:
            return await response.json()
    except aiohttp.ClientError as e:
        return 'retry'
    else:
        return 'post_gcode_async error'

async def check_job(session, smoothie):
    """ Return completion status of syringe pump actuation via GET request to Ocotprint server """
    # get url for target smoothie server and make API request to get pump status information
    url = OCTOPRINT_URLS[smoothie] + '/api/job'
    header={'X-Api-Key': API_KEY }
    try:
        async with session.get(url, headers=header) as response:
            return await response.json()
    except Exception as e:
        return 'check_job error'

async def check_status(session, gcode_paths):
    """ Return completion status of desired pump actuation event based on gcode path given. Returns True if desired pump(s) are ready for new actuation event, False if not """
    status_tasks = []
    for gcode_path in gcode_paths:
        # map gcode file to cognate smoothie
        gcode_parent_path = os.path.split(gcode_path)[0]
        for smoothie in PUMP_SETTINGS['smoothies']:
            if PUMP_SETTINGS['smoothies'][smoothie]['gcode_path'] == gcode_parent_path:
                status_tasks.append(check_job(session, smoothie))
                break

    # use check_job() to get status information on desired pump(s) by parsing JSON data
    try:
        status_results = await asyncio.gather(*status_tasks)
        status_complete = 0
        for i in range(len(gcode_paths)):
            filename = os.path.split(gcode_paths[i])[1]
            if (status_results[i]['progress']['completion'] >= 100) and (status_results[i]['state'] == 'Operational') and (status_results[i]['job']['file']['name'] == filename):
                status_complete = status_complete + 1
        if status_complete == len(gcode_paths):
            return True
        else:
            return False

    except Exception as e:
        #print('error checking pump status')
        return False

async def prime_pumps_helper():
    """ Call this function to prime pumps after filling tubing """
    session = aiohttp.ClientSession()

    # get fluid pumps from server_conf and write prime pumps instructions
    instructions = {}
    print_string = ''

    for pump in PUMP_SETTINGS['pumps']:
        if PUMP_SETTINGS['pumps'][pump]['type'] == 'fluid':
            print_string = print_string + '{0} pump'.format(pump)
            instructions[pump] = PUMP_SETTINGS['priming_steps']
    write_gcode('prime_pumps', instructions)

    # create tasks for prime pump events
    try:
        prime_pumps_tasks = [None] * PUMP_SETTINGS['smoothie_num']
        check_files = [None] * PUMP_SETTINGS['smoothie_num']
        prime_pumps_results = []
        while True:
            for smoothie in range(PUMP_SETTINGS['smoothie_num']):
                gcode_path = os.path.join(PUMP_SETTINGS['smoothies'][smoothie]['gcode_path'], 'prime_pumps.gcode')
                prime_pumps_tasks[smoothie] = post_gcode_async(session, gcode_path, smoothie)
                check_files[smoothie] = gcode_path

            prime_pumps_results = await asyncio.gather(*prime_pumps_tasks)
            if 'retry' in prime_pumps_results:
                pass
            else:
                break
        print('priming {0}'.format(print_string), file=sys.stdout, flush=True)

    except Exception as e:
        #print('error priming pumps', file=sys.stdout, flush=True)
        await session.close()
        return 'error filling out tubing'

    # verify that robotic pipette has executed fill out events
    tasks_complete_prime_pumps = 0
    for result in prime_pumps_results:
        if result['done'] == True:
            tasks_complete_prime_pumps = tasks_complete_prime_pumps + 1

    # check status of pumps before priming pumps
    if prime_pumps_tasks == len(prime_pumps_tasks):
        while True:
            check = await check_status(session, check_files)
            if check:
                break
            else:
                pass
        await session.close()
        return 'priming pumps success'
    else:
        #print('prime_pumps tasks not completed'.format(print_string), file=sys.stdout, flush=True)
        await session.close()
        return 'prime_pumps tasks not completed {0}'.format(print_string)


async def fill_tubing_helper():
    """ Call this function to fill tubing lines for all pumps that are in fluid mode (check/update server_conf.yml to set modes for pumps) """
    # start asyncio Client Session
    session = aiohttp.ClientSession()

    # get fluid pumps from server_conf
    instructions = {}
    print_string = ''

    for pump in PUMP_SETTINGS['pumps']:
        if PUMP_SETTINGS['pumps'][pump]['type'] == 'fluid':
            print_string = print_string + '{0} pump '.format(pump)
            instructions[pump] = 300
    write_gcode('fill_tubing_in', instructions)
    write_gcode('fill_tubing_out', instructions)

    # create tasks for fill_tubing input events
    try:
        check_files = [None] * PUMP_SETTINGS['smoothie_num']
        fill_in_tasks = [None] * PUMP_SETTINGS['smoothie_num']
        fill_in_results = []
        while True:
            for smoothie in range(PUMP_SETTINGS['smoothie_num']):
                gcode_path = os.path.join(PUMP_SETTINGS['smoothies'][smoothie]['gcode_path'], 'fill_tubing_in.gcode')
                fill_in_tasks[smoothie] = post_gcode_async(session, gcode_path, smoothie)
                check_files[smoothie] = gcode_path
            fill_in_results = await asyncio.gather(*fill_in_tasks)
            if fill_in_results[0] == 'retry':
                pass
            else:
                break
        print('filling in tubing for {0}'.format(print_string), file=sys.stdout, flush=True)

    except Exception as e:
        print('error filling in tubing', file=sys.stdout, flush=True)
        await session.close()
        return 'error filling in tubing'

    # verify that robotic pipette has executed input events
    tasks_complete_fill_in = 0
    for result in fill_in_results:
        if result['done'] == True:
            tasks_complete_fill_in = tasks_complete_fill_in + 1

    # check status of pumps before moving to fill out events
    if tasks_complete_fill_in == len(fill_in_tasks):
        while True:
            check = await check_status(session, check_files)
            if check:
                break
            else:
                pass

        # create tasks for fill out events
        try:
            fill_out_tasks = [None] * PUMP_SETTINGS['smoothie_num']
            check_files = [None] * PUMP_SETTINGS['smoothie_num']
            fill_out_results = []
            while True:
                for smoothie in range(PUMP_SETTINGS['smoothie_num']):
                    gcode_path = os.path.join(PUMP_SETTINGS['smoothies'][smoothie]['gcode_path'], 'fill_tubing_out.gcode')
                    fill_out_tasks[smoothie] = post_gcode_async(session, gcode_path, smoothie)
                    check_files[smoothie] = gcode_path

                fill_out_results = await asyncio.gather(*fill_out_tasks)
                if fill_out_results[0] == 'retry':
                    pass
                else:
                    break
            print('filling out tubing for {0}'.format(print_string), file=sys.stdout, flush=True)

        except Exception as e:
            print('error filling out tubing', file=sys.stdout, flush=True)
            await session.close()
            return 'error filling out tubing'

        # verify that robotic pipette has executed fill out events
        tasks_complete_fill_out = 0
        for result in fill_out_results:
            if result['done'] == True:
                tasks_complete_fill_out = tasks_complete_fill_out + 1

        # check status of pumps before priming pumps
        if tasks_complete_fill_out == len(fill_out_tasks):
            while True:
                check = await check_status(session, check_files)
                if check:
                    break
                else:
                    pass
        else:
            print('cant validate that filling out tasks for {0} were comleted'.format(print_string), file=sys.stdout, flush=True)
            await session.close()
            return 'cant validate that filling out tasks for {0} were completed'.format(print_string)
    else:
        print('cant validate that filling in tasks for {0} were comleted'.format(print_string), file=sys.stdout, flush=True)
        await session.close()
        return 'cant validate that filling in tasks for {0} were comleted'.format(print_string)

    await session.close()
    return 'fill tubing cycle success'

async def influx_helper(fluid_command, quads, test=False):
    """ Main method for dilution routine for specified quads. Called every time eVOLVER client sends fluid_command to fluidics server """
    # start asyncio Client Session
    session = aiohttp.ClientSession()

    # get vial coordinates from calibrations
    f1 = open(CALIBRATION_PATH)
    coordinate_config = json.load(f1)
    f1.close()

    # get dilution steps for fluid command
    test = bool(test)
    dilutions = media_transform(fluid_command, test)

    # loop through vials and execute fluidic events
    for quad in quads:
        quad_name = 'quad_{0}'.format(quad)

        # create data structure to map fluidic events
        vial_map = [[0,1,2,3,4,5], [11,10,9,8,7,6], [12,13,14,15,16,17]]
        change_row = False

        for row_num in range(len(vial_map)):
            row = vial_map[row_num]

            # get list of pumps from server_conf.yml
            pump_map = []
            for pump_id in range(PUMP_SETTINGS['pump_num']):
                for pump in PUMP_SETTINGS['pumps']:
                    if PUMP_SETTINGS['pumps'][pump]['id'] == pump_id:
                        pump_map.append(pump)
                        break

            if row_num % 2 > 0:
                pump_map.reverse()

            # number of fluidic events based on number of pumps
            number_events = 6 + (PUMP_SETTINGS['pump_num'] - 1)
            active_vials = []
            active_pumps = []


            for event_num in range(number_events):

                # get list of vials and active pumps for current fluidic event
                if event_num < PUMP_SETTINGS['pump_num']:
                    active_vials.append(row[event_num])
                    active_pumps.append(pump_map[event_num])
                if event_num >= PUMP_SETTINGS['pump_num']:
                    active_vials.pop(0)
                    if event_num < len(row):
                        active_vials.append(row[event_num])
                    if event_num >= len(row):
                        active_pumps.pop(0)

                print('active vials for fluidic event {0} are:{1}'.format(event_num, active_vials), file=sys.stdout, flush=True)
                print('active pumps for fluidic event {0} are:{1}'.format(event_num, active_pumps), file=sys.stdout, flush=True)

                # using dilutions data strcuture, write gcode files to handle dilution events for active vials
                instructions = {}
                for i in range(len(active_vials)):
                    # for current vial, get cogante pump and steps
                    active_vial_name = 'vial_{0}'.format(active_vials[i])
                    active_vial = active_vials[i]
                    active_pump = active_pumps[i]
                    pump_steps = dilutions[active_pump][quad_name][active_vial_name]
                    instructions[active_pump] = pump_steps
                write_gcode('volume_in', instructions)
                write_gcode('volume_out', instructions)

                # get gcode files for active vials
                print_string = ''
                for i in range(len(active_vials)):
                    print_string = print_string + 'vial_{0} '.format(active_vials[i])
                print_string = print_string + 'in quad_{0}'.format(quad)

                # create tasks for fluidic input events
                try:
                    fluidic_results = []
                    skip = False
                    arm_move_result = []
                    while True:
                        fluidic_tasks = []
                        check_files = []
                        for smoothie in range(PUMP_SETTINGS['smoothie_num']):
                            gcode_path = os.path.join(PUMP_SETTINGS['smoothies'][smoothie]['gcode_path'], 'volume_in.gcode')
                            fluidic_tasks.append(post_gcode_async(session, gcode_path, smoothie))
                            check_files.append(gcode_path)
                        if skip == False:
                            fluidic_tasks.append(pipette_next_step(row_num, quad_name, change_row, coordinate_config))

                        fluidic_results = await asyncio.gather(*fluidic_tasks)
                        if 'retry' in fluidic_results:
                            if fluidic_results[-1][0] == 'arm_moved':
                                skip = True
                                arm_move_result = fluidic_results[-1]
                            time.sleep(0.1)
                            continue
                        else:
                            if skip:
                                fluidic_results.append(arm_move_result)
                            break
                    print('pumping in dilution volume for: {0}'.format(print_string), file=sys.stdout, flush=True)

                except Exception as e:
                    print('error pumping in dilution volume', file=sys.stdout, flush=True)
                    print(e, file=sys.stdout, flush=True)
                    await session.close()
                    return e

                # verify that robotic pipette has executed input events and update arm coordinate configurations
                tasks_complete = 0
                if fluidic_results[-1][0] == 'arm_moved':
                    tasks_complete = tasks_complete + 1
                    coordinate_config = fluidic_results[-1][1]
                for result in fluidic_results[0:-1]:
                    if result['done'] == True:
                        tasks_complete = tasks_complete + 1

                # check status of pumps before moving to dilution events
                if tasks_complete == len(fluidic_results):
                    while True:
                        check = await check_status(session, check_files)
                        if check:
                            break
                        else:
                            pass

                    # create tasks for fluidic output events
                    try:
                        fluidic_results = []
                        while True:
                            fluidic_tasks = []
                            check_files = []
                            for smoothie in range(PUMP_SETTINGS['smoothie_num']):
                                gcode_path = os.path.join(PUMP_SETTINGS['smoothies'][smoothie]['gcode_path'], 'volume_out.gcode')
                                fluidic_tasks.append(post_gcode_async(session, gcode_path, smoothie))
                                check_files.append(gcode_path)
                            fluidic_results = await asyncio.gather(*fluidic_tasks)
                            if 'retry' in fluidic_results:
                                time.sleep(0.1)
                                continue
                            else:
                                break
                        print('pumping out dilution volume for: {0}'.format(print_string), file=sys.stdout, flush=True)

                    except Exception as e:
                        print('error pumping out dilution volume', file=sys.stdout, flush=True)
                        #print(e, file=sys.stdout, flush=True)
                        await session.close()
                        return e

                    # verify that arm has pumped in volume
                    tasks_complete = 0
                    for result in fluidic_results:
                        if result['done'] == True:
                            tasks_complete = tasks_complete + 1

                    # check status of pumps before moving to dilution events
                    if tasks_complete == len(fluidic_results):
                        while True:
                            check = await check_status(session, check_files)
                            if check:
                                break
                            else:
                                pass
                        print('finished dilution routine for: {0}'.format(print_string), file=sys.stdout, flush=True)


                    else:
                        print('cant validate that dilution volumes were pumped out for: {0}'.format(print_string), file=sys.stdout, flush=True)
                        await session.close()
                        return 'cant validate that dilution volumes were pumped out for: {0}'.format(print_string)
                else:
                    print('cant validate that dilution volumes were pumped in or that arm was moved to proper location for: {0}'.format(print_string), file=sys.stdout, flush=True)
                    await session.close()
                    return 'cant validate that dilution volumes were pumped in and arm moved to proper location for: {0}'.format(print_string)

                # end of fluidic event
                change_row = False

            # reached end of row, increment arm coordinates to change row
            change_row = True

        # reached end of fluidic events for quad, move arm up before moving to next quad
        coordinates = {'x': coordinate_config[quad_name]['x_out'], 'y': coordinate_config[quad_name]['y'], 'z': coordinate_config[quad_name]['z_out']}
        await move_arm(coordinates, True)
    await session.close()
    return 'dilution routine success'
## ## This script is to define xarm related functions that are not covered by auto-generated blockly functions. Useful for more precise movements.
async def move_arm(coordinates, wait):
    """ Return string indicating that arm was moved to specified XYZ location in space """
    x = coordinates['x']
    y = coordinates['y']
    z = coordinates['z']

    with open(CONFIG_PATH,'r') as config:
        USER_PARAMS = yaml.safe_load(config)['xarm_params']


    # move xARM to specified coordinates
    try:
        if arm.error_code == 0 and not params['quit']:
            await asyncio.sleep(0.5)
            return arm.set_position(x=x, y=y, z=z, roll=USER_PARAMS['roll'], pitch=USER_PARAMS['pitch'], yaw=USER_PARAMS['yaw'], speed=USER_PARAMS['speed'], mvacc=USER_PARAMS['mvacc'], wait=wait)
    except:
        print('error moving arm', file=sys.stderr)
        return 'error moving arm'


async def pipette_next_step(row_num, quad_name, change_row, coordinate_config):
    arm_location = {}
    part1 = None
    part2 = None

    # move arm up
    arm_location['x'] = coordinate_config[quad_name]['x_out']
    arm_location['y'] = coordinate_config[quad_name]['y']
    arm_location['z'] = coordinate_config[quad_name]['z_out']
    part1 = await move_arm(arm_location, False)

    if part1 == 0:
        # move arm above next set of active_vials
        if change_row:
            coordinate_config[quad_name]['x_in'] = coordinate_config[quad_name]['x_in'] + 18
            coordinate_config[quad_name]['x_out'] = coordinate_config[quad_name]['x_out'] + 18
            arm_location['x'] = coordinate_config[quad_name]['x_out']
            part2 = await move_arm(arm_location, False)
        else:
            if row_num % 2 == 0:
                coordinate_config[quad_name]['y'] = coordinate_config[quad_name]['y'] + 18
                arm_location['y'] = coordinate_config[quad_name]['y']
            else:
                coordinate_config[quad_name]['y'] = coordinate_config[quad_name]['y'] - 18
                arm_location['y'] = coordinate_config[quad_name]['y']
            part2 = await move_arm(arm_location, False)

        if part2 == 0:
            # move arm down into next set of active_vials
            arm_location['x'] = coordinate_config[quad_name]['x_in']
            arm_location['z'] = coordinate_config[quad_name]['z_in']
            await move_arm(arm_location, True)

    return ['arm_moved', coordinate_config]
## This script is to define all API calls to the flask server. Ensure that functions called in routes exist are pulled ./functions or ./manual

# #########################   Example Scripts ####################################
# #########################   End of Example Scripts ####################################


@app.route('/arm_test', methods=['POST'])
@auth.login_required
def arm_test():
    above_evolver()
    above_to_zero()
    return 'arm_test success'

@app.route('/set_arm', methods=['POST'])
@auth.login_required
def set_arm():
    above_evolver()
    time.sleep(1)
    return 'set_arm success'

@app.route('/reset_arm', methods=['POST'])
@auth.login_required
def reset_arm():
    above_to_zero()
    time.sleep(1)
    return 'reset_arm success'

@app.route('/move_to_quad', methods=['POST'])
@auth.login_required
def move_to_quad():
    quad = request.json['quad']
    if quad == 0:
        print('moving to smart quad 0')
        quad_0_location()
    if quad == 1:
        print('moving to smart quad 1')
        quad_1_location()
    if quad == 2:
        print('moving to smart quad 2')
        quad_2_location()
    if quad == 3:
        print('moving to smart quad 3')
        quad_3_location()
    time.sleep(1)
    return 'move_to_quad success'

@app.route('/fill_tubing', methods=['POST'])
@auth.login_required
def fill_tubing():
    """ Perform fluidic influx for target vial. Pump in and dispense dilution volume """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(fill_tubing_helper())
    return 'fill tubing cycle success'

@app.route('/prime_pump', methods=['POST'])
@auth.login_required
def prime_pump():
    """ Prime pump after filling lines """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(prime_pumps_helper())
    return 'prime_pump success'

@app.route('/influx', methods=['POST'])
@auth.login_required
def influx():
    """ Perform fluidic influx for target vial. Pump in and dispense dilution volume """
    fluid_command = request.json['fluid_command']
    quads = request.json['quads']
    test = request.json['test']
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(influx_helper(fluid_command, quads, test))
    return 'influx success'
if __name__ == '__main__':
    with open(CONFIG_PATH,'r') as config:
        port = yaml.safe_load(config)['server_port']
    app.run(host='0.0.0.0', port=port)
