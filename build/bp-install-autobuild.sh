# Shell script to install Bus Pirate firmware auto-build under linux
# Assumes logged in as root or do 'su' first
# The instructions are presented in the format of a shell script, but you should really run each step manually!
# Tested under Ubuntu 14.04 LTS 64bit

cd ~

# Install Python 3.x
apt-get install python3

# Install Python PIP 3.x
apt-get install python3-pip

# Install Python modules
pip3 install requests pprint

# Download the latest autobuild script, example config
# https://github.com/DangerousPrototypes/automation see latest here if files have moved...
#
wget https://raw.githubusercontent.com/DangerousPrototypes/automation/master/build/buildv2.py
wget https://raw.githubusercontent.com/DangerousPrototypes/automation/master/build/buildv2_tasks_example.py
wget https://raw.githubusercontent.com/DangerousPrototypes/automation/master/build/bp-build

# Copy the configuration file
cp buildv2_tasks_example.py buildv2_tasks.py

# Edit the build configuration file
nano buildv2_tasks.py

# Add build jobs to the tasks configuration file:
#
# 'hardware'/'firmware':
# 	Hardware/Firmware version id. This is returned in the result json as 'hardware'/'firmware'. Used to support multiple builds, use as needed.
#
# 'work_dir':
#	Where to execute git and make commands. '/root/armdev/bus_pirate_ng/source' or '/root/picdev/Bus_Pirate/Firmware/busPirate3X.X'
#
# 'make_command':
#	Make command for this task. For example 'make bin' (ARM) or 'make' (PIC)
#
# 'output_dir':
#	Firmware output directory. For example '/root/armdev/bus_pirate_ng/source' or '/root/picdev/Bus_Pirate/Firmware/busPirate3X.X/dist/default/production'
#
# 'output_file':
#	Name of firmware file in output_dir. For example 'buspirateNG.bin' or 'busPirate3X.X.production.hex'
#
# 'api_url','api_key':
#	URL to POST results JSON file. 'api_key' is included for authentication. Backend stuff depends on your implementation.


# Test the build script
# --test=true force compile and upload result, even if no new git commits
python3 buildv2.py --test=true

# Install as service
# Installing the script as a service means it will run at startup and continue running in the background until stopped or crashed... 
# Copy the bp-build service script to /etc/init.d and give it execution permissions
cp bp-build /etc/init.d/bp-build
chmod 777 bp-build

# Customize the file paths in the 'bp-build' service script:
#
# EXEARGS="/root/buildv2.py --tasks /root/buildv2_tasks.py" 
#
# NOTE: be sure the full path to buildv2 and buildv2_tasts.py matches your setup
nano bp-build

# Start the service
/etc/init.d/bp-build start

# Stop the service
# NOTE: an error about PID means it crashed at some point. Double check the full path to the script in bp-build
/etc/init.d/bp-build stop

# Command line options
# root@demoautomakesetup:~# python3 buildv2.py --help
#
# usage: buildv2.py [-h] [--tasks TASKS] [--interval INTERVAL] [--test TEST]
# Dangerous Prototypes auto build v2.0
# optional arguments:
# -h, --help           show this help message and exit
# --tasks TASKS        Build tasks configuration file (default: buildv2_tasks.py)
# --interval INTERVAL  Repeat interval in minutes (default: 10)
# --test=true          Run in test mode, force uploads even if no new commits (default false)
# root@demoautomakesetup:~# 
