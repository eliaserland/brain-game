import argparse
import time
import logging
import numpy as np

#import pyqtgraph as pg
#from pyqtgraph.Qt import QtGui, QtCore
#import pyqtgraph.ptime as ptime

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes, WindowFunctions, DetrendOperations

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
        # paranoia in case we missed the draw event,
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
	def __init__(self, board_shim):
		self.board_id = board_shim.get_board_id()
		self.board_shim = board_shim
		self.exg_channels = BoardShim.get_exg_channels(self.board_id)
		self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
		self.window_size = 5
		self.num_points = self.window_size * self.sampling_rate
		self.time_stamp_channel = BoardShim.get_timestamp_channel(self.board_id)
		self.data = np.zeros((BoardShim.get_num_rows(self.board_id), self.num_points))
		self.time = list(reversed(-np.arange(0, self.num_points)/self.sampling_rate))
		
		# Limit no. of channels if testing with synthetic data
		if self.board_id == BoardIds.SYNTHETIC_BOARD:
			self.exg_channels = [1, 2, 3, 4, 5, 6, 7, 8]
		
		# Initialize plots
		self._init_timeseries()

		# Update plots, until program end.
		self.running = True
		while self.running:
			self.update()

	def _init_timeseries(self):
		
		ylim = 200 * 1.1
		
		# Create a figure
		fig, axes = plt.subplots(len(self.exg_channels), 1, figsize=(6, 6), sharex=True)
		axes = axes.flatten()

		# Set sequential colormap
		#cmap = 'viridis'
		#colors = getattr(plt.cm, cmap)(np.linspace(0,1,len(axes)))
		colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

		# Add all lines 
		ln = list()
		for i, ax in enumerate(axes):
			(ln_tmp,) = ax.plot(self.time, self.data[i], animated=True, linewidth=0.8, color=colors[i])
			ln.append(ln_tmp)
			ax.set_ylim(-ylim, ylim)
			ax.set_xlim(np.min(self.time)*1.001, np.max(self.time))
			ax.tick_params(axis='x', labelsize=6)
			ax.tick_params(axis='y', labelsize=6)
			ax.set_ylabel("Pot (uV)", fontsize=6)
			if i == len(axes)-1:
				ax.set_xlabel("Time (s)", fontsize=6)

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

		print("----INITIALIZATION COMPLETED----")

	def _on_close(self, event):
		self.running = False

	def update(self):
		global fps, lastTime
		# Get data from board
		data = self.board_shim.get_current_board_data(self.num_points)

		# Data filtering: Manipulate the data array 
		for i, channel in enumerate(self.exg_channels):
			# Notch filter, remove 50Hz AC interference.
			DataFilter.remove_environmental_noise(data[channel], self.sampling_rate, NoiseTypes.FIFTY)


			DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
			DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
									FilterTypes.BUTTERWORTH.value, 0)
			DataFilter.perform_bandpass(data[channel], self.sampling_rate, 51.0, 100.0, 2,
										FilterTypes.BUTTERWORTH.value, 0)
			DataFilter.perform_bandstop(data[channel], self.sampling_rate, 50.0, 4.0, 2,
										FilterTypes.BUTTERWORTH.value, 0)
			DataFilter.perform_bandstop(data[channel], self.sampling_rate, 60.0, 4.0, 2,
										FilterTypes.BUTTERWORTH.value, 0)

		# Data processing:
		for i, channel in enumerate(self.exg_channels):
			# Fast Fourier Transform:
			# FFT-alg can only accept an array with lenght equal to a power of 2.
			length = data.shape[1]
			n = smallest_power(length)
			freq = DataFilter.perform_fft(data[channel, length-n:], WindowFunctions.HANNING)
#		print(freq.shape)

		# Merge into self.data
		series_len = data.shape[1]
		self.data[:, (self.num_points-series_len):] = data

		# Update the artists
		for i, channel in enumerate(self.exg_channels):
			self.ln[i].set_ydata(self.data[channel])

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
		print(f" {fps:0.2f} fps", end='\r')

def smallest_power(x):
	"Return the smallest power of 2, smaller than or equal to x."
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
