import dearpygui.dearpygui as dpg

# Font registry
with dpg.font_registry():
	default_font = dpg.add_font("fonts/Roboto-Regular.ttf", 20)
	small_font = dpg.add_font("fonts/Roboto-Regular.ttf", 16)
	large_font = dpg.add_font("fonts/Roboto-Regular.ttf", 40)
	huge_font = dpg.add_font("fonts/Roboto-Regular.ttf", 80)
	#second_font = dpg.add_font("Resources/Roboto/Roboto-Medium.ttf", 18)
dpg.bind_font(default_font)