config=[
	#
	# Each feed provides pull and build tasks
	# 
	{ 
		"api_url":"http://bp.test/api/autobuild", # Where to get JSON feed of build tasks
		"api_key":"", # Info field. API key to access the build tasks feed. Depends on your implementation
		"repo_store":"/root/autobuild" # Where to save and compile the builds
	}#,
	# The script can run build tasks from multiple sources by adding new tasts to the array
	#{ 
	#	"api_url":"http://anothersite.test/api/autobuild", #different feed of build tasks
	#	"api_key":"",
	#	"repo_store":"/root/autobuild2" #different working folder
	#}
]