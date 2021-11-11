from collections import deque
import numpy as np
import dearpygui.dearpygui as dpg
import braingame
import threading
import time
import logging

programName = 'BrainGame Curiosum'
series1 = 0
series2 = 0
series3 = 0
series4 = 0


class DataContainer:
	"""Container used for dynamic return data from game thread loop."""
	def __init__(self):
		self.data = None
		self.cond = threading.Condition()
		self.bypass = False

	def put(self, data):
		"""Place data into the container."""
		with self.cond:
			self.data = data
			self.cond.notify()
	def get(self):
		"""Retrieve data from the container."""
		if not self.bypass:
			with self.cond:
				self.cond.wait()
				data = self.data
		return data
	
	def destroy(self):
		"""Destroy the container."""
		self.bypass = True
		with self.cond:
			self.cond.notify()


class GUI:
	def __init__(self) -> None:
		# Create an instance of the main game.
		self.game = braingame.BrainGameInterface()
		self.game_is_running = False

	def callback_start_game(self):
		if not self.game_is_running:
			logging.info("Starting game.")
			# Set flag.
			self.game_is_running = True
			# Create a container used for housing return data from game loop.
			self.data = DataContainer()
			# Start the main game loop.
			self.game.start_game(self.data)
			# Start gui plotting thread.
			self.thread = threading.Thread(target=self.__update_gui_loop, daemon=False)
			self.thread.start()
		else:
			logging.info("Game is already running.")

	def callback_stop_game(self):
		if self.game_is_running:
			logging.info("Stopping game.")
			self.game_is_running = False
			self.game.stop_game()
			self.data.destroy()
			self.thread.join()
		else:
			logging.info("No game is running.")

	def __update_gui_loop(self):

		global series1, series2, series3, series4
		#print(series1, series2, series3, series4)
		flag = True
		self.__init_fps()
		while self.game_is_running:

			d = self.data.get()
			if not d:
				#print("Wrong")
				continue

			quantities = d[0]
			actions = d[1]
			 
			#print("HEJ")
			q1, q2 = quantities

			time1, timeseries1 = q1['time_series']
			time2, timeseries2 = q2['time_series']
			metric_time1, metric1 = q1['focus_metric']
			metric_time2, metric2 = q2['focus_metric']

			#print("Actions: " + ' '.join(actions) + f"  {metric1[-1]:.5f} {metric2[-1]:.5f}", end='\r')
			if flag:
				print(len(time1), len(timeseries1), len(time2), len(timeseries2))
				flag = False
			dpg.set_value(series1, [list(time1), list(timeseries1)])
			dpg.set_value(series2, [list(time2), list(timeseries2)])
			dpg.set_value(series3, [list(metric_time1), list(metric1)])
			dpg.set_value(series4, [list(metric_time2), list(metric2)])
			self.__calc_fps()
			print(f"FPS: {self.fps:.3f}", end='\r')
	def __init_fps(self):
		self.fps = -1
		self.lastTime = time.time()
	
	def __calc_fps(self):
		"""Calculate frames per second."""
		now = time.time()
		dt = now - self.lastTime
		self.lastTime = now
		if self.fps == -1:
			self.fps = 1.0/dt
		else: 
			s = np.clip(dt*3., 0, 1)
			self.fps = self.fps * (1-s) + (1.0/dt) * s



	def create_window(self):
		global series1, series2, series3, series4


		with dpg.window(tag='Time Series'):
			dpg.set_exit_callback(callback=self.callback_stop_game)
			
			with dpg.group(horizontal=True):			
				dpg.add_button(label="  Apply  ", callback=self.game.callback_apply_settings)
				dpg.add_button(label=" Discard ", callback=self.game.callback_discard_settings)
				dpg.add_button(label="  Start  ", callback=self.callback_start_game)
				dpg.add_button(label="  Stop   ", callback=self.callback_stop_game)

			y_min = -50
			y_max = 50
			with dpg.group(horizontal=True):
				with dpg.plot(label='Player 1 - Time Series', height=600, width=900, anti_aliased=True):
					# optionally create legend
					dpg.add_plot_legend()

					# REQUIRED: create x and y axes
					x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
					y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Voltage")

					# series belong to a y axis
					series1 = dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=y_axis)
					dpg.set_axis_limits(y_axis, y_min, y_max)
					dpg.set_axis_limits(x_axis, -5, 0)

				with dpg.plot(label='Player 2 - Time Series', height=600, width=900, anti_aliased=True):
					# optionally create legend
					dpg.add_plot_legend()

					# REQUIRED: create x and y axes
					x_axis2 = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
					y_axis2 = dpg.add_plot_axis(dpg.mvYAxis, label="Voltage")

					# series belong to a y axis
					series2 =  dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=y_axis2)
					dpg.set_axis_limits(y_axis2, y_min, y_max)
					dpg.set_axis_limits(x_axis2, -5, 0)
			with dpg.group(horizontal=True):
				with dpg.plot(label='Player 1 - Metric', height=600, width=900, anti_aliased=True):
					# optionally create legend
					dpg.add_plot_legend()

					# REQUIRED: create x and y axes
					x_axis3 = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
					y_axis3 = dpg.add_plot_axis(dpg.mvYAxis, label="Voltage")

					# series belong to a y axis
					series3 = dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=y_axis3)
					dpg.set_axis_limits(y_axis3, -0.005, 1.005)
					dpg.set_axis_limits(x_axis3, -5, 0)
				
				with dpg.plot(label='Player 2 - Metric', height=600, width=900, anti_aliased=True):
					# optionally create legend
					dpg.add_plot_legend()

					# REQUIRED: create x and y axes
					x_axis4 = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
					y_axis4 = dpg.add_plot_axis(dpg.mvYAxis, label="Voltage")

					# series belong to a y axis
					series4 = dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=y_axis4)
					dpg.set_axis_limits(y_axis4, -0.005, 1.005)
					dpg.set_axis_limits(x_axis4, -5, 0)

	


def main():

	gui = GUI()

	#------------------------
	# Prepare GUI (these lines are always needed)
	dpg.create_context()
	#------------------------

	gui.create_window()	
	dpg.show_metrics()
	#dpg.show_debug()
	
	print(series1, series2, series3, series4)
	
	#------------------------
	dpg.create_viewport(title=programName, vsync=False, resizable=True)
	# must be called before showing viewport
	#pg.set_viewport_small_icon("path/to/icon.ico")
	#dpg.set_viewport_large_icon("path/to/icon.ico")
	dpg.setup_dearpygui()
	dpg.show_viewport()
	#------------------------
	
	dpg.maximize_viewport()
	dpg.set_primary_window("Time Series", True)
	
	#------------------------
	dpg.start_dearpygui()
	dpg.destroy_context()

if __name__ == '__main__':
	main()