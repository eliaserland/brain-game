import argparse
import time
import logging
import random

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore

import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, WindowFunctions, DetrendOperations

# My stuff
import matplotlib.pyplot as plt



class Graph:
	def __init__(self, board_shim):
		self.board_id = board_shim.get_board_id()
		self.board_shim = board_shim
		self.exg_channels = BoardShim.get_exg_channels(self.board_id)
		self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
		self.update_speed_ms = 5
		self.window_size = 5
		self.num_points = self.window_size * self.sampling_rate

		self.exg_channels = [1, 2, 3, 4, 5, 6, 7, 8]
		
		for count, channel in enumerate(self.exg_channels):
			print(count, channel)

		self.app = QtGui.QApplication([])
		self.win = pg.GraphicsWindow(title='BrainFlow Plot',size=(800, 600))

		self._init_timeseries()

		timer = QtCore.QTimer()
		timer.timeout.connect(self.update)
		timer.start(self.update_speed_ms)
		QtGui.QApplication.instance().exec_()


	def _init_timeseries(self):
		self.plots = list()
		self.curves = list()
		for i in range(len(self.exg_channels)):
			p = self.win.addPlot(row=i,col=0)
			p.showAxis('left', True)
			p.setMenuEnabled('left', True)
			p.showAxis('bottom', True)
			p.setMenuEnabled('bottom', True)
			if i == 0:
				p.setTitle('TimeSeries Plot')
			self.plots.append(p)
			curve = p.plot()
			self.curves.append(curve)

	def update(self):
		data = self.board_shim.get_current_board_data(self.num_points)
		print(data.shape)
		avg_bands = [0, 0, 0, 0, 0]
		for count, channel in enumerate(self.exg_channels):
			# plot timeseries
			#DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
			DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
										FilterTypes.BUTTERWORTH.value, 0)
			DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
										FilterTypes.BUTTERWORTH.value, 0)
			DataFilter.perform_bandstop(data[channel], self.sampling_rate, 50.0, 4.0, 2,
										FilterTypes.BUTTERWORTH.value, 0)
			DataFilter.perform_bandstop(data[channel], self.sampling_rate, 60.0, 4.0, 2,
										FilterTypes.BUTTERWORTH.value, 0)
			self.curves[count].setData(data[channel].tolist())

		self.app.processEvents()

class Plot:
	def __init__(self, board_shim):
		# Save board_shim and associated values.
		self.board_shim = board_shim
		self.board_id = board_shim.get_board_id()
		self.exg_channels = BoardShim.get_exg_channels(self.board_id)
		self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
		
		# 
		self.update_speed_ms = 50
		self.window_size = 4
		self.num_points = self.window_size * self.sampling_rate

		self.app = QtGui.QApplication([])
		self.win = pg.GraphicsWindow(title='BrainFlow Plot',size=(800, 600))


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
