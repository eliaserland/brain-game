import argparse
import time
import numpy as np
from collections import deque

from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowError
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, NoiseTypes, WindowFunctions, DetrendOperations
from brainflow.ml_model import BrainFlowMetrics, BrainFlowClassifiers, BrainFlowModelParams, MLModel

def parse_arguments():
	"""
	Parse command line arguments. Use brainflow docs to check which parameters 
	are required for any specific board, e.g. for Cyton - set serial port.
	"""
	parser = argparse.ArgumentParser()
	# Board options:
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
	parser.add_argument('--board-id',        type=int, required=False, default=BoardIds.SYNTHETIC_BOARD, help='Board id, check docs to get a list of supported boards.')
	# Game options:
	parser.add_argument('--custom_channels', type=list[int], required=False, default=None, help='In game mode: custom channels for each player. Defaults to channels 1 to num_players.')
	args = parser.parse_args()
	return args

def set_brainflow_input_params(args: argparse.Namespace):
	"""
	Set parsed parameters in BrainFlowInputParams structure. 
	"""
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
	return params

def set_active_channels(args: argparse.Namespace):
	"""
	Set which two channels of the BCI board to use. Defaults to 
	channels 1 and 2. 
	"""
	if args.custom_channels is None:
		active_channels = [1, 2] # default
	else:
		active_channels = args.custom_channels
	return active_channels

def set_differential_mode(board_shim: BoardShim, active_channels: list[int]):
	"""
	Set BCI board to 'differential mode', neccessary for multiplayer on a single
	board. For the Cyton board, we set channels 1,2 to "differential mode", 
	channels 3-8 to off. See: https://docs.openbci.com/Cyton/CytonSDK/#channel-setting-commands.
	x (CHANNEL, POWER_DOWN, GAIN_SET, INPUT_TYPE_SET, BIAS_SET, SRB2_SET, SRB1_SET) X
	"""
	#ch_settings = ["x1060100X", "x2060100X", "x3161000X", "x4161000X",
	#               "x5161000X", "x6161000X", "x7161000X", "x8161000X"]
	ch_settings = []
	opt_channel_on  = "060100X" # powered up, default gain, normal input, bias on, srbs off
	opt_channel_off = "161000X" # powered down, default gain, shorted input, bias off, srbs off
	for i in range(1, len(BoardShim.get_eeg_channels(board_shim.board_id))+1):
		base = f'x{i}' # channel no
		if i in active_channels:
			ch_settings.append(base+opt_channel_on)
		else:
			ch_settings.append(base+opt_channel_off)
	# Send configuration to the board.
	board_shim.config_board(''.join(ch_settings))

class Board:
	def __init__(self, board_shim: BoardShim, active_channels: list[int]):
		# Save board parameters.
		self.board_shim = board_shim
		self.board_id = board_shim.get_board_id()
		self.eeg_channels = BoardShim.get_eeg_channels(self.board_id)
		self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
		self.window_size = 5
		self.num_points = self.window_size * self.sampling_rate
		self.timestamp_channel = BoardShim.get_timestamp_channel(self.board_id)
		self.active_channels = active_channels
		# Limit no. of channels if testing with synthetic data
		if self.board_id == BoardIds.SYNTHETIC_BOARD:
			self.eeg_channels = [1, 2, 3, 4, 5, 6, 7, 8]

class AvgBandPower(Board):
	def __init__(self, board_shim: BoardShim, active_channels: list[int], channel: int):
		super().__init__(board_shim, active_channels)
		# Allocate deque for tracking average band power.
		self.avg_band_power = deque([], maxlen=100)
		self.avg_band_power.append(np.zeros(5))
		self.channel = channel

	def get_band_power(self, data: np.ndarray):
		"""
		Calculate average band power from the time series data. 5 Bands: 
		1-4Hz, 4-8Hz, 8-13Hz, 13-30Hz, 30-50Hz.
		"""
		avg, std = DataFilter.get_avg_band_powers(data, [self.channel], self.sampling_rate, True)
		self.avg_band_power.append(avg)
		current_band_power = np.array(self.avg_band_power).mean(0)
		return current_band_power

class MLClassifier:
	"""Initialize BrainFlow machine learning classifier."""
	model_params = BrainFlowModelParams(BrainFlowMetrics.RELAXATION, BrainFlowClassifiers.REGRESSION)
	model = MLModel(model_params)
	model.enable_ml_logger()
	model.prepare()

	@classmethod
	def destroy(cls):
		cls.model.release()

class FocusMetric(Board):
	def __init__(self, board_shim: BoardShim, active_channels: list[int], channel: int):
		super().__init__(board_shim, active_channels)
		self.metric = deque([0], maxlen=self.num_points) 
		self.time = deque([time.time()], maxlen=self.num_points)
		self.model = MLClassifier.model
		self.model_params = MLClassifier.model_params
		self.channel = channel

	def get_metric(self, data: np.ndarray):
		# Get metric estimate. 
		bands = DataFilter.get_avg_band_powers(data, [self.channel], self.sampling_rate, True)
		feature_vector = np.concatenate((bands[0], bands[1]))
		metric = self.model.predict(feature_vector)
		self.metric.append(metric)
		# Get time corresponding to the metric value.
		time = data[self.timestamp_channel, -1]
		self.time.append(time)
		return self.metric, self.time

class TimeSeries(Board):
	def __init__(self, board_shim: BoardShim, active_channels: list[int], channel: int):
		super().__init__(board_shim, active_channels)
		self.channel = channel

	def get_time_series(self, data: np.ndarray):
		pass


class Player:
	def __init__(self, board_shim: BoardShim, active_channels: list[int], channel: int):
		self.bandp = AvgBandPower(board_shim, active_channels, channel)
		self.focus = FocusMetric(board_shim, active_channels, channel)

	def update(self, data: np.ndarray):
		# Calculate all derived quantities, such as band power, focus metric etc.
		band_power  = self.bandp.get_band_power(data)
		metric, metric_time = self.focus.get_metric(data)

		# Send quantities to the GUI.



class BrainGame(Board):
	def __init__(self, board_shim: BoardShim, active_channels: list[int]):
		super().__init__(board_shim, active_channels)
		self.p1 = Player(board_shim, active_channels, active_channels[0])
		self.p2 = Player(board_shim, active_channels, active_channels[1])

	def update(self):
		# Collect data from BCI board.
		data = self.board_shim.get_current_board_data(self.num_points)
		print(data.shape)
		# Process the raw data, denoise signal.

		# Send processed data to players
		self.p1.update(data)
		self.p2.update(data)

		# Retrieve metrics, choose an action.

		# Send action to arduino

		# Send quantities to the GUI ?

	def destroy(self):
		MLClassifier.destroy()


class Action:
	def __init__(self) -> None:
		pass