### This script helps compile the blockly functions into a single python script and uploaded
### to the Raspberry Pi running the xARM.


import os, glob, subprocess
import urllib.request, tarfile
from xarm.tools.blockly_tool import BlocklyTool
from pathlib import Path
import shutil

xarm_ip = "10.241.32.169"
pi_ip = "10.241.32.170"

# List Directories
dir_path = os.path.dirname(os.path.realpath(__file__)) + '/server_compile/'
save_path = os.path.dirname(os.path.realpath(__file__)) + '/nonmag_server/'
file_paths = glob.glob(dir_path+"/functions/*.py")
##  http://192.168.1.198:18333/project/download?path=test/xarm5/app/myapp

user_input = input("Update Blockly Script from xArm (y/n) ? ")
if user_input == 'y':
    # Delete exisiting python + blockly functions
    for f in file_paths:
        os.remove(f)
    blockly_folder = Path(dir_path, "blockly-all-apps")
    if blockly_folder.exists() and blockly_folder.is_dir():
        shutil.rmtree(blockly_folder)

    # Download and unzip Blockly Scripts from Robot
    url = "http://" + xarm_ip + ":18333/project/download?path=test/xarm5/app/myapp"
    filename = "blockly-all-apps.tar.gz"
    urllib.request.urlretrieve(url, filename)
    tar = tarfile.open(filename)
    tar.extractall('server_compile/blockly-all-apps')
    tar.close()

blockly_functions = glob.glob(dir_path+"/blockly-all-apps/*")

# Convert blockly folder to python scripts
for file_name in blockly_functions:
    if "[UF]" not in file_name:
        function_name = os.path.basename(file_name)
        print(function_name)
        source_path = file_name + '/app.xml'
        target_path = dir_path + "/functions/" + function_name + ".py"
        f = open(target_path, "w")
        f.close()
        blockly = BlocklyTool(source_path)
        blockly.to_python(target_path)

# Reupdate directories
file_paths = glob.glob(dir_path+"/functions/*.py")
blockly_functions = glob.glob(dir_path+"/blockly-all-apps/*")
manual_functions_paths = glob.glob(dir_path+"/manual/*.py")

# Write header into scripts
f = open(save_path + "nonmag_server.py", "w")
file = open("server_compile/server_header.py", 'r')
lines = file.readlines()
for line in lines:
    f.write(line)

# Add functions to output script based on exported python scripts
for file_name in file_paths:
    function_name = os.path.basename(file_name)[0:-3]
    file = open(file_name, 'r')
    lines = file.readlines()
    record = False
    f.write("def " + function_name + "():\n")
    f.write("    print('Running ' + '" + function_name + "' + '...')")
    for line in lines:
        if "arm.register_count_changed_callback" in line:
            record = True
            continue
        if "release_error_warn_changed_callback(state_changed_callback)" in line:
            record = False
        if record:
            # print("Line{}: {}".format(count, line))
            f.write("    " + line)
    f.write("\n")

for file_name in manual_functions_paths:
    file = open(file_name, 'r')
    lines = file.readlines()
    for line in lines:
            f.write(line)

# Write footer into scripts
file = open("server_compile/server_foot.py", 'r')
lines = file.readlines()
for line in lines:
    f.write(line)

f.close()

# Transfer file to Raspberry Pi
## TODO: add pi folder to SCP w/ yMACS files
user_input = input("Update Raspberry Pi (y/n) ? ")
if user_input == 'y':
    subprocess.run(["scp", "-r", save_path , "pi@" + pi_ip + ":nonmag_server/"])
