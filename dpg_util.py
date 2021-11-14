import dearpygui.dearpygui as dpg

fullscreen_is_active = False

def is_viewport_fullscreen():
	global fullscreen_is_active
	return fullscreen_is_active

def enter_viewport_fullscreen():
	global fullscreen_is_active
	if not is_viewport_fullscreen():
		dpg.toggle_viewport_fullscreen()
		fullscreen_is_active = True

def exit_viewport_fullscreen():
	global fullscreen_is_active
	if is_viewport_fullscreen():
		dpg.toggle_viewport_fullscreen()
		fullscreen_is_active = False

def toggle_viewport_fullscreen():
	if is_viewport_fullscreen():
		exit_viewport_fullscreen()
	else: 
		enter_viewport_fullscreen()



