import dearpygui.dearpygui as dpg

# Font registry
with dpg.font_registry():
	default_font = dpg.add_font("fonts/Roboto-Regular.ttf", 20)
	small_font = dpg.add_font("fonts/Roboto-Regular.ttf", 16)
	intermediate_font = dpg.add_font("fonts/Roboto-Regular.ttf", 18)
	medium_font = dpg.add_font("fonts/Roboto-Regular.ttf", 30) 
	large_font = dpg.add_font("fonts/Roboto-Regular.ttf", 40)
	huge_font = dpg.add_font("fonts/Roboto-Regular.ttf", 80)
	large_bold = dpg.add_font("fonts/Roboto-Medium.ttf", 40)
	#second_font = dpg.add_font("Resources/Roboto/Roboto-Medium.ttf", 18)
dpg.bind_font(default_font)