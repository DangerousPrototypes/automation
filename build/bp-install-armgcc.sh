# Shell script to install ARM GNU compiler and libopencm3 under linux
# Assumes logged in as root or do 'su' first
# The instructions are presented in the format of a shell script, but you should really run each step manually!
# Based on setup instructions from Sjaak @ SMDprutser.nl
# Tested under Ubuntu 14.04 LTS 64bit

cd ~

# Update apt-get repositories
apt-get update

# Install needed helpers
# make, git, python (2.x), tar
apt-get -y install git make python tar

# Install ARM GCC compiler
# Download compiler
wget https://developer.arm.com/-/media/Files/downloads/gnu-rm/6-2017q2/gcc-arm-none-eabi-6-2017-q2-update-linux.tar.bz2 

# Extract compiler
bzip2 -d gcc-arm-none-eabi-6-2017-q2-update-linux.tar.bz2 

# Untar to usr/local
cd /usr/local
tar xsf ~/gcc-arm-none-eabi-6-2017-q2-update-linux.tar 

# Add compiler to the system PATH
# NOTE: manual step!
nano /etc/environment
# add '/usr/local/gcc-arm-none-eabi-6-2017-q2-update/bin' to the path variable
# save and exit <ctrl + X>, Y
# NOTE: log out and log in again for the PATH to take effect

##########################
# Clone Bus Pirate NG repo
##########################

#arm development directory for our projects
cd ~
mkdir armdev 
cd armdev 

##########################
#
#	YOU HAVE CHOICES!!!
#
#	The 'Sjaak' method uses a single command 
#	to pull the Bus Pirate source, libopencm3 source, 
#	and set libopencm3 to the right commit.
#
#	The 'Ian' method does each step individually
#
#	ONLY CHOOSE ONE!
#
##########################

##########################
#
# 	Sjaak method, one command
#
##########################
git clone --recursive https://github.com/DangerousPrototypes/bus_pirate_ng

cd bus_pirate_ng/libopencm3 
##########################
#
# 	END SJAAK METHOD
#
##########################

##########################
#
# 	Ian method, discrete commands
#
##########################
#git clone https://github.com/DangerousPrototypes/bus_pirate_ng.git

# Clone libopencm3 inside of bus_pirate_ng repo
#cd bus_pirate_ng
#git clone git://github.com/libopencm3/libopencm3.git 

# Switch to working commit for our project (953bf53) because later versions break compatibility
#cd libopencm3 
#git checkout 953bf53
##########################
#
# 	END IAN METHOD
#
##########################

# Build libopencm3 libraries
cd ~/armdev/bus_pirate_ng/libopencm3
make

# Test compile
cd ~/armdev/bus_pirate_ng/source
make clean
make



