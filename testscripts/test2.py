import dearpygui.dearpygui as dpg
from math import sin

dpg.create_context()


sindatax = []
sindatay = []
for i in range(0, 100):
	sindatax.append(i / 100)
	sindatay.append(0.5 + 0.5 * sin(50 * i / 100))
sindatay2 = []
for i in range(0, 100):
	sindatay2.append(2 + 0.5 * sin(50 * i / 100))

with dpg.window(label="Tutorial", width=500, height=400, tag="win"):
	# create a theme for the plot
	with dpg.theme(tag="plot_theme"):
		with dpg.theme_component(dpg.mvStemSeries):
			dpg.add_theme_color(dpg.mvPlotCol_Line, (150, 255, 0), category=dpg.mvThemeCat_Plots)
			dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Diamond, category=dpg.mvThemeCat_Plots)
			dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 7, category=dpg.mvThemeCat_Plots)

		with dpg.theme_component(dpg.mvScatterSeries):
			dpg.add_theme_color(dpg.mvPlotCol_Line, (60, 150, 200), category=dpg.mvThemeCat_Plots)
			dpg.add_theme_style(dpg.mvPlotStyleVar_Marker, dpg.mvPlotMarker_Square, category=dpg.mvThemeCat_Plots)
			dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 4, category=dpg.mvThemeCat_Plots)

with dpg.window(label="Tutorial", width=500, height=400, tag="win2"):
	# create plot
	with dpg.plot(tag="plot", label="Line Series", height=-1, width=-1):
		# optionally create legend
		dpg.add_plot_legend()

		# REQUIRED: create x and y axes
		dpg.add_plot_axis(dpg.mvXAxis, label="x")
		dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="yaxis")

		# series belong to a y axis
		dpg.add_stem_series(sindatax, sindatay, label="0.5 + 0.5 * sin(x)", parent="yaxis", tag="series_data")
		dpg.add_scatter_series(sindatax, sindatay2, label="2 + 0.5 * sin(x)", parent="yaxis", tag="series_data2")

		# apply theme to series
		dpg.bind_item_theme("series_data", "plot_theme")
		dpg.bind_item_theme("series_data2", "plot_theme")

dpg.create_viewport(title='Custom Title', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()

#dpg.enable_docking()
dpg.maximize_viewport()
#dpg.show_documentation()
#dpg.set_primary_window("win", True)




def window_resize():
	h = dpg.get_viewport_height()
	w = dpg.get_viewport_width()
	
	dpg.set_item_height("win2", h//2)
	dpg.set_item_width("win2", w//2)
	
	dpg.set_item_height("win", h//2)
	dpg.set_item_width("win", w//2)
	dpg.set_item_pos("win", [w//2, h//2,])


dpg.set_viewport_resize_callback(callback=window_resize)

#dpg.start_dearpygui()
# Main render loop: code here is executed every frame.
while dpg.is_dearpygui_running():
	dpg.set_viewport_title("BrainGame Curiosum" + f" {dpg.get_frame_rate():.1f} fps")
	dpg.render_dearpygui_frame()

dpg.destroy_context()