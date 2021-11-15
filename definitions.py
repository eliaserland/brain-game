# Sets up all important config variables
import dearpygui.dearpygui as dpg

# Set up all IDs required by items in Dear PyGui
item_id = {
	"windows": {
		"main_window": dpg.generate_uuid(),
		"welcome_window": dpg.generate_uuid(),
		"settings_window": dpg.generate_uuid(),
		"loading_screen": dpg.generate_uuid()
	},
	"plots": {
		"timeseries1": dpg.generate_uuid(),
		"timeseries2": dpg.generate_uuid(),
		"metric1": dpg.generate_uuid(),
		"metric2": dpg.generate_uuid()
	},
	"line_series": {
		"timeseries1": dpg.generate_uuid(),
		"timeseries2": dpg.generate_uuid(),
		"metric1": dpg.generate_uuid(),
		"metric2": dpg.generate_uuid()
	},
	"axes": {
		"timeseries1_yaxis": dpg.generate_uuid(),
		"timeseries1_xaxis": dpg.generate_uuid(),
		"timeseries2_yaxis": dpg.generate_uuid(),
		"timeseries2_xaxis": dpg.generate_uuid(),
		"metric1_yaxis": dpg.generate_uuid(),
		"metric1_xaxis": dpg.generate_uuid(),
		"metric2_yaxis": dpg.generate_uuid(),
		"metric2_xaxis": dpg.generate_uuid()
	},
	"buttons": {
		"start": dpg.generate_uuid(),
		"stop": dpg.generate_uuid(),
		"exit": dpg.generate_uuid(),
		"settings": dpg.generate_uuid(),
		"ok": dpg.generate_uuid(),
		"reset": dpg.generate_uuid(),
		"cancel": dpg.generate_uuid(),
		"loading": dpg.generate_uuid()
	},
	"combos": {
		"board_id": dpg.generate_uuid()
	},
	"text": {
		"title": dpg.generate_uuid(),
		"tagline": dpg.generate_uuid(),
		"enter_key": dpg.generate_uuid(),
		"copyright": dpg.generate_uuid(),
		"help": dpg.generate_uuid(),
		"loading": dpg.generate_uuid(),
	},
	"registry": {
		"enter_key": dpg.generate_uuid(),
		"game_key_binds": dpg.generate_uuid(),
	},
	"handlers": {
		"enter_key": dpg.generate_uuid(),
	},
	"theme": {
		"disabled": dpg.generate_uuid(),
	},
	"indicator": {
		"settings_loading": dpg.generate_uuid(),
	}
}

# All descriptive texts in the game, in swedish and english.
desc = {
	"timeseries_title": {
		"eng": 'Time Series',
		"swe": 'Tidserie',
	},
	"metric_title": {
		"eng": 'Focus Metric',
		"swe": 'Fokusmättal',
	}
}

