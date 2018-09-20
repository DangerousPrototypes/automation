############################################
# 	A script to check git for new commits, 
#	run make, package up the output
#	and POST to an HTML form.
#
#	More docs:
#		http://dangerousprototypes.com
#		https://github.com/DangerousPrototypes/automation
#
#	Used at:
#		http://buspirate.com/firmware/builds
#
#
#	Output is a JSON file, here's some of the key variables:
#
# 	'error'
# 		0 if make executed, 1 if make returned system error (build failed with errors).
# 	'timestamp'
# 		start/stop build timestamp
# 	'firmware'/'hardware'
# 		Identifying info
# 	'starthashlong'/'endhashlong'
# 		Commit hash before/after 'git pull' command
# 	'gitoutput'
# 		Output from the 'git pull' command
# 	'makeoutput'
# 		Output from the 'make' command
# 	'apikey'
# 		Identifying info
# 	'firmware_type'
# 		The file extension of the firmware. Added to automate naming in the backend. PIC uses .HEX, ARM uses .BIN
# 	'base64encbin'
# 		Base 64 encoded firmware file
#
##############################################
import sys
import subprocess
import json
import time
import os
import argparse
import base64
import requests
import imp
from pprint import pprint


parser = argparse.ArgumentParser(description='Dangerous Prototypes auto build v2.0')
parser.add_argument('--tasks', required=False, default='buildv2_tasks.py', help='Build tasks configuration file (default buildv2_tasks.py)')
parser.add_argument('--interval', required=False, default=10.0, help='Repeat interval in minutes (default 10)')
parser.add_argument('--test', required=False, default=False, help='Run in test mode, force result upload even if no new commits')

args = vars(parser.parse_args())
#pprint(args)

class autoBuild:
	def __init__(self):
		#import make tasks config
		with open(args['tasks'],'r') as infile:
			tasks=imp.load_source( 'tasks', '',infile) 
		self.tasks=tasks.tasks
		
	def runTasks(self):
		for task in self.tasks:
			self.pull(task)
			#pprint(task)
			#pprint(task['work_dir'])
	
	def pull(self, task):
		#git log --pretty=format:'%h' -n 1 #or H for long hash
		hashshort = subprocess.check_output('cd '+task['git_pull_dir']+" && git log --pretty=format:'%h' -n 1",shell=True).decode().strip("'")
		hashlong = subprocess.check_output('cd '+task['git_pull_dir']+" && git log --pretty=format:'%H' -n 1",shell=True).decode().strip("'")


		gitoutput=subprocess.check_output('cd '+task['git_pull_dir']+' && git pull',shell=True).decode()

		newhashshort = subprocess.check_output('cd '+task['git_pull_dir']+" && git log --pretty=format:'%h' -n 1",shell=True).decode().strip("'")
		newhashlong = subprocess.check_output('cd '+task['git_pull_dir']+" && git log --pretty=format:'%H' -n 1",shell=True).decode().strip("'")

		print(hashlong)
		print(gitoutput)
		print(newhashlong)
		
		if args['test'] is not False or hashlong != newhashlong:
			for build in task['builds']:
				pprint(build['work_dir'])
				self.make(build,hashshort,hashlong,gitoutput,newhashshort,newhashlong)
		
	def make(self, build,hashshort,hashlong,gitoutput,newhashshort,newhashlong):
		result={}
		print('Preparing build report')
		timestampstart=time.time()
		subprocess.check_output('cd '+build['work_dir']+' && make clean', shell=True)
		try:
			makeoutput=subprocess.check_output('cd '+build['work_dir']+' && '+build['make_command'], shell=True,stderr=subprocess.STDOUT).decode()
			result['error']='0';
		except subprocess.CalledProcessError as e:
			#print("command '"+e.cmd+"' return with error (code "+e.returncode.decode()+"): "+e.output)	
			pprint(e.returncode)
			#pprint(stderr)
			makeoutput=str(e.output.decode())
			result['error']='1'
			pprint(makeoutput)

		#create data structure
		result['timestamp']={}
		result['timestamp']['start']=timestampstart
		result['timestamp']['stop']=time.time()
		result['firmware']=build['firmware']
		result['hardware']=build['hardware']
		result['starthashshort']=hashshort
		result['starthashlong']=hashlong
		result['endhashshort']=newhashshort
		result['endhashlong']=newhashlong
		result['gitoutput']=gitoutput
		result['makeoutput']=makeoutput
		result['apikey']=build['api_key']
		result['response']='json'
		result['firmware_type']=build['output_file'].split(".")[-1] 	

		#base64 encode file
		if os.path.exists(build['output_dir'] + '/' + build['output_file']):
			print('Base 64 encoding file')
			with open(build['output_dir'] + '/' + build['output_file'], "rb") as firmware: 
				result['base64encbin']= base64.b64encode(firmware.read()).decode()

		#upload .json to API
		print("Dumping JSON")	
		with open(build['work_dir'] + '/result.json', 'w') as outfile:
			json.dump(result, outfile, indent=4, sort_keys=False)
			
		print("Uploading JSON")
		with open(build['work_dir'] + '/result.json', 'rb') as f: 
			r = requests.post(build['api_url'], files={'result': f})	
		pprint(r)
		pprint(r.text)
		subprocess.check_output('cd '+build['work_dir']+' && make clean', shell=True)

ab=autoBuild()

while(True):
	ab.runTasks();
	print('sleep')
	#sleep for configured number of minutes
	time.sleep(args['interval']*60)



