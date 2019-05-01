# Shell script to install icestorm/yosys/nextpnr/arachne-pnr under linux
# Assumes logged in as root or do 'su' first
# The instructions are presented in the format of a shell script, but you should really run each step manually!
# Based on setup instructions from:
# http://www.clifford.at/icestorm/
# https://github.com/YosysHQ/nextpnr
# Tested under Ubuntu 18.10 64bit
# NOTE: add a swap if using a tiny node (digital ocean, vultr, etc) or the compile will run out of memory
# swapon --show #should be empty
# fallocate -l 4G /swapfile #4G, etc
# chmod 600 /swapfile
# mkswap /swapfile
# swapon /swapfile
# fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
# nano /etc/fstab #ADD: "/swapfile swap swap defaults 0 0"
cd ~

# Update apt-get repositories
apt-get update

# Install needed helpers
#prereqs
apt-get -y install build-essential clang bison flex libreadline-dev gawk tcl-dev libffi-dev git mercurial graphviz xdot pkg-config python python3 libftdi-dev qt5-default python3-dev libboost-all-dev cmake libqt5opengl5-dev python3-dev libeigen3-dev
					 
# install icestorm
git clone https://github.com/cliffordwolf/icestorm.git icestorm && cd icestorm && make -j$(nproc) && sudo make install && cd ..

#install arachne-pnr
git clone https://github.com/cseed/arachne-pnr.git arachne-pnr && cd arachne-pnr && make -j$(nproc) && sudo make install && cd ..

#install nextpnr
git clone https://github.com/YosysHQ/nextpnr nextpnr && cd nextpnr && cmake -DARCH=ice40 -DCMAKE_INSTALL_PREFIX=/usr/local . && make -j$(nproc) && sudo make install && cd ..

#install yosys
git clone https://github.com/cliffordwolf/yosys.git yosys && cd yosys && make -j$(nproc) && sudo make install && cd ..



















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
git clone –recursive https://github.com/DangerousPrototypes/bus_pirate_ng

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



