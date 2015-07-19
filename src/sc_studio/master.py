'''
sc_studio.master

Author: Ming Tsang
Copyright (c) 2014-2015 HKUST SmartCar Team
Refer to LICENSE for details
'''

import binascii
import codecs
from collections import deque
import logging
import os
import sys
import subprocess
import time
import serial
from sc_studio import config, console_utils, message
from threading import Thread, Lock, Semaphore

class Master(object):
	VERSION_STR = "0.9 dev"

	# id, label, module name, class name
	_SELECTIONS = [('0', "Raw", "_on_choose_raw"),
			('1', "String", "_on_choose_string"),
			('2', "CCD graph", "_on_choose_ccd_graph"),
			('3', "CCD image", "_on_choose_ccd_image"),
			('4', "Camera", "_on_choose_camera"),
			('5', "Graph", "_on_choose_graph"),
			('t', "Send text", "_on_choose_send_text"),
			('h', "Send hex", "_on_choose_send_hex"),
			('x', "Exit", "_on_choose_exit")]

	def __init__(self, params : list):
		self._dev = params["dev"]
		self._preinput = params["preinput"] if "preinput" in params else ""

		self._com = None
		self._views = []
		self._raw_processes = []

		self._is_i_thread_run = True
		self._i_thread = Thread(target = self._i_thread_main)
		self._msg_builder = message.MessageBuilder()

		self._is_o_thread_run = True
		self._o_thread = Thread(target = self._o_thread_main)
		self._out_queue = deque()
		self._out_queue_mutex = Lock()
		self._out_queue_semaphore = Semaphore(0)

	def run(self):
		print("ScStudio " + Master.VERSION_STR)
		print("Device: " + self._dev)
		print("Connecting to " + self._dev + "...")
		while not self._connect():
			print("Failed connecting to " + self._dev + ", retrying...")
		self._i_thread.start()
		self._o_thread.start()
		self._run_menu()

	def _i_thread_main(self):
# 		i = 0
# 		ary = [b"00", b"10", b"20", b"30", b"40", b"50", b"60", b"70", b"80",
# 				b"90", b"A0", b"B0", b"C0", b"D0", b"E0", b"F0"]
#
# 		while self._is_thread_run:
# 			line = bytearray();
# 			for j in range(8):
# 				for k in range(i, i + 16):
# 					line += ary[(j + k) % 16]
# 			i = (i + 1) % 16
# 			msg = message.Message(config.MSG_CCD_DATA, line);
# 			self._dispatch(msg)
# 			time.sleep(1.0)

		while self._is_i_thread_run:
			self._com.timeout = .01
			data = self._com.read(0xFF)
			for d in data:
				msg = self._msg_builder.push(d)
				if msg is not None:
					self._dispatch(msg)

			remove_processes = []
			for p in self._raw_processes:
				try:
					p.stdin.write(data)
				except BrokenPipeError:
					# likely closed
					remove_processes.append(p)
			if remove_processes:
				self._raw_processes[:] = [p for p in self._raw_processes
						if p not in remove_processes]

	def _o_thread_main(self):
		while self._is_o_thread_run:
			if not self._out_queue_semaphore.acquire(timeout = 1):
				continue
			self._out_queue_mutex.acquire()
			try:
				send = self._out_queue.popleft()
				self._com.write(send)
			finally:
				self._out_queue_mutex.release()

	def _dispatch(self, msg : message.Message):
		remove_views = []
		for v in self._views:
			try:
				if msg.token in v[1]:
					hex_str = codecs.encode(bytes(msg.data), "hex")
					v[0].stdin.write(hex_str)
					v[0].stdin.write(b'\n')
					v[0].stdin.flush()
			except BrokenPipeError:
				# likely closed
				remove_views.append(v)
		if remove_views:
			self._views[:] = \
					[v for v in self._views if v not in remove_views]

	def _on_choose_raw(self):
		cmd = sys.executable + ' ' + os.path.dirname(os.path.realpath(__file__)) \
				+ "/main.py -vraw"
		p = subprocess.Popen(cmd, stdin = subprocess.PIPE, shell = True)
		self._raw_processes.append(p)

	def _on_choose_string(self):
		cmd = sys.executable + ' ' + os.path.dirname(os.path.realpath(__file__)) \
				+ "/main.py -vstring"
		p = subprocess.Popen(cmd, stdin = subprocess.PIPE, shell = True)
		self._views.append((p, [config.MSG_STRING]))

	def _on_choose_ccd_graph(self):
		while True:
			try:
				ccd_id = int(self._get_input("CCD id:\n> "))
				break
			except ValueError:
				print("Input error")
		cmd = sys.executable + ' ' + os.path.dirname(os.path.realpath(__file__)) \
				+ "/main.py -vccd_graph --varg=ccd_id=" + str(ccd_id)
		p = subprocess.Popen(cmd, stdin = subprocess.PIPE, shell = True)
		self._views.append((p, [config.MSG_CCD_DATA]))

	def _on_choose_ccd_image(self):
		while True:
			try:
				ccd_id = int(self._get_input("CCD id:\n> "))
				break
			except ValueError:
				print("Input error")
		cmd = sys.executable + ' ' + os.path.dirname(os.path.realpath(__file__)) \
				+ "/main.py -vccd_image --varg=ccd_id=" + str(ccd_id)
		p = subprocess.Popen(cmd, stdin = subprocess.PIPE, shell = True)
		self._views.append((p, [config.MSG_CCD_DATA]))

	def _on_choose_camera(self):
		while True:
			try:
				multiplier = int(self._get_input("View size multiplier:\n> "))
				break
			except ValueError:
				print("Input error")
		cmd = sys.executable + ' ' + os.path.dirname(os.path.realpath(__file__)) \
				+ "/main.py -vcamera --varg=multiplier=" + str(multiplier)
		p = subprocess.Popen(cmd, stdin = subprocess.PIPE, shell = True)
		self._views.append((p, [config.MSG_CAMERA]))

	def _on_choose_graph(self):
		while True:
			try:
				ids = self._get_input("ids (separate with space):\n> ")\
						.split(' ')
				# Make sure all could be casted to int
				_ = [int(i) for i in ids]
				labels = self._get_input("labels (separate with space):\n> ")\
						.split(' ')
				colors = self._get_input("colors (separate with space):\n> ")
				if colors:
					colors = colors.split(' ')
				min_val = float(self._get_input("min:\n> "))
				max_val = float(self._get_input("max:\n> "))
				break
			except ValueError:
				print("Input error")
		cmd = sys.executable + ' ' + os.path.dirname(os.path.realpath(__file__)) \
				+ "/main.py -vgraph --varg=ids=\"" + ' '.join(ids) \
				+ "\" --varg=labels=\"" + ' '.join(labels) + "\" --varg=min=" \
				+ str(min_val) + " --varg=max=" + str(max_val)
		if colors:
			cmd += " --varg=colors=\"%s\"" % ' '.join(colors)
		p = subprocess.Popen(cmd, stdin = subprocess.PIPE, shell = True)
		self._views.append((p, [config.MSG_GRAPH]))

	def _on_choose_send_text(self):
		inp = self._get_input("> ")
		byte_data = inp.encode(encoding = "UTF-8").decode("unicode_escape")\
				.encode(encoding = "UTF-8")
		self._out_queue_mutex.acquire()
		try:
			self._out_queue.append(byte_data)
			self._out_queue_semaphore.release()
		finally:
			self._out_queue_mutex.release()

	def _on_choose_send_hex(self):
		while True:
			inp = self._get_input("> ")
			if len(inp) % 2:
				print("Number of char is odd")
				continue
			try:
				byte_data = binascii.unhexlify(inp)
			except:
				print("Error input")
				continue

			self._out_queue_mutex.acquire()
			try:
				self._out_queue.append(byte_data)
				self._out_queue_semaphore.release()
			finally:
				self._out_queue_mutex.release()
			break

	def _on_choose_exit(self):
		print("Killing views...")
		for v in self._views:
			try:
				v[0].stdin.write(codecs.encode(b"\xDC\xCD", "hex"))
				v[0].terminate()
			except:
				pass
		for p in self._raw_processes:
			try:
				p.terminate()
			except:
				pass
		print("OK")
		self._com.close()

		print("Ending process...")
		self._is_i_thread_run = False
		self._is_o_thread_run = False
		self._i_thread.join()
		self._o_thread.join()
		sys.exit(0)

	def _connect(self) -> bool :
		try:
			self._com = serial.Serial(port = self._dev, baudrate = 115200,
					bytesize = serial.EIGHTBITS, parity = serial.PARITY_NONE,
					stopbits = serial.STOPBITS_ONE, timeout = .01,
					writeTimeout = .01)
			return True
		except serial.serialutil.SerialException:
			return False

	def _run_menu(self):
		while True:
			self._print_menu()
			try:
				choice = self._get_input("> ")
				index = [s[0] for s in Master._SELECTIONS].index(choice)
				getattr(self, Master._SELECTIONS[index][2])()
			except ValueError:
				print("Input error")

	def _print_menu(self):
		# console_utils.clear()
		print("ScStudio " + Master.VERSION_STR)
		print("Select view:")
		for pos, label, _ in Master._SELECTIONS:
			print(str(pos) + ". " + label)

	def _get_input(self, label) -> str:
		if self._preinput:
			found = self._preinput.find(',')
			if found != -1:
				product = self._preinput[:found];
				self._preinput = self._preinput[found + 1:]
			else:
				product = self._preinput;
				self._preinput = None
			print(label + product)
			return product
		else:
			return input(label)
