'''
sc_studio.console_utils

Author: Ming Tsang
Copyright (c) 2014-2015 HKUST SmartCar Team
Refer to LICENSE for details
'''

import logging
import os
import shlex
import subprocess
import sys

def clear():
	os.system(["clear", "cls"][os.name == "nt"])

def run_in_new_console(cmd, stdin = None, stdout = None, stderr = None):
	if sys.platform.startswith(("win32", "cygwin")):
		cmd_ = "start " + sys.executable + " " + cmd
	elif sys.platform.startswith(("darwin")):
		cmd_ = "open -W -a Terminal.app " + sys.executable + " " + cmd
	else:
		cmd_ = "x-terminal-emulator -e sh -c \"" + sys.executable + ' ' + cmd \
				+ '"'

	# args = shlex.split(cmd_);
	logging.debug(cmd_)
	return subprocess.Popen(cmd_, stdin = stdin, stdout = stdout,
			stderr = stderr, shell = True)
