'''
sc_studio.message

Author: Ming Tsang
Copyright (c) 2014-2015 HKUST SmartCar Team
Refer to LICENSE for details
'''

import logging
from sc_studio import config

class Message(object):
	def __init__(self, token, data):
		self.token = token
		self.data = data

class MessageBuilder(object):
	def __init__(self):
		self._reset()

	def push(self, data) -> Message:
		if not self._is_start and data != config.MSG_BEGIN:
			pass
		elif not self._is_start:
			self._is_start = True
		elif self._token is None:
			if data in config.MSG_TOKENS:
				self._token = data
			else:
				logging.error("Unknown msg token")
				self._reset()
		elif self._size is None:
			self._buf.append(data)
			if len(self._buf) >= 3 or not (data & 0x80):
				self._size = self._parse_size(self._buf)
				self._buf = []
		elif len(self._buf) < self._size:
			self._buf.append(data)
		else:
			if data == config.MSG_END:
				product = Message(self._token, self._buf)
				self._reset()
				return product
			else:
				logging.error("End byte mismatch")
				self._reset()

		return None

	def _reset(self):
		self._is_start = False
		self._token = None
		self._size = None
		self._buf = []

	def _parse_size(self, buf) -> int:
		size = 0
		for i in range(3):
			if i >= len(buf):
				break
			size |= (buf[i] if i == 2 else (buf[i] & 0x7F)) << (i * 7)
		return size
