from serial.tools import list_ports

#Saves all connected USB_ports to port_list and prints out all of
def get_connected_usbs():
	ports = list_ports.comports()
	port_list = []
	for port in ports:
		port_list.append(port.device)
	
	print(f"Ports connected to something: {port_list}")
	return port_list

if __name__ == '__main__':
	list = get_connected_usbs()