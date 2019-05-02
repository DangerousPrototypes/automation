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
#	Input is a JSON feed from an API.  It is something like this:
# tasks	=[ 		#an array of tasks
#	branch_id=1	#this is a unique ID number for the branch (from our database), the branch will be cloned into a folder named "1"
#	git_pull_dir="source" #folder to run git pull command
#	git_branch="master"	#git branch to check out
#	pre_install_script	=""	#\n terminated list of commands to run BEFORE cloning the repo # and blank lines ignored
#	post_install_script=""	#\n terminated list of commands to run AFTER cloning the repo # and blank lines ignored
#	git_url	="https://github.com/DangerousPrototypes/Bus_Pirate.git" #url for the remote repo
#	builds =[	#an array of builds to run on this branch
# 		autobuild_id	=1 #unique id of this build. will be POSTed to the API
# 		work_dir	="source" #where to run make
# 		make_command	="make bin" #the make command
# 		output_dir	="source" #where to find the compiled files
# 		output_file	="buspirateNG.bin" #compiled file to POST to api
# 		api_url	="http://site.com/api/build" #url of the API to POST the build results
# 		api_key	="" #reference info, key to API. will be posted back to API as api_key variable
# 		],
#		[
#		another build
#		]
#	[
#	another task
#	]
#
#	Output is a JSON file, here's some of the key variables:
#
# 	'error'
# 		0 if make executed, 1 if make returned system error (build failed with errors).
# 	'timestamp'
# 		start/stop build timestamp
# 	'starthashlong'/'endhashlong'
# 		Commit hash before/after 'git pull' command
# 	'gitoutput'
# 		Output from the 'git pull' command
# 	'makeoutput'
# 		Output from the 'make' command
# 	'apikey'
# 		Identifying info
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
import pathlib


parser = argparse.ArgumentParser(description='Dangerous Prototypes auto build v3.0')
parser.add_argument('--config', required=False, default='buildv3_config.py', help='Build tasks configuration file (default buildv3_config.py)')
parser.add_argument('--interval', required=False, default=1.0, help='Repeat interval in minutes (default 1)')
parser.add_argument('--test', required=False, default=False, help='Run in test mode, force result upload even if no new commits')
parser.add_argument('--debug', required=False, default=False, help='Run in debug mode, skip git and make commands')

args = vars(parser.parse_args())
#pprint(args)

class autoBuild:
	def __init__(self):
		#import config
		with open(args['config'],'r') as infile:
			config=imp.load_source( 'config', '',infile) 
		self.config=config.config
		self.log=[]
		self.new_repo=False;
		#pprint(self.config)
		return
	def runTasks(self):
		for feed in self.config:
			#import make tasks config
			print("Loading tasks")
			try:
				r = requests.post(feed['api_url'], data={'api_key': feed['api_key']})
			except requests.exceptions.ConnectionError as e:
				print("Error loading tasks: cannot connect to server")
				continue
			if(r.status_code!=requests.codes.ok):
				print("Error loading tasks: page not found")
				continue
			#pprint(r)
			#pprint(r.text)
			tasks= json.loads(r.text)
			if 'status' in tasks:
				#pprint(tasks['status'])
				if tasks['status']!= 'ok':
					print("Error loading tasks: Missing or bad API key")
					continue
			#pprint(tasks)
			self.tasks=tasks['tasks']

			for task in self.tasks:
				self.log.clear()
				self.log.append('===== '+time.asctime()+' =====')
				#pprint(feed)
				#pprint(task)
				#we will reuse this a lot!
				#pprint(str(task['branch_id']))
				branch_path=feed['repo_store'] +'/' + str(task['branch_id'])
		
				#check for branch folder
				self.new_repo=False
				p=pathlib.Path(branch_path)
				if p.exists() is False:
					init_result=self.init_branch(branch_path,task['git_url'],task['git_branch'],task['pre_install_script'],task['post_install_script'])
					#save install log to file
					install_report=''
					for line in self.log:
						install_report=install_report + "{}\n".format(line)
					with open('build_install_log.txt', 'a+') as outfile:
						outfile.write(install_report)
					#POST to api/autobuildinstallreport
					try:
						r = requests.post(feed['api_url'], data={'api_key': feed['api_key'],'branch_id':task['branch_id'],'install_report':install_report})
					except requests.exceptions.ConnectionError as e:
						print("Error submitting install report: cannot connect to server")
				
					if init_result is False:
						pprint(self.log)
						continue
					else:
						self.new_repo=True
				
				#pull and make if new commits
				#pprint(task)
				self.pull(branch_path, task)
				
	def logger(self, message):
		print(message)
		self.log.append(message)
		
	def command(self, command, error):
		try:
			self.logger(command)
			output = subprocess.check_output(command,shell=True, stderr=subprocess.STDOUT ).decode()
			self.logger(output)
		except subprocess.CalledProcessError as e:
			self.logger(e.output.decode())
			self.logger(error)
			return False
		return True
		
	def init_branch(self, branch_path, git_url, git_branch, pre_install_script, post_install_script):
		self.logger("Repo not found. Creating folder.")
		#make path for this branch
		pathlib.Path(branch_path).mkdir(parents=True, exist_ok=True)
		#try preinstall script
		if pre_install_script not in (None,'',False):
			if self.install_script(branch_path, pre_install_script) is False: return False
		#try to check it out
		if git_url not in (None,'',False):
			if self.git_clone(branch_path,git_url) is False: return False
			#try to switch branches
			if git_branch not in (None,'',False):
				if self.git_checkout(branch_path, git_branch) is False: return False
		#try post install script
		if post_install_script not in (None,'',False):
			if self.install_script(branch_path, post_install_script) is False: return False
		
		return True
		
	def git_clone(self,branch_path,git_url):
		self.logger("Cloning repo: "+git_url)
		return self.command('cd '+branch_path+" && git clone --recursive "+git_url+" .","Problem cloning repository!")
		
	def git_checkout(self, branch_path, git_branch):
		self.logger("Checking out branch: "+git_branch)
		return self.command('cd '+branch_path+" && git checkout "+git_branch,"Problem switching branch!");
	
	def git_hash(self,pull_path,long_hash=True):
		#git log --pretty=format:'%h' -n 1 #or H for long hash
		try:
			hash_type='H'
			if long_hash is False: hash_type='h'
			
			command='cd '+pull_path+" && git log --pretty=format:'%"+hash_type+"' -n 1"
			self.logger(command)
			output = subprocess.check_output(command,shell=True, stderr=subprocess.STDOUT ).decode()
			self.logger(output)
			return output.strip("'")
		except subprocess.CalledProcessError as e:
			self.logger(e.output.decode())
			self.logger("Failed to git log")
			return False
	def git_pull(self, pull_path):
		try:
			return subprocess.check_output('cd '+pull_path+' && git pull',shell=True,stderr=subprocess.STDOUT).decode()
		except subprocess.CalledProcessError as e:
			self.logger(e.output.decode())
			self.logger("Failed to git pull")
			return False
	def install_script(self, branch_path, script):
		install_script=script.splitlines()
		#pprint(install_script)
		self.logger("Running install script.")

		for step in install_script:
			if (len(step) == 0) or (step[0] == '#'): 
				continue
			#TODO: choose if to ignore errors or not...
			result=self.command('cd '+branch_path+" && "+step, "Problem running install script!") 
			if False and result is False: #turn to true to cancel on error
				return False
		return True

	def pull(self, branch_path, task):
		pull_path=branch_path+'/'+task['git_pull_dir']
		
		#get start hash to compare
		hashshort = self.git_hash(pull_path,False)
		if hashshort is False: return False
		hashlong = self.git_hash(pull_path,True)	
		#git pull new code
		gitoutput=self.git_pull(pull_path)
		#get end hash to see if we have new code
		newhashshort = self.git_hash(pull_path,False)
		newhashlong = self.git_hash(pull_path,True)

		print(hashlong)
		print(gitoutput)
		print(newhashlong)
		
		if args['test'] is not False or hashlong != newhashlong or self.new_repo==True:
			for build in task['builds']:
				pprint(build['work_dir'])
				self.make(branch_path, build,hashshort,hashlong,gitoutput,newhashshort,newhashlong)
	def make_clean(self, work_path):
		self.command('cd '+work_path+' && make clean', 'Make clean failed!')
	def make(self, branch_path, build,hashshort,hashlong,gitoutput,newhashshort,newhashlong):
		#setup output and work paths
		output_path=branch_path
		if build['output_dir'] not in (None,'',False):
			output_path=output_path + '/' + build['output_dir']
		work_path=branch_path
		if build['work_dir'] not in (None,'',False):
			work_path=work_path + '/' + build['work_dir']
			
		result={}
		print('Preparing build report')
		timestampstart=time.time()
		self.make_clean(work_path)
		try:
			result['error']='0';
			command='cd '+work_path+' && '+build['make_command']
			self.logger(command)
			makeoutput=subprocess.check_output(command, shell=True,stderr=subprocess.STDOUT).decode()
			self.logger(makeoutput)
		except subprocess.CalledProcessError as e:
			result['error']='1'
			self.logger(e.returncode)
			makeoutput=str(e.output.decode())
			self.logger(makeoutput)

		#create data structure
		result['timestamp']={}
		result['timestamp']['start']=timestampstart
		result['timestamp']['stop']=time.time()
		result['autobuild_id']=build['autobuild_id']
		result['starthashshort']=hashshort
		result['starthashlong']=hashlong
		result['endhashshort']=newhashshort
		result['endhashlong']=newhashlong
		result['gitoutput']=gitoutput
		result['makeoutput']=makeoutput
		result['apikey']=build['api_key']
		result['response']='json'

		#base64 encode file
		firmware_path=output_path + '/' + build['output_file']
		if os.path.exists(firmware_path):
			print('Base 64 encoding file')
			with open(firmware_path, "rb") as firmware: 
				result['base64encbin']= base64.b64encode(firmware.read()).decode()

		#upload .json to API
		print("Dumping JSON")	
		dump_path=work_path + '/' + 'result.json'
			
		with open(dump_path, 'w') as outfile:
			json.dump(result, outfile, indent=4, sort_keys=False)
			
		print("Uploading JSON")
		with open(dump_path, 'rb') as f: 
			r = requests.post(build['api_url'], files={'result': f})	
		#pprint(r)
		#pprint(r.text)
		self.make_clean(work_path)

ab=autoBuild()

while(True):
	ab.runTasks();
	print('sleep')
	#sleep for configured number of minutes
	time.sleep(args['interval']*60)



