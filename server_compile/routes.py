## This script is to define all API calls to the flask server. Ensure that functions called in routes exist are pulled ./functions or ./manual
@app.route('/get_pump_settings', methods=['POST', 'GET'])
@auth.login_required
def get_pump_settings():
    """ GET pump settings from fluidics_server.conf file """
    return PUMP_SETTINGS

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
    pump_commands = request.json
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(influx_helper(pump_commands))
    return 'influx success'
