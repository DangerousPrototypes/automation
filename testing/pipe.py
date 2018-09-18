import sys
import json
import serial
import time
import os
import glob
import requests
import argparse
import imp
from pprint import pprint
from colorama import init
from colorama import Fore
from colorama import Style
from colorama import Back

parser = argparse.ArgumentParser(description='Bus Pirate Automated Test Suite v1.0')
parser.add_argument('--port', required=False, default='COM4', help='Bus Pirate serial port name')
parser.add_argument('--test', required=False, default=None, help='Test script (folder) to load')
parser.add_argument('--result', required=False, default='result.json', help='Test result file name')
parser.add_argument('--upload', required=False, action='store_true', help='Upload results?')
parser.add_argument('--url', required=False, help='Upload URL')
parser.add_argument('--apikey', required=False, help='Upload API key')
parser.add_argument('--rig', required=False, default=None, help='Test rig definition file')
parser.add_argument('--rigport', required=False, default=None, help='Test rig serial port')
parser.add_argument('--rigdevice', required=False, default=None, help='Set test rig to device')
args = vars(parser.parse_args())
#pprint( args)
#if --upload make sure url and api key specified
if args['upload']==True:
	if args['url']==None or args['apikey']==None:
		print('Specify upload URL and API key or remove --upload option')
		sys.exit(2)

class testSuite:
	def __init__(self):
		self.version={}
		self.rig=None
	
	def setupBusPirate(self, p='COM4', s=115200, t=1):
		try:
			self.port = serial.Serial(p, s, timeout=t)
		except:
			self.printRed('Could not open Bus Pirate serial port!')
			quit()		
		self.port.flushInput()
		
		
	def setupRig(self, rig, rigport):	
		self.rig=rig
		# Setup the test rig if any...
		if self.rig is not None:
			try:
				self.rig_port = serial.Serial(rigport, 115200, timeout=1)
			except:
				self.printRed('Could not open test rig serial port!')
				quit()
			#get test rig version
			self.rig_port.flushInput()
			self.rig_port.write("\n".encode())
			self.rig_port.read(10000)
			self.rig_port.flushInput()
			self.rig_port.write("\n".encode())
			self.rig_port.write("i\n".encode())
			data = self.rig_port.read(10000).decode()
			lines=data.splitlines(0)
			self.lastPrompt=lines[-1];
			#pprint(lines)
			self.version['rig_hardware']=lines[2].rpartition('v')[2]
			self.version['rig_hardwareMajor']=self.version['rig_hardware'].split('.')[0]
			seq_type= type(self.version['rig_hardwareMajor'])
			self.version['rig_hardwareMajor']=seq_type().join(filter(seq_type.isdigit, self.version['rig_hardwareMajor']))	
			self.printGreen('Test Rig Hardware: ' + self.version['rig_hardware'])	
			self.rig_port.write("m 5 1 1 2 1 2 2 \n W\n".encode()) #put in SPI mode
			rig_reply=self.rig_port.read(10000).decode()
			self.printYellow(rig_reply)
			self.printYellow(self.setRigChip(0xff, 0))
		
	def printRed(self, text):
		print(Back.RED + text + Style.RESET_ALL)
	def printYellow(self,text):
		print(Back.YELLOW + text + Style.RESET_ALL)
	def printGreen(self,text):
		print(Back.GREEN + text + Style.RESET_ALL)
	
	def getVersion(self):
		#get bus pirate hardware and firmware version
		self.port.flushInput()
		self.port.write("\n".encode())
		self.port.read(10000)
		self.port.flushInput()
		self.port.write("\n".encode())
		self.port.write("i\n".encode())
		data = self.port.read(10000).decode()
		lines=data.splitlines(0)
		self.lastPrompt=lines[-1];
		#pprint(lines)
		self.version['hardware']=lines[2].rpartition('v')[2]
		self.version['hardwareMajor']=self.version['hardware'].split('.')[0]
		seq_type= type(self.version['hardwareMajor'])
		self.version['hardwareMajor']=seq_type().join(filter(seq_type.isdigit, self.version['hardwareMajor']))
		firmwareInfo=lines[3].split()
		self.version['firmware']=firmwareInfo[1].strip('v')
		self.version['commit']=firmwareInfo[2].strip('r')
		#pprint(self.version)
		self.printGreen('Hardware: ' + self.version['hardware'])
		self.printGreen('Firmware: ' + self.version['firmware'] + ' commit: '+self.version['commit'] )
		return data
		
	def importTest(self,test):
		t = json.load(open(test))
		#t=json.loads(requests.get('http://bp.dev/api/test/download/50').text)
		#test if this is a test for our hardware version
		#if no version string, set one
		if 'hardware' in t:
			if self.version['hardwareMajor'] not in t['hardware']:
				self.printRed("Not for this hardware, skipping")
				return False
		else:
			self.printYellow("Hardware version not defined, using on all versions")
			t['hardware']=[]
			t['hardware'].append(self.version['hardwareMajor'])		
		
		self.test={}
		if 'name' in t: 
			self.test['name']=t['name']
			self.printGreen("Test: " + t['name'])
		else: 
			self.printYellow("Missing test name, using 'unknown'")
			self.test['name']='unknown'		
		
		if 'device' in t:
			self.test['device']=t['device']
			self.printGreen("Device: " + t['device'])
		else:
			self.printYellow("Missing device ID, using 'unknown'")
			self.test['device']='unknown'			
						
		if 'test' not in t:
			self.printRed("Missing test steps!")
			self.test['test']={}
		else:
			self.printGreen("Test steps: " + str(len(t['test'])))	
			self.test['test']=t['test']
		
		if self.rig is not None:
			self.rigUpdate(self.test['device'])
		
		return True
	
	def rigUpdate(self, device):
		if device not in self.rig['devices']:
			if self.rig['deviceNotFoundAction'] is 'exit':
				self.printRed('Device not found in rig definition file, exiting!')
				quit()
			else:
				self.printYellow('Device not found in rig definition file, skipping!')
				return False
		else:				
			d=self.rig['devices'][device];
			self.printGreen("Position: "+str(d))
			
			#get board number
			d-=1
			board=d>>4 #upper four bits are the board position
			self.printGreen("Rig board number: "+str(board+1))
			
			position=d&0x0F #remove board number
			self.printGreen("Board position: "+str(position+1))
			n = 0
			k=1
			#reverse the bits
			for i in range(8):              	# for each bit number
				n=n<<1
				if (position & k):     	# if it matches that bit
					n |= 1				   	# set the "opposite" bit in answer
				k=k<<1
				#print("<<: "+hex(n))
					
			#print("Reverse: "+hex(n))
			#n=n|0x08 /E is disabled high, active low...
			#print("W/Enable: "+hex(n))
			self.printGreen("Setup test rig active chip")
			self.printYellow(self.setRigChip(board, n))
			#quit()

	def setRigChip(self, board, chip):
		for i in range(4,0,-1): #currently up to four boards
			if(i==board+1):
				self.rig_port.write((" " + hex(chip)).encode()) #send the position and set the enable bit`
			else:
				self.rig_port.write((" 0x08").encode()) #send 0x08 /E disabled high
		self.rig_port.write((" ][\n").encode()) #send linefeed, bump the latch
		rig_reply=self.rig_port.read(10000).decode()
		return rig_reply
		
	def run(self):
		#reset to HiZ
		self.port.write("\nm 1\n".encode())
		self.port.read(10000).decode()
		
		#test output array
		result={}
		
		result['timestamp']={}
		result['timestamp']['start']=time.time()
		result['timestamp']['stop']=time.time()
		result['name']=self.test['name']
		result['device']=self.test['device']
		
		if self.rig is not None:
			result['position']=self.rig['devices'][self.test['device']]
		
		result['test']={}
	
		i=0
		
		#loop tests
		self.port.flushInput()
		for steps in self.test['test']:
			#get steps name
			if 'name' not in steps:
				self.printYellow("Missing step name, using 'step_"+str(i)+"'")
				#use default steps name
				defaultName='step_' + str(i)
				steps['name']=defaultName

			self.printGreen("Starting step: " + steps['name'])
			#add to output array			
			result['test'][steps['name']]=[]
		
			if 'steps' not in steps:
				self.printRed('No test steps, doing nothing!')
				continue;
			#else:
				#self.printGreen('Step sections: '+ str(len(steps['steps'])))
				
			for step in steps['steps']:
				
				#if 'hardware' not in then all else check against this version
				if 'hardware' in step:
					if self.version['hardwareMajor'] not in step['hardware']:
						continue;
				
				if 'commands' not in step:
					self.printRed('No test commands, doing nothing!')
					continue;
				
				#loop commands
				for command in step['commands']:	
				
					output={}
				
					#write command out
					self.port.write(command.encode());
					output['command']=command
					
					#if 'linefeed' not in then linefeed else check against the linefeed values
					if 'linefeed' not in step: #default is line feed
						self.port.write("\n".encode())
					else:
						if step['linefeed']==True:
							self.port.write("\n".encode())
							
					#save output in array with step/steps name/input and output stepss
					data = self.port.read(10000).decode()
					print(self.lastPrompt + data)					
					output['result']=self.lastPrompt + data
					
					lines=data.splitlines(0)
					if len(lines) > 0 :
						self.lastPrompt=lines[-1]
						
					result['test'][steps['name']].append(output)
			i=i+1
					
		result['timestamp']['stop']=time.time()
		self.port.write("\nm 1\n".encode())
		self.port.read(10000).decode()
		return result
							
	def display(self, output):
		print(output);
		
	def saveResult(self,tests,filename):
			#test output array
		out={}	
		out['hardware']={}
		out['hardware']['version']=self.version['hardware']
		out['hardware']['major']=self.version['hardwareMajor']
		out['firmware']={}
		out['firmware']['version']=self.version['firmware']
		out['firmware']['commit']=self.version['commit']
		out['tests']=tests #add based on device key....
		
		with open(filename, 'w') as outfile:
			json.dump(out, outfile, indent=4, sort_keys=False)
					
	def timeout(self, timeout=0.1):
		select.select({}, {}, {}, timeout)

init() #colorama
t=testSuite()
	
#load test rig definition file if selected
if args['rig'] is not None:
	if args['rigport'] is None:
		print(Back.RED + '--rigport is required with option --rig' + Style.RESET_ALL)
		quit()
	with open(args['rig'],'r') as infile:
		rig=imp.load_source( 'rig', '',infile) 
	#pprint(rig.rig)
	rig=rig.rig
	t.setupRig(rig,args['rigport'])
	if args['rigdevice'] is not None:
		t.rigUpdate(args['rigdevice'])
else:
	rig=None
	

if args['test'] is not None:
	t.setupBusPirate(args['port'],115200,1)

	version=t.getVersion()
	result={}

	#are we loading a single script or a folder of scripts?
	if os.path.isfile(args['test']):
		testStatus=t.importTest(args['test'])
		if testStatus == False:
			t.printRed('Skipped test, hardware version not supported!')
		else:
			testoutput=t.run()
			result[testoutput['name']]=testoutput
	elif os.path.isdir(args['test']):
		for filename in glob.glob(os.path.join(args['test'], '*.json')):
			testStatus=t.importTest(filename)
			if testStatus == False:
				t.printRed('Skipped test, hardware version not supported!')
			else:
				testoutput=t.run()
				result[testoutput['name']]=testoutput

	t.saveResult(result,args['result'])

	if(args['upload']==True):
		uploadtempfilename='upload.json'
		temp = json.load(open(args['result']))
		temp['apikey']=args['apikey']
		with open(uploadtempfilename, 'w') as outfile:
			json.dump(temp, outfile, indent=4, sort_keys=False)
		with open(uploadtempfilename, 'rb') as f: 
			r = requests.post(args['url'], files={uploadtempfilename: f})	