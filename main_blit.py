import argparse
import time
import logging
import numpy as np

from collections import deque

#import pyqtgraph as pg
#from pyqtgraph.Qt import QtGui, QtCore
#import pyqtgraph.ptime as ptime

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes, WindowFunctions, DetrendOperations
from brainflow.ml_model import BrainFlowMetrics, BrainFlowClassifiers, BrainFlowModelParams, MLModel

import matplotlib
#matplotlib.use('GTK3Agg')
from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec
logging.getLogger('matplotlib').disabled = True

programName = 'BrainGame Curiosum'

fps = -1
lastTime = time.time()

class BlitManager:
	def __init__(self, canvas, animated_artists=()):
		"""
		Parameters
		----------
		canvas : FigureCanvasAgg
		The canvas to work with, this only works for sub-classes of the Agg
		canvas which have the `~FigureCanvasAgg.copy_from_bbox` and
		`~FigureCanvasAgg.restore_region` methods.

		animated_artists : Iterable[Artist]
		List of the artists to manage
		"""
		self.canvas = canvas
		self._bg = None
		self._artists = []

		for a in animated_artists:
			self.add_artist(a)
		# grab the background on every draw
		self.cid = canvas.mpl_connect("draw_event", self.on_draw)

	def on_draw(self, event):
		"""Callback to register with 'draw_event'."""
		cv = self.canvas
		if event is not None:
			if event.canvas != cv:
				raise RuntimeError
		self._bg = cv.copy_from_bbox(cv.figure.bbox)
		self._draw_animated()

	def add_artist(self, art):
		"""
		Add an artist to be managed.

		Parameters
		----------
		art : Artist

		The artist to be added.  Will be set to 'animated' (just
		to be safe).  *art* must be in the figure associated with
		the canvas this class is managing.

		"""
		if art.figure != self.canvas.figure:
			raise RuntimeError
		art.set_animated(True)
		self._artists.append(art)

	def _draw_animated(self):
		"""Draw all of the animated artists."""
		fig = self.canvas.figure
		for a in self._artists:
			fig.draw_artist(a)

	def update(self):
		"""Update the screen with animated artists."""
		cv = self.canvas
		fig = cv.figure
		# paranoia in case we missed the draw event
		if self._bg is None:
			self.on_draw(None)
		else:
			# restore the background
			cv.restore_region(self._bg)
			# draw all of the animated artists
			self._draw_animated()
			# update the GUI state
			cv.blit(fig.bbox)
		# let the GUI event loop process anything it has to do
		cv.flush_events()

class Graph:
	def __init__(self, board_shim, no_gui):
		self.board_id = board_shim.get_board_id()
		self.board_shim = board_shim
		self.eeg_channels = BoardShim.get_eeg_channels(self.board_id)
		self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
		self.window_size = 5
		self.num_points = self.window_size * self.sampling_rate
		self.timestamp_channel = BoardShim.get_timestamp_channel(self.board_id)
		self.data = np.zeros((BoardShim.get_num_rows(self.board_id), self.num_points))
		self.time = list(reversed(-np.arange(0, self.num_points)/self.sampling_rate))
		
		self.metric = deque([0], maxlen=self.num_points)
		self.metric_time = deque([time.time()], maxlen=self.num_points)
		self.no_gui = no_gui
		#print(BoardShim.get_board_descr(self.board_id))

		# Limit no. of channels if testing with synthetic data
		if self.board_id == BoardIds.SYNTHETIC_BOARD:
			self.eeg_channels = [1, 2, 3, 4, 5] #, 6, 7, 8]
		
		# Initialize plots
		if not self.no_gui:
			self._init_plot()
		else:
			time.sleep(1) # ONLY TEMPORARY

		# Initialize ML model
		self._init_ml_model()

		print("----INITIALIZATION COMPLETED----")
				

		# Update plots, until program end.
		self.running = True
		now = time.time()
		while self.running:
			# Gather data and update everything.
			self.update()

			# Limit update freq if needed ()
			lastTime = now
			now = time.time()
			dt = now-lastTime
			if dt <= 1/self.sampling_rate:
				time.sleep(1/self.sampling_rate - dt)



	def _init_plot(self):
		"""Initialize the time series and associated plots."""
		# Window limits of time series plot.
		ylim = 200 * 1.1
		
		# Create a figure.
		fig = plt.figure(constrained_layout=True)
		
		# Set gridspec for custom subplot layout.
		gs = GridSpec(len(self.eeg_channels), 2, figure=fig)
		axes = []
		# Create axes for the left column of time series plot.
		for i in range(len(self.eeg_channels)):
			ax = fig.add_subplot(gs[i, 0])
			axes.append(ax)

		# Right column
		ax = fig.add_subplot(gs[:len(self.eeg_channels)//2, 1])
		axes.append(ax)
		ax = fig.add_subplot(gs[len(self.eeg_channels)//2:, 1])
		axes.append(ax)


		#fig, axes = plt.subplots(len(self.eeg_channels), 1, figsize=(6, 6), sharex=True)
		#axes = axes.flatten()

		# Set sequential colormap
		#cmap = 'viridis'
		#colors = getattr(plt.cm, cmap)(np.linspace(0,1,len(axes)))
		colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

		# Add all lines 
		ln = list()
		for i, ax in enumerate(axes):
			if i < len(self.eeg_channels):
				(ln_tmp,) = ax.plot(self.time, self.data[self.eeg_channels[i]], animated=True, linewidth=0.8, color=colors[i%10])
				ln.append(ln_tmp)
				ax.set_ylim(-ylim, ylim)
				ax.set_xlim(np.min(self.time)*1.001, np.max(self.time))
				ax.tick_params(axis='x', labelsize=6)
				ax.tick_params(axis='y', labelsize=6)
				ax.set_ylabel("Pot (uV)", fontsize=6)
				if i == len(self.eeg_channels)-1:
					ax.set_xlabel("Time (s)", fontsize=6)
			else:
				(ln_tmp,) = ax.plot([0], self.metric, animated=True, linewidth=0.8, color=colors[i%10])
				ln.append(ln_tmp)
				ax.set_ylim(-0.01, 1.01)
				ax.set_xlim(-10, 0)

		# Add an FPS counter
		fr_number = axes[0].set_title("0")

		# Create the blitting manager, save all artists
		self.bm = BlitManager(fig.canvas, ln + [fr_number])
		self.ln = ln
		self.fr_number = fr_number

		# Make sure the window is on the screen and drawn
		plt.show(block=False)
		plt.pause(0.1)

		# Set trigger when when window is closed.
		fig.canvas.mpl_connect('close_event', self._on_close)
		fig.canvas.manager.set_window_title(programName)


	def _init_ml_model(self):
		"""Initialize the BrainFlow Machine Learning model."""
		# Get model parameters.
		self.model_params = BrainFlowModelParams(BrainFlowMetrics.RELAXATION, BrainFlowClassifiers.REGRESSION)
		# Create the model.
		self.model = MLModel(self.model_params)
		# Set log level and prepare the classifier.
		self.model.enable_ml_logger()
		self.model.prepare()


	def _on_close(self, event):
		"""Tasks to perform on app closing event."""
		self.running = False
		self.model.release()

	def update(self):
		global fps, lastTime
		# Get data from board
		data = self.board_shim.get_current_board_data(self.num_points)

		# Data filtering: Manipulate the data array 
		for i, channel in enumerate(self.eeg_channels):
			# Notch filter, remove 50Hz AC interference.
			DataFilter.remove_environmental_noise(data[channel], self.sampling_rate, NoiseTypes.FIFTY)

			DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
			DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
									FilterTypes.BUTTERWORTH.value, 0)
			#DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
			#							FilterTypes.BUTTERWORTH.value, 0)
			#DataFilter.perform_bandstop(data[channel], self.sampling_rate, 50.0, 4.0, 2,
			#							FilterTypes.BUTTERWORTH.value, 0)
			#DataFilter.perform_bandstop(data[channel], self.sampling_rate, 60.0, 4.0, 2,
			#							FilterTypes.BUTTERWORTH.value, 0)

		# Data processing:
		#for i, channel in enumerate(self.eeg_channels):
		#	# Fast Fourier Transform:
		#	# FFT-alg can only accept an array with lenght equal to a power of 2.
		#	length = data.shape[1]
		#	n = smallest_power(length)
		#	freq = DataFilter.perform_fft(data[channel, length-n:], WindowFunctions.HANNING)
#		print(freq.shape)

		# Get metric prediction from the ML model
		bands = DataFilter.get_avg_band_powers(data, self.eeg_channels, self.sampling_rate, True)
		feature_vector = np.concatenate((bands[0], bands[1]))
		metric = self.model.predict(feature_vector)

		# Get time and append to the appropriate lists
		metric_time = data[self.timestamp_channel, -1]
		self.metric.append(metric)
		self.metric_time.append(metric_time)

		# Merge into self.data
		series_len = data.shape[1]
		self.data[:, (self.num_points-series_len):] = data

		
		if not self.no_gui:
			# Update the artists:
			for i, channel in enumerate(self.eeg_channels):
				self.ln[i].set_ydata(self.data[channel])
			rel_time = np.array(self.metric_time)-metric_time
			self.ln[-1].set_ydata(self.metric)
			self.ln[-1].set_xdata(rel_time)
			self.fr_number.set_text(f"{fps:0.2f} fps")
		
			# Tell the blitting manager to do its thing
			self.bm.update()

		# Calculate frames per second
		now = time.time()
		dt = now - lastTime
		lastTime = now
		if fps == -1:
			fps = 1.0/dt
		else:
			s = np.clip(dt*3., 0, 1)
			fps = fps * (1-s) + (1.0/dt) * s
		print(f" {fps:6.2f} fps, metric ({self.model_params.metric.name.lower()}): {metric:.3f}", end='\r')

def smallest_power(x):
	"""Return the smallest power of 2, smaller than or equal to x."""
	return 0 if x == 0 or x == 1 else  1<<(x.bit_length()-1)

def main():
	# Set logging level.
	BoardShim.enable_dev_board_logger()
	#logging.basicConfig(level=logging.DEBUG)

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
	parser.add_argument('--no-gui', type=bool, required=False, default=False, help='run program without GUI')
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
	no_gui = args.no_gui

	try:
		# Start session.
		board_shim = BoardShim(args.board_id, params)
		board_shim.prepare_session()

		# Set board to "differential mode." See: https://docs.openbci.com/Cyton/CytonSDK/#channel-setting-commands
		# x (CHANNEL, POWER_DOWN, GAIN_SET, INPUT_TYPE_SET, BIAS_SET, SRB2_SET, SRB1_SET) X
		if board_shim.board_id == BoardIds.CYTON_BOARD:
			ch_settings = ["x1060100X", "x2060100X", "x3161000X", "x4161000X",
			               "x5161000X", "x6161000X", "x7161000X", "x8161000X"]
			for s in ch_settings:
				board_shim.config_board(s)
		
		board_shim.start_stream(450000, args.streamer_params)
		
		# Start plotting.
		g = Graph(board_shim, no_gui)
		
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
