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
