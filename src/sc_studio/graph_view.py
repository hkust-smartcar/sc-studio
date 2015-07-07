'''
sc_studio.graph_view

Author: Ming Tsang
Copyright (c) 2014-2015 HKUST SmartCar Team
Refer to LICENSE for details
'''

from collections import deque
import binascii
import logging
import random
import struct
import time
import tkinter
from tkinter import Tk, Canvas
from sc_studio import config
from sc_studio.view import View
from time import sleep

class _GraphData(object):
	def __init__(self):
		self._values = deque()

	def append(self):
		self._values.append(None)

	def put_value(self, val):
		self._values[-1] = val

	def get_values(self):
		return self._values

	def get_value(self, pos):
		return self._values[pos]

	def size(self):
		return len(self._values)

	def shrink(self, size):
		while self.size() > size:
			self._values.popleft()

class _GraphDataView(object):
	def __init__(self, color):
		self._color = color
		self._graph_lines = []
		self._graph_coords = deque()

	def populate(self, values, max_val, diff_val, graph_x, graph_h):
		self._graph_coords.clear()
		x = graph_x
		for val in values:
			if val is not None:
				ratio = (max_val - val) / diff_val
				y = graph_h * ratio + GraphView.WIN_PADDING_Y
				self._graph_coords.append((x, y))
			x += GraphView.POINT_MARGIN

	def draw(self, canvas):
		gen = self._gen_line_coord()
		pos = 0
		for lc in gen:
			if pos >= len(self._graph_lines):
				l = canvas.create_line(lc, width = 1, fill = self._color)
				self._graph_lines.append(l)
			else:
				canvas.coords(self._graph_lines[pos], lc)
			pos += 1
		while pos < len(self._graph_lines):
			canvas.delete(self._graph_lines[-1])
			self._graph_lines.pop()

	def clear_lines(self):
		self._graph_lines.clear()

	def _gen_line_coord(self):
		prev = None
		for c in self._graph_coords:
			if prev is None:
				prev = c
			else:
				yield prev + c
				prev = c

class GraphView(View):
	WIN_PADDING_Y = 16
	POINT_MARGIN = 2

	def __init__(self, params):
		super(GraphView, self).__init__(params)

		self._ids = params["ids"] if "ids" in params else ""
		self._ids = [int(i) for i in self._ids.split(' ')]
		self._labels = params["labels"] if "labels" in params else ""
		self._labels = [l for l in self._labels.split(' ')]
		self._colors = [c for c in params["colors"].split(' ')] if "colors" in \
				params else None
		if not self._colors:
			self._colors = self._get_auto_colors(len(self._ids))
		if not len(self._ids) == len(self._labels) == len(self._colors):
			raise RuntimeError("ids, labels and colors must share the same size")

		self._min = float(params["min"]) if "min" in params else -1000
		self._max = float(params["max"]) if "max" in params else 1000
		if self._min > self._max:
			self._min, self._max = self._max, self._min
		self._diff = abs(self._max - self._min)

		self._data = [_GraphData() for _ in range(len(self._ids))]
		self._data_view = [_GraphDataView(self._colors[i]) for i in range(
				len(self._ids))]
		self._graph_x = 0

		self._tk = Tk()
		self._tk.title("Graph view %s" % str(self._labels))

		self._canvas = Canvas(self._tk, width = 640, height = 480)
		self._canvas.pack(fill = tkinter.BOTH, expand = 1)

		self._tk.update()
		self._win_size = self._tk.winfo_width(), self._tk.winfo_height()
		# graph_rect only works as providing the area but not coord
		self._graph_rect = self._win_size
		self._tk.minsize(320, 240)
		self._tk.protocol("WM_DELETE_WINDOW", self.on_press_close)

		self._tk.bind("<Configure>", self.on_config)
		self._canvas.config(background = config.COL_GREY_900)

		self._full_redraw()

		self._file = open("graph_%s_%i.csv" % (str(self._labels),
				int(time.time() * 1000)), "w")
		self._file.write(','.join(self._labels) + '\n')

		self._tk.after(16, self._refresh)

	def run(self):
		super(GraphView, self).run()
		self._tk.mainloop()

	def on_new_input(self):
		try:
			hex_data = binascii.unhexlify(self.get_input())
		except TypeError as e:
			logging.debug(str(e))
			return

		count = int(len(hex_data) / GraphView._MSG_SIZE)
		for i in (x * 6 for x in range(count)):
			if hex_data[i] in self._ids:
				value_type = hex_data[i + 1]
				value_bytes = hex_data[i + 2:i + 6]
				if value_type == GraphView._MSG_TYPE_INT:
					value = int.from_bytes(value_bytes, byteorder = "big",
							signed = True)
				elif value_type == GraphView._MSG_TYPE_FLOAT:
					value = struct.unpack(">f", value_bytes)[0]
				else:
					logging.error("Unknown type: " + str(value_type))
					continue
				self._tk.after_idle(self._put_value, hex_data[i], value)

	def on_dismiss(self):
		self._tk.after_idle(self.on_press_close)

	def on_press_close(self):
		self._tk.destroy()
		self.join_io_thread()

	def on_config(self, event):
		win_size = (event.width, event.height)
		if win_size != self._win_size:
			self._win_size = win_size
			self._full_redraw()

	def is_test_input(self):
		return False

	def gen_test_input(self):
		while True:
			for i in range(int(self._min), int(self._max)):
				sleep(0.1)
				yield "0000%08x" % (random.randrange(-100, 100) & 0xFFFFFFFF) \
						+ "0100%08x\n" % (i & 0xFFFFFFFF)

	def _put_value(self, id, value):
		pos = self._ids.index(id)
		if self._data[pos].size() == 0:
			for d in self._data:
				d.append()
		elif self._data[pos].get_value(-1) is not None:
			for d in self._data:
				d.append()
			if self._data[pos].size() > 1:
				self._write_prev_records()
		self._data[pos].put_value(value)

		graph_w = self._win_size[0] - self._graph_x;
		count = int(graph_w / GraphView.POINT_MARGIN + 1)

		for d in self._data:
			d.shrink(count)

	def _write_prev_records(self):
		write = ','.join((str(d.get_value(-2)) for d in self._data)) + '\n'
		self._file.write(write)
		self._file.flush()

	def _refresh(self):
		self._redraw_graph()
		self._tk.after(16, self._refresh)

	def _full_redraw(self):
		self._canvas.delete("all")
		bounding_box = self._redraw_data_labels()
		self._graph_rect = 0, 0, self._win_size[0], bounding_box[1]
		self._redraw_y_labels()
		for v in self._data_view:
			v.clear_lines();
		self._redraw_graph()

	def _redraw_data_labels(self):
		top = self._win_size[1]
		x = GraphView._DATA_LABEL_PADDING
		for l, c in zip(self._labels, self._colors):
			t = self._canvas.create_text(x,
					self._win_size[1] - GraphView._DATA_LABEL_PADDING,
					anchor = tkinter.SW, fill = c, font = config.FONT,
					text = '-' + l)
			bounding_box = self._canvas.bbox(t)
			top = min(top, bounding_box[1])
			x = bounding_box[2] + GraphView._DATA_LABEL_PADDING
		return 0, top, x, self._win_size[1]

	def _redraw_y_labels(self):
		height = self._graph_rect[3] - self._graph_rect[1] \
				- GraphView.WIN_PADDING_Y * 2
		count = max(int(height / 50), 2)

		labels = []
		max_label_size = 0
		longest_label = None
		longest_label_i = None
		for i in range(count):
			ratio = i / (count - 1)
			value = self._max - self._diff * ratio
			value_label = ("%.2f" % value) if value % 1 != 0 else str(value)
			labels.append(value_label)
			if len(value_label) > max_label_size:
				max_label_size = len(value_label)
				longest_label = value_label
				longest_label_i = i

		label_id = self._canvas.create_text(0, height * (longest_label_i \
						/ (count - 1)) + GraphView.WIN_PADDING_Y,
				anchor = tkinter.W, fill = config.COL_GREY_100,
				font = config.FONT, text = longest_label)
		bounding_box = self._canvas.bbox(label_id)
		width = bounding_box[2] - bounding_box[0]
		self._graph_x = width + GraphView.POINT_MARGIN

		for i in range(count):
			ratio = i / (count - 1)
			y = height * ratio + GraphView.WIN_PADDING_Y
			if i != longest_label_i:
				self._canvas.create_text(width, y, anchor = tkinter.E,
						fill = config.COL_GREY_100, font = config.FONT,
						text = labels[i])
			self._canvas.create_line(self._graph_x, y, self._graph_rect[2], y,
					fill = config.COL_GREY_700)

	def _redraw_graph(self):
		graph_h = self._graph_rect[3] - GraphView.WIN_PADDING_Y * 2
		for d, v in zip(self._data, self._data_view):
			v.populate(d.get_values(), self._max, self._diff, self._graph_x,
					graph_h)
			v.draw(self._canvas)

	def _get_auto_colors(self, size) -> list:
		product = GraphView._COLOR_REPO[:min(size, len(GraphView._COLOR_REPO))]
		while len(product) < size:
			product.append("#%06x" % random.randrange(0xFFFFFF))
		return product

	_LABEL_SIZE = 10
	_DATA_LABEL_PADDING = 8
	_MSG_SIZE = 6
	_MSG_TYPE_INT = 0
	_MSG_TYPE_FLOAT = 1
	_COLOR_REPO = ["#F44336", "#4CAF50", "#2196F3", "#FFEB3B", "#607D8B",
			"#9C27B0", "#009688", "#673AB7", "#795548"]
