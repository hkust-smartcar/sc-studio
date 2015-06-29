'''
sc_studio.main

Author: Ming Tsang
Copyright (c) 2014-2015 HKUST SmartCar Team
Refer to LICENSE for details
'''

import getopt
import logging
import sys
from sc_studio import config

def _print_usage():
	print("Usage: main.py -d <device>")

def _start_master(view_args : dict):
	module = __import__("master")
	clz = getattr(module, "Master")
	app = clz(view_args)
	app.run()

def _start_raw(view_args : dict):
	module = __import__("raw_view")
	clz = getattr(module, "RawView")
	app = clz(view_args)
	app.run()

def _start_string(view_args : dict):
	module = __import__("string_view")
	clz = getattr(module, "StringView")
	app = clz(view_args)
	app.run()

def _start_ccd_graph(view_args : dict):
	module = __import__("ccd_graph_view")
	clz = getattr(module, "CcdGraphView")
	app = clz(view_args)
	app.run()

def _start_ccd_image(view_args : dict):
	module = __import__("ccd_image_view")
	clz = getattr(module, "CcdImageView")
	app = clz(view_args)
	app.run()

def _init_logging():
	if not config.LOGFILE:
		return

	root = logging.getLogger()
	root.setLevel(logging.DEBUG)
	sh = logging.FileHandler(config.LOGFILE)
	sh.setFormatter(logging.Formatter(
			"[%(asctime)s] %(levelname)s: (%(module)s) %(message)s"))
	root.addHandler(sh)

def main(argv : list):
	_init_logging()

	dev = ""
	view_name = ""
	view_args = {}

	try:
		opts, _ = getopt.gnu_getopt(argv, "d:hv:", ["dev=", "help", "varg="])
		for opt, arg in opts:
			if opt in ("-d", "--dev"):
				dev = arg
			elif opt in ("-h", "--help"):
				_print_usage()
			elif opt == "-v":
				view_name = arg
			elif opt == "--varg":
				index = arg.find('=')
				if index == -1:
					view_args[arg] = True
				else:
					view_args[arg[:index]] = arg[index + 1]
	except (getopt.GetoptError, ValueError):
		_print_usage()
		sys.exit(2)

	if not dev and not view_name:
		_print_usage()
	elif view_name:
		if config.REMOTE_DEBUG:
			sys.path.append(config.PYSRC)
			import pydevd
			pydevd.settrace(suspend = False)
	else:
		view_name = "master"
		view_args["dev"] = dev

	globals()["_start_" + view_name](view_args)

if __name__ == '__main__':
	main(sys.argv[1:])
