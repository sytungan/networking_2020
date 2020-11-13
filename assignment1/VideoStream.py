import os
# get the size of file
class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
			self.size = os.path.getsize(filename) 
		except:
			raise IOError
		self.frameNum = 0
		self.indexOfSeek = []
		self.numberOfFrame = 0

		self.indexOfSeek += [self.file.tell()]
		data = self.file.read(5)
		while data:
			framelength = int(data)
			self.file.read(framelength)
			self.numberOfFrame += 1
			self.indexOfSeek += [self.file.tell()]
			data = self.file.read(5)
		self.file.seek(0,0)
		
	def nextFrame(self):
		"""Get next frame."""
		data = self.file.read(5) # Get the framelength from the first 5 bits
		if data: 
			framelength = int(data)
			# Read the current frame
			data = self.file.read(framelength)
			self.frameNum += 1
		return data
		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum

	def getNumberOfFrame(self):
		return self.numberOfFrame

	def getFrameRest(self):
		return self.numberOfFrame - self.frameNum

	def goToFrame(self, num):
		self.file.seek(self.indexOfSeek[num])
		self.frameNum = num
	
	def resetFrame(self):
		self.file.seek(0,0)
		self.frameNum = 0

	def getSizeFile(self):
		return self.size