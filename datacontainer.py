import threading

class DataContainer:
	"""Container used for dynamic data retrieval from the game thread."""
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