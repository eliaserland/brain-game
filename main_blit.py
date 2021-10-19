import argparse
import time
import logging
import random
import numpy as np

import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, WindowFunctions, DetrendOperations

from matplotlib import pyplot as plt
logging.getLogger('matplotlib.font_manager').disabled = True

programName = 'BrainGame Curiosum'

fps = None
lastTime = time.time()

class Graph:
	def __init__(self, board_shim):
		self.board_id = board_shim.get_board_id()
		self.board_shim = board_shim
		self.exg_channels = BoardShim.get_exg_channels(self.board_id)
		self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
		self.update_speed_ms = 10
		self.window_size = 4 
		self.num_points = self.window_size * self.sampling_rate
		self.time_stamp_channel = BoardShim.get_timestamp_channel(self.board_id)
		self.data = np.zeros((BoardShim.get_num_rows(self.board_id), self.num_points))
		self.time = list(reversed(-np.arange(0, self.num_points)/self.sampling_rate))
		
		# ONLY TEMPORARY
		self.exg_channels = [1, 2, 3, 4, 5, 6, 7, 8]
		
		# Initialize plots
		self._init_timeseries()

		# Update plots, until program end.
		self.running = True
		while self.running:
			self.update()

	def _init_timeseries(self):
		ylim = 20
		self.plots = list()
		self.curves = list()

		fig, axes = plt.subplots(len(self.exg_channels), 1, figsize=(8, 8))
		ln = list()
		for i, ax in enumerate(axes):
			(ln_tmp,) = ax.plot(self.time, self.data[i], animated=True, linewidth=1.)
			ln.append(ln_tmp)
			ax.set_ylim(-200, 200)

		plt.show(block=False)
		plt.pause(0.1)

		bg = fig.canvas.copy_from_bbox(fig.bbox)

		for i, ax in enumerate(axes):
			ax.draw_artist(ln[i])
		fig.canvas.blit(fig.bbox)

		# Set trigger when when window is closed.
		fig.canvas.mpl_connect('close_event', self._on_close)

		self.fig = fig
		self.axes = axes
		self.ln = ln
		self.bg = bg
		print("----INITIALIZATION COMPLETED----")


	def _on_close(self, event):
		self.running = False


	def update(self):
		global fps, lastTime
		# Get data from board
		board_data = self.board_shim.get_current_board_data(self.num_points)
		series_len = board_data.shape[1]
		self.data[:, (self.num_points-series_len):] = board_data

		self.fig.canvas.restore_region(self.bg)
		for i, channel in enumerate(self.exg_channels):
			self.ln[i].set_ydata(self.data[channel])
		for i, ax in enumerate(self.axes):
			ax.draw_artist(self.ln[i])

		self.fig.canvas.blit(self.fig.bbox)
		self.fig.canvas.flush_events()
		
		now = time.time()
		dt = now - lastTime
		lastTime = now
		if fps is None:
			fps = 1.0/dt
		else:
			s = np.clip(dt*3., 0, 1)
			fps = fps * (1-s) + (1.0/dt) * s
		print(f" {fps:0.2f} fps", end='\r')


def main():
	# Set logging level.
	BoardShim.enable_dev_board_logger()
	logging.basicConfig(level=logging.DEBUG)

	# Parse command line arguments. Use docs to check which parameters are 
	# required for specific board, e.g. for Cyton - set serial port.
	parser = argparse.ArgumentParser()
	parser.add_argument('--timeout',     type=int, required=False, default=0, help='timeout for device discovery or connection',)
	parser.add_argument('--ip-port',     type=int, required=False, default=0, help='ip port',)
	parser.add_argument('--ip-protocol', type=int, required=False, default=0, help='ip protocol, check IpProtocolType enum')
	parser.add_argument('--ip-address',      type=str, required=False, default='', help='ip address')
	parser.add_argument('--serial-port',     type=str, required=False, default='', help='serial port')
	parser.add_argument('--mac-address',     type=str, required=False, default='', help='mac address')
	parser.add_argument('--other-info',      type=str, required=False, default='', help='other info')
	parser.add_argument('--streamer-params', type=str, required=False, default='', help='streamer params')
	parser.add_argument('--serial-number',   type=str, required=False, default='', help='serial number')
	parser.add_argument('--file',            type=str, required=False, default='', help='file')
	parser.add_argument('--board-id',        type=int, required=False, default=BoardIds.SYNTHETIC_BOARD, help='board id, check docs to get a list of supported boards')
	args = parser.parse_args()

	# Set parsed parameters in BrainFlowInputParams structure.
	params = BrainFlowInputParams()
	params.ip_port = args.ip_port
	params.serial_port = args.serial_port
	params.mac_address = args.mac_address
	params.other_info = args.other_info
	params.serial_number = args.serial_number
	params.ip_address = args.ip_address
	params.ip_protocol = args.ip_protocol
	params.timeout = args.timeout
	params.file = args.file

	try:
		# Start session.
		board_shim = BoardShim(args.board_id, params)
		board_shim.prepare_session()
		board_shim.start_stream(450000, args.streamer_params)
		
		# Start plotting.
		g = Graph(board_shim)
		
	except BaseException as e:
		# Error handling.
		logging.warning('Exception', exc_info=True)
	
	finally:
		# End session.
		logging.info('End')
		if board_shim.is_prepared():
			logging.info('Releasing session')
			board_shim.release_session()


if __name__ == '__main__':
	main()
