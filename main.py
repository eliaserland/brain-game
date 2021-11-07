from collections import deque
import numpy as np
import dearpygui.dearpygui as dpg
import braingame
import threading
import time
programName = 'BrainGame Curiosum'
series1 = 0
series2 = 0
series3 = 0
series4 = 0


class DataContainer:
	def __init__(self):
		self.data = []
		self.sem = threading.Semaphore(value=0)
	def put(self, data):
		self.data = data
		self.sem.release()
	def get(self):
		self.sem.acquire()
		return self.data


data = DataContainer()

class Plotter:
	def __init__(self, game) -> None:
		self.game = game

	def callback_start_game(self, game):
		self.game.callback_start_game()

		self.plotter_active = True
		self.thread = threading.Thread(target=self._update_loop, daemon=False)
		self.thread.start()

	def callback_stop_game(self, game):
		
		self.game.callback_stop_game()
		
		self.plotter_active = False
		self.thread.join()

	def _update_loop(self):
		global data
		global series1, series2, series3, series4
		#print(series1, series2, series3, series4)
		flag = True
		self.init_fps()
		while self.plotter_active:

			d = data.get()
			if not d:
				#print("Wrong")
				continue

			quantities = d[0]
			actions = d[1]
			 
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
			self.calc_fps()
			print(f"FPS: {self.fps:.3f}", end='\r')
	def init_fps(self):
		self.fps = -1
		self.lastTime = time.time()
	
	def calc_fps(self):
		"""Calculate frames per second."""
		now = time.time()
		dt = now - self.lastTime
		self.lastTime = now
		if self.fps == -1:
			self.fps = 1.0/dt
		else: 
			s = np.clip(dt*3., 0, 1)
			self.fps = self.fps * (1-s) + (1.0/dt) * s



def create_window(game, plotter):
	global series1, series2, series3, series4

	with dpg.window(tag='Time Series'):
		dpg.set_exit_callback(callback=plotter.callback_stop_game)
		
		with dpg.group(horizontal=True):
			
			dpg.add_button(label="  Apply  ", callback=game.callback_apply_settings)
			dpg.add_button(label=" Discard ", callback=game.callback_discard_settings)
			dpg.add_button(label="  Start  ", callback=plotter.callback_start_game)
			dpg.add_button(label="  Stop   ", callback=plotter.callback_stop_game)

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

	#game.callback_start_game()
	game = braingame.BrainGameInterface(data)
	plotter = Plotter(game)

	# Prepare GUI (these lines are always needed)
	dpg.create_context()
	
	create_window(game, plotter)
	dpg.show_metrics()
	#dpg.show_debug()
	
	
	
	print(series1, series2, series3, series4)
	
	
#	

	
	
	

	dpg.create_viewport(title=programName, vsync=False, resizable=True)
	# must be called before showing viewport
	#pg.set_viewport_small_icon("path/to/icon.ico")
	#dpg.set_viewport_large_icon("path/to/icon.ico")
	dpg.setup_dearpygui()
	dpg.show_viewport()

	dpg.maximize_viewport()
	dpg.set_primary_window("Time Series", True)

	dpg.start_dearpygui()
	dpg.destroy_context()

if __name__ == '__main__':
	main()