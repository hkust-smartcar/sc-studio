'''
sc_studio.view

Author: Ming Tsang
Copyright (c) 2014-2015 HKUST SmartCar Team
Refer to LICENSE for details
'''

import codecs
import collections
import logging
import sys
from threading import Thread, Lock

class View(object):
	_KILL_SEQ = codecs.encode(b"\xDC\xCD", "hex")

	def __init__(self, params):
		self._is_thread_run = True
		self._input_thread = Thread(target = self._io_thread_main)
		self._input_queue = collections.deque()
		self._input_queue_mutex = Lock()

	def run(self):
		self._input_thread.start()

	def get_input(self):
		if not self._input_queue:
			return None

		self._input_queue_mutex.acquire()
		try:
			text = self._input_queue.popleft()
		finally:
			self._input_queue_mutex.release()
			return text

	def on_new_input(self):
		pass

	def on_dismiss(self):
		pass

	def join_io_thread(self):
		self._is_thread_run = False
		self._input_thread.join()

	def is_test_input(self):
		return False

	def gen_test_input(self):
		return None

	def _io_thread_main(self):
		while self._is_thread_run:
			if not self.is_test_input():
				text = sys.stdin.readline()
			else:
				if "test_gen" not in locals():
					test_gen = self.gen_test_input()
				text = next(test_gen)

			if not text:
				logging.error("Failed while readline")
				self.on_dismiss()
				return

			text = text[:-1]
			self._input_queue_mutex.acquire()
			try:
				self._input_queue.append(text)
			finally:
				self._input_queue_mutex.release()
			self.on_new_input()
