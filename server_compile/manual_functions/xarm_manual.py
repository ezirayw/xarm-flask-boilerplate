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
