import numpy as np
import dearpygui.dearpygui as dpg
import braingame
programName = 'BrainGame Curiosum'

def update(my_dpg, quantities, actions):
	q1, q2 = quantities
	
	time1, timeseries1 = q1['time_series']
	time2, timeseries2 = q2['time_series']
	metric_time1, metric1 = q1['focus_metric']
	metric_time2, metric2 = q2['focus_metric']
	
	print("Actions: " + ' '.join(actions) + f"  {metric1[-1]:.5f} {metric2[-1]:.5f}", end='\r')
	
	my_dpg.set_value('series_tag1', [list(time1), list(timeseries1)])
	my_dpg.set_value('series_tag2', [list(time2), list(timeseries2)])
	my_dpg.set_value('series_tag3', [list(metric_time1), list(metric1)])
	my_dpg.set_value('series_tag4', [list(metric_time2), list(metric2)])


def main():

	

	#game.callback_start_game()

	# Prepare GUI (these lines are always needed)
	dpg.create_context()
	dpg.create_viewport(title=programName, width=1000, height=800)

	#dpg.show_metrics()
	game = braingame.BrainGameInterface(dpg)
	
	with dpg.window(tag='Time Series'):
		#dpg.set_exit_callback(callback=game.callback_end_game)
		with dpg.group(horizontal=True):
			dpg.add_button(label="  Apply  ", callback=game.callback_apply_settings)
			dpg.add_button(label=" Discard ", callback=game.callback_discard_settings)
			dpg.add_button(label="  Start  ", callback=game.callback_start_game)
			dpg.add_button(label="  Stop   ", callback=game.callback_stop_game)


		with dpg.group(horizontal=True):
			with dpg.plot(label='Player 1 - Time Series', height=600, width=1200, anti_aliased=True):
				# optionally create legend
				dpg.add_plot_legend()

				# REQUIRED: create x and y axes
				dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
				dpg.add_plot_axis(dpg.mvYAxis, label="Voltage", tag="y_axis1")

				# series belong to a y axis
				dpg.add_line_series(list(range(10)), list(np.ones(10)), label="0.5 + 0.5 * sin(x)", parent="y_axis1", tag="series_tag1")
				dpg.set_axis_limits('y_axis1', -100.0, 100.0)
			with dpg.plot(label='Player 2 - Time Series', height=600, width=1200, anti_aliased=True):
				# optionally create legend
				dpg.add_plot_legend()

				# REQUIRED: create x and y axes
				dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
				dpg.add_plot_axis(dpg.mvYAxis, label="Voltage", tag="y_axis2")

				# series belong to a y axis
				dpg.add_line_series(list(range(10)), list(np.ones(10)), label="0.5 + 0.5 * sin(x)", parent="y_axis2", tag="series_tag2")
				dpg.set_axis_limits('y_axis2', -100.0, 100.0)
		with dpg.group(horizontal=True):
			with dpg.plot(label='Player 1 - Metric', height=600, width=1200, anti_aliased=True):
				# optionally create legend
				dpg.add_plot_legend()

				# REQUIRED: create x and y axes
				dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
				dpg.add_plot_axis(dpg.mvYAxis, label="Voltage", tag="y_axis3")

				# series belong to a y axis
				dpg.add_line_series(list(range(10)), list(np.ones(10)), label="0.5 + 0.5 * sin(x)", parent="y_axis3", tag="series_tag3")
				dpg.set_axis_limits('y_axis3', -0.005, 1.005)
			with dpg.plot(label='Player 2 - Metric', height=600, width=1200, anti_aliased=True):
				# optionally create legend
				dpg.add_plot_legend()

				# REQUIRED: create x and y axes
				dpg.add_plot_axis(dpg.mvXAxis, label="Time (s)")
				dpg.add_plot_axis(dpg.mvYAxis, label="Voltage", tag="y_axis4")

				# series belong to a y axis
				dpg.add_line_series(list(range(10)), list(np.ones(10)), label="0.5 + 0.5 * sin(x)", parent="y_axis4", tag="series_tag4")
				dpg.set_axis_limits('y_axis4', -0.005, 1.005)

	
	

#	 Run GUI (these lines are always needed)
	dpg.setup_dearpygui()
	dpg.show_viewport()

	

	

	dpg.set_primary_window("Time Series", True)

	# Main render loop: code here is executed every frame.
	dpg.start_dearpygui()
	#while dpg.is_dearpygui_running():
	#	quantities, actions = game.update_TMP()
	#	q1, q2 = quantities
	#	time1, metric1 = q1['focus_metric']
	#	time2, metric2 = q2['focus_metric']
		
		
	#	update(quantities)
	#	dpg.render_dearpygui_frame()
	

if __name__ == '__main__':
	main()