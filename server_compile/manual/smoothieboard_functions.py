## This script is to define any functions that are based on other API calls/ functions, mainly if coordination is needed with the smoothieboard.



# #########################   Example Scripts ####################################
# def squirter_to_vialrest(index):
#     print('Bringing squirter to vialrest ' + str(index) + '...')
#
#     params['angle_speed'] = 100
#     params['angle_acc'] = 500
#     params['speed'] = 1000
#     params['acc'] = 30000
#
#     # Upper left vial coordinates
#     x_00 = 341.6; y_00 = -117; z_00 = 335.1; roll = 180; yaw = -90
#
#     # Determine vial coordinates
#     if index in [0,1,2,3]:
#         x = x_00
#     if index in [4,5,6,7]:
#         x = x_00 - 50.8
#     if index in [8,9,10,11]:
#         x = x_00 - 101.6
#     if index in [12,13,14,15]:
#         x = x_00 - 152.4
#
#     if index in [0,4,8,12]:
#         y = y_00
#     if index in [1,5,9,13]:
#         y = y_00 - 50.8
#     if index in [2,6,10,14]:
#         y = y_00 - 101.6
#     if index in [3,7,11,15]:
#         y = y_00 - 152.4
#
#     if arm.error_code == 0 and not params['quit']:
#         if arm.set_position(*[x, y, z_00+15, roll, 0.0, yaw], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False) != 0:
#             params['quit'] = True
#     if arm.error_code == 0 and not params['quit']:
#         if arm.set_position(*[x, y, z_00-15, roll, 0.0, yaw], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True) != 0:
#             params['quit'] = True
#
# def squirter_to_vialready(index):
#     print('Bringing squirter to ready...')
#
#     params['angle_speed'] = 100
#     params['angle_acc'] = 500
#     params['speed'] = 1000
#     params['acc'] = 30000
#
#     # Upper left vial coordinates
#     x_00 = 341.6; y_00 = -117; z_00 = 335.1; roll = 180; yaw = -90
#
#     # Determine vial coordinates
#     if index in [0,1,2,3]:
#         x = x_00
#     if index in [4,5,6,7]:
#         x = x_00 - 50.8
#     if index in [8,9,10,11]:
#         x = x_00 - 101.6
#     if index in [12,13,14,15]:
#         x = x_00 - 152.4
#
#     if index in [0,4,8,12]:
#         y = y_00
#     if index in [1,5,9,13]:
#         y = y_00 - 50.8
#     if index in [2,6,10,14]:
#         y = y_00 - 101.6
#     if index in [3,7,11,15]:
#         y = y_00 - 152.4
#
#     if arm.error_code == 0 and not params['quit']:
#         if arm.set_position(*[x, y, z_00+15, roll, 0.0, yaw], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False) != 0:
#             params['quit'] = True
#
# def squirter_to_blockrest(index):
#     print('Bringing squirter to vialrest ' + str(index) + '...')
#
#     params['angle_speed'] = 100
#     params['angle_acc'] = 500
#     params['speed'] = 1000
#     params['acc'] = 30000
#
#     # Upper left vial coordinates
#     x_00 = 341.6; y_00 = -117; z_00 = 335.1; roll = 180; yaw = -90
#
#     # Determine vial coordinates
#     if index in [0,1,2,3]:
#         x = x_00
#     if index in [4,5,6,7]:
#         x = x_00 - 50.8
#     if index in [8,9,10,11]:
#         x = x_00 - 101.6
#     if index in [12,13,14,15]:
#         x = x_00 - 152.4
#
#     if index in [0,4,8,12]:
#         y = y_00
#     if index in [1,5,9,13]:
#         y = y_00 - 50.8
#     if index in [2,6,10,14]:
#         y = y_00 - 101.6
#     if index in [3,7,11,15]:
#         y = y_00 - 152.4
#
#     if arm.error_code == 0 and not params['quit']:
#         if arm.set_position(*[x, y, z_00+15, roll, 0.0, yaw], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False) != 0:
#             params['quit'] = True
#     if arm.error_code == 0 and not params['quit']:
#         if arm.set_position(*[x, y, z_00-15, roll, 0.0, yaw], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=True) != 0:
#             params['quit'] = True
#
# def squirter_to_blockready(index):
#     print('Bringing squirter to ready...')
#
#     params['angle_speed'] = 100
#     params['angle_acc'] = 500
#     params['speed'] = 1000
#     params['acc'] = 30000
#
#     # Upper left vial coordinates
#     x_00 = 341.6; y_00 = -117; z_00 = 335.1; roll = 180; yaw = -90
#
#     # Determine vial coordinates
#     if index in [0,1,2,3]:
#         x = x_00
#     if index in [4,5,6,7]:
#         x = x_00 - 50.8
#     if index in [8,9,10,11]:
#         x = x_00 - 101.6
#     if index in [12,13,14,15]:
#         x = x_00 - 152.4
#
#     if index in [0,4,8,12]:
#         y = y_00
#     if index in [1,5,9,13]:
#         y = y_00 - 50.8
#     if index in [2,6,10,14]:
#         y = y_00 - 101.6
#     if index in [3,7,11,15]:
#         y = y_00 - 152.4
#
#     if arm.error_code == 0 and not params['quit']:
#         if arm.set_position(*[x, y, z_00+15, roll, 0.0, yaw], speed=params['speed'], mvacc=params['acc'], radius=-1.0, wait=False) != 0:
#             params['quit'] = True
#
# smoothie_mL_per_step = 0.016 # mL/step at F6000; 5 seconds for 12 mL at G1 E-500 F6000
# smoothie_seconds_per_step = 0.01
#
# def send_gcode(output):
#    time.sleep(.2)
#    output = output + '\n'
#    s.write(output.encode('ascii'))
#    time.sleep(.2)
#
# def squirt_liquid(volume):
#    send_gcode("G91")
#    squirter_steps = volume/smoothie_mL_per_step
#    send_gcode('G1 X'+ str(squirter_steps) + ' F6000')
#    time.sleep(abs(squirter_steps) * smoothie_seconds_per_step + .5)
#    send_gcode('G1 X-1 F6000')
#    send_gcode("M18")
#
# def dilute_vials(volume,vials): #mL
#    grab_squirterA()
#    for index in vials:
#       squirter_to_vialrest(index)
#       squirt_liquid(volume)
#       squirter_to_vialready(index)
#    drop_squirterA()
#
# def dilute_block(volume,well): #mL
#    grab_squirterA()
#    for index in well:
#       squirter_to_blockrest(index)
#       squirt_liquid(volume)
#       squirter_to_blockready(index)
#    drop_squirterA()
#
# def prime_pump(volume): #mL
#    grab_squirterA()
#    squirter_to_waste()
#    squirt_liquid(volume)
#    drop_squirterA()
#
# def vortex_conical(mix_time, vials):
#    for index in vials:
#       grab_vialrest(index)
#       drop_vortexer()
#       GPIO.output(31, GPIO.HIGH)
#       time.sleep(mix_time)
#       GPIO.output(31, GPIO.LOW)
#       time.sleep(1)
#       grab_vortexer()
#       drop_vialrest(index)
#
# @app.route('/route_dilute_vials', methods=['POST'])
# @auth.login_required
# def route_dilute_vials():
#     changeStatus('busy')
#     volume = request.json['volume']
#     vials = request.json['vials']
#     dilute_vials(volume, vials)
#     changeStatus('ready')
#     return 'Vials Diluted!'
#
# @app.route('/route_prime_pump', methods=['POST'])
# @auth.login_required
# def route_prime_pump():
#     changeStatus('busy')
#     volume = request.json['volume']
#     prime_pump(volume)
#     changeStatus('ready')
#     return 'Pump Primed!'
#
#
# @app.route('/route_vortex_conical', methods=['POST'])
# @auth.login_required
# def route_vortex_conical():
#     changeStatus('busy')
#     mix_time = request.json['mix_time']
#     vials = request.json['vials']
#     vortex_conical(mix_time, vials)
#     changeStatus('ready')
#     return 'Vials Mixed!'
#
# @app.route('/route_return_home', methods=['POST'])
# @auth.login_required
# def route_return_home():
#     changeStatus('busy')
#     return_home()
#     changeStatus('ready')
#     return 'Return xARM Home'
#
# #########################   Example Scripts ####################################
