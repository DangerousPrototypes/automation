# Shell script to install MPLABX and XC16 compiler under linux
# Assumes logged in as root or do 'su' first
# The instructions are presented in the format of a shell script, but you should really run each step manually!
# Based on example here: https://www.microchip.com/forums/FindPost/998286
# Tested under Ubuntu 14.04 LTS 64bit, newer versions may not have the needed 32bit support libraries
# Updated for Ubuntu 18.10 64 bit

cd ~

# Update apt-get repositories
apt-get update

# Install needed helpers
# make, tar, git-core, default-jre
apt-get -y install make tar git-core default-jre

# Install 32bit libraries
# ubuntu 14.04: apt-get -y install lib32z1 lib32ncurses5 lib32stdc++6 libx11-6:i386 libexpat1:i386 libXext6:i386
# 18.10 :
apt-get -y install lib32z1 lib32ncurses5-dev lib32stdc++6 libx11-6:i386 libexpat1:i386 libxext6:i386


# Install XC16 compiler
# Download compiler 
wget http://www.microchip.com/mplabxc16linux

# Make executable
chmod +x mplabxc16linux

# Install
# NOTE: two pairs of dashes -- --mode
# NOTE: remember the XC16 install directory, it will be needed later (eg '/opt/microchip/xc16/v1.36')
./mplabxc16linux -- --mode text
# NOTE: follow instructions to accept the license and install the software

# Install MPLabX IDE (needed generate make files)
# Download IDE
wget http://www.microchip.com/mplabx-ide-linux-installer

# Extract IDE
# NOTE: This will extract a file such as MPLABX-v5.05-linux-installer.sh. Use this file name in the next two steps
tar -xvf mplabx-ide-linux-installer

# Make install script executable
# NOTE: change name to current version of IDE installer
chmod +x MPLABX-v5.15-linux-installer.sh

# Run install script
# NOTE: change name to current version of IDE installer
# NOTE: two pairs of dashes -- --mode
./MPLABX-v5.15-linux-installer.sh -- --mode text
# NOTE: follow instructions to accept the license and install the software

# Install peripheral library
# Download library
wget http://ww1.microchip.com/downloads/en//softwarelibrary/pic24%20mcu%20dspic%20peripheral%20lib/peripheral-libraries-for-pic24-and-dspic-v2.00-linux-installer.run

# Make executable
chmod +x peripheral-libraries-for-pic24-and-dspic-v2.00-linux-installer.run

# Run installer
# NOTE: two pairs of dashes -- --mode
# NOTE: if XC16 installed to a version specific directory it needs to be entered. Example library default install directory is '/opt/microchip/xc16' but our XC16 is installed in '/opt/microchip/xc16/v1.36' by default
./peripheral-libraries-for-pic24-and-dspic-v2.00-linux-installer.run -- --mode text
# NOTE: follow instructions to accept the license and install the software

# Clone Bus Pirate repo
mkdir picdev &&
cd picdev &&
git clone https://github.com/DangerousPrototypes/Bus_Pirate.git

# Check out a development branch (optional)
cd Bus_Pirate
git checkout firmware_v8_official

# Create correctly formatted make files from the MPLABX project file
# Do for all projects before compiling
# The location of the prjMakefilesGenerator.sh changes frequently. You may need to hunt for it.
cd ~/picdev/Bus_Pirate/Firmware/busPirate3X.X
/opt/microchip/mplabx/v5.15/mplab_platform/bin/prjMakefilesGenerator.sh .

cd ~/picdev/Bus_Pirate/Firmware/busPirate4X.X
/opt/microchip/mplabx/v5.15/mplab_platform/bin/prjMakefilesGenerator.sh .

cd ~/picdev/Bus_Pirate/Firmware/busPirate5X.X
/opt/microchip/mplabx/v5.15/mplab_platform/bin/prjMakefilesGenerator.sh .

# Test compile
# There are three MPLABX project files in Bus_Pirate/Firmware/busPirate(3-5)X.X
# Each of these projects is setup in MPLABX IDE to pass the -D {build version} compiler flag for one version of hardware (v3, v4, v5)
# These commands are normally run by the automated compile script
# NOTE: if you have compile errors be sure you ran prjMakefilesGenerator.sh in the previous step!!!
cd ~/picdev/Bus_Pirate/Firmware/busPirate3X.X
make clean
make

cd ~/picdev/Bus_Pirate/Firmware/busPirate4X.X
make clean
make

cd ~/picdev/Bus_Pirate/Firmware/busPirate5X.X
make clean
make


