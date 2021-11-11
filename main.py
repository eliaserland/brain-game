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
plt1 = 0
plt2 = 0
plt3 = 0 
plt4 = 0
btn1 = 0


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
		"""Callback to start a new game."""
		if not self.game_is_running:
			logging.info("Starting game")
			# Set flag.
			self.game_is_running = True
			# Create a container used for housing return data from game loop.
			self.data = DataContainer()
			# Start the main game loop.
			self.game.start_game(self.data)
			# Start gui plotting thread.
			self.thread = threading.Thread(target=self.__gui_loop, daemon=False)
			self.thread.start()
		else:
			logging.info("Game is already running")

	def callback_stop_game(self):
		"""Callback to stop and end a running game."""
		if self.game_is_running:
			logging.info("Stopping game")
			self.game_is_running = False
			self.game.stop_game()
			self.data.destroy()
			self.thread.join()
		else:
			logging.info("No game is running")

	def callback_restart_game(self):
		pass

	def callback_settings_menu(self):
		pass

	def callback_press_any_key(self):
		pass

	def callback_timeseries_settings(self):
		pass

	def callback_focus_settings(self):
		pass

	def __gui_loop(self):
		"""Main thread function for updating the GUI plots during a game."""
		global series1, series2, series3, series4
		
		self.__init_fps()
		while self.game_is_running:

			return_data = self.data.get()
			self.__update_plots(return_data)
	
			self.__calc_fps()
			print(f"FPS: {self.fps:.3f}", end='\r')
	
	def __update_plots(self, data):
			(player1, player2), actions = data
			time1, timeseries1 = player1['time_series']
			time2, timeseries2 = player2['time_series']
			metric_time1, metric1 = player1['focus_metric']
			metric_time2, metric2 = player2['focus_metric']

			#print("Actions: " + ' '.join(actions) + f"  {metric1[-1]:.5f} {metric2[-1]:.5f}", end='\r')
			dpg.set_value(series1, [list(time1), list(timeseries1)])
			dpg.set_value(series2, [list(time2), list(timeseries2)])
			dpg.set_value(series3, [list(metric_time1), list(metric1)])
			dpg.set_value(series4, [list(metric_time2), list(metric2)])

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
		"""Create the main window. """
		global series1, series2, series3, series4
		global plt1, plt2, plt3, plt4, btn1

		#data = self.game.get_init_data()

		with dpg.window(tag='Time Series'):
			dpg.set_exit_callback(callback=self.callback_stop_game)
			
			with dpg.group(horizontal=True):
				btn1 = dpg.add_button(label="  Apply  ", callback=self.game.callback_apply_settings)
				dpg.add_button(label=" Discard ", callback=self.game.callback_discard_settings)
				dpg.add_button(label="  Start  ", callback=self.callback_start_game)
				dpg.add_button(label="  Stop   ", callback=self.callback_stop_game)

			y_min = -100
			y_max = 100
			width = 620
			height = 375
			with dpg.group(horizontal=True):
				with dpg.plot(label='Player 1 - Time Series', width=width, height=height, anti_aliased=True) as plt1:
					# optionally create legend
					dpg.add_plot_legend()

					# REQUIRED: create x and y axes
					x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
					y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Voltage (uV)")

					# series belong to a y axis
					series1 = dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=y_axis)
					dpg.set_axis_limits(y_axis, y_min, y_max)
					dpg.set_axis_limits(x_axis, -5, 0)

				with dpg.plot(label='Player 2 - Time Series', width=width, height=height, anti_aliased=True) as plt2:
					# optionally create legend
					dpg.add_plot_legend()

					# REQUIRED: create x and y axes
					x_axis2 = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
					y_axis2 = dpg.add_plot_axis(dpg.mvYAxis, label="Voltage (uV)")

					# series belong to a y axis
					series2 =  dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=y_axis2)
					dpg.set_axis_limits(y_axis2, y_min, y_max)
					dpg.set_axis_limits(x_axis2, -5, 0)
			with dpg.group(horizontal=True):
				with dpg.plot(label='Player 1 - Foucs Metric', width=width, height=height, anti_aliased=True) as plt3:
					# optionally create legend
					dpg.add_plot_legend()

					# REQUIRED: create x and y axes
					x_axis3 = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
					y_axis3 = dpg.add_plot_axis(dpg.mvYAxis, label="Metric")

					# series belong to a y axis
					series3 = dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=y_axis3)
					dpg.set_axis_limits(y_axis3, -0.005, 1.005)
					dpg.set_axis_limits(x_axis3, -5, 0)
				
				with dpg.plot(label='Player 2 - Focus Metric', width=width, height=height, anti_aliased=True) as plt4:
					# optionally create legend
					dpg.add_plot_legend()

					# REQUIRED: create x and y axes
					x_axis4 = dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
					y_axis4 = dpg.add_plot_axis(dpg.mvYAxis, label="Metric")

					# series belong to a y axis
					series4 = dpg.add_line_series(list(range(10)), list(np.ones(10)), parent=y_axis4)
					dpg.set_axis_limits(y_axis4, -0.005, 1.005)
					dpg.set_axis_limits(x_axis4, -5, 0)

	
def window_resize():
		global plt1, plt2, plt3, plt4, btn1
		plots = [plt1, plt2, plt3, plt4]
		xpos = [0, 0, 1, 1]
		ypos = [0, 1, 0, 1]
		btn_height = dpg.get_item_height(btn1)
		#h = dpg.get_item_height("Time Series") - btn_height - 45
		h = dpg.get_viewport_client_height() - btn_height - 45
		#w = dpg.get_item_width("Time Series") - 40
		w = dpg.get_viewport_client_width() - 40
		for i, p in enumerate(plots):
			dpg.set_item_height(p, height=h//2)
			dpg.set_item_width(p, width=w//2)
			dpg.set_item_pos(p, [(w//2)*xpos[i], (h//2)*ypos[i],])
		#dpg.set_item_height("win", h//2)
		#dpg.set_item_width("win", w//2)

	
def main():
	gui = GUI()

	#------------------------
	# Prepare dearpygui (these lines are always needed)
	dpg.create_context()
	#------------------------

	#dpg.show_metrics()
	gui.create_window()
	#dpg.show_debug()
	
	#------------------------
	# (these lines are always needed)
	dpg.create_viewport(title=programName, vsync=False, resizable=True, width=1280, height=800)
	# must be called before showing viewport
	#pg.set_viewport_small_icon("path/to/icon.ico")
	#dpg.set_viewport_large_icon("path/to/icon.ico")
	dpg.setup_dearpygui()
	dpg.show_viewport()
	#------------------------
	
	
	dpg.set_primary_window("Time Series", True)

	dpg.set_viewport_resize_callback(callback=window_resize)
	

	#dpg.maximize_viewport()

	#------------------------
	# (these lines are always needed)
	dpg.start_dearpygui()
	dpg.destroy_context()

if __name__ == '__main__':
	main()