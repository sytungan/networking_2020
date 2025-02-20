from random import randint
import sys, traceback, threading, socket
from glob import glob

from VideoStream import VideoStream
from RtpPacket import RtpPacket

class ServerWorker:
	SETUP = 'SETUP'
	PLAY = 'PLAY'
	PAUSE = 'PAUSE'
	TEARDOWN = 'TEARDOWN'
	DESCRIBE = 'DESCRIBE'
	STOP = 'STOP'
	SPEED = 'SPEED'
	FORWARD = 'FORWARD'
	BACKWARD = 'BACKWARD'
	SWITCH = 'SWITCH'
	SELECT = 'SELECT'
	
	INIT = 0
	READY = 1
	PLAYING = 2
	SWITCHING = 3 
	state = INIT


	OK_200 = 0
	FILE_NOT_FOUND_404 = 1
	CON_ERR_500 = 2

	clientInfo = {}
	
	def __init__(self, clientInfo):
		self.clientInfo = clientInfo
		
	def run(self):
		threading.Thread(target=self.recvRtspRequest).start()
	
	def recvRtspRequest(self):
		"""Receive RTSP request from the client."""
		connSocket = self.clientInfo['rtspSocket'][0]
		while True:            
			data = connSocket.recv(256)
			if data:
				print("Data received:\n" + data.decode("utf-8"))
				self.processRtspRequest(data.decode("utf-8"))
	
	def processRtspRequest(self, data):
		"""Process RTSP request sent from the client."""
		# Get the request type
		request = data.split('\n')
		line1 = request[0].split(' ')
		requestType = line1[0]
		
		# Get the media file name
		filename = line1[1]
		
		# Get the RTSP sequence number 
		seq = request[1].split(' ')
		
		# Process SETUP request
		if requestType == self.SETUP:
			if self.state == self.INIT:
				# Update state
				print("processing SETUP\n")
				
				try:
					self.clientInfo['videoStream'] = VideoStream(filename)
					self.setSpeed(1)
					self.state = self.READY
				except IOError:
					self.replyRtsp(self.FILE_NOT_FOUND_404, seq[1])
				
				# Generate a randomized RTSP session ID
				self.clientInfo['session'] = randint(100000, 999999)
				
				# Send RTSP reply
				self.replyRtsp(self.OK_200, seq[1])
				
				# Get the RTP/UDP port from the last line
				self.clientInfo['rtpPort'] = request[2].split(' ')[3]
		
		# Process PLAY request 		
		elif requestType == self.PLAY:
			if self.state == self.READY:
				print("processing PLAY\n")
				self.state = self.PLAYING
				
				# Create a new socket for RTP/UDP
				self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				
				self.replyRtsp(self.OK_200, seq[1])
				
				# Create a new thread and start sending RTP packets
				self.clientInfo['event'] = threading.Event()
				self.clientInfo['worker']= threading.Thread(target=self.sendRtp) 
				self.clientInfo['worker'].start()
		
		# Process PAUSE request
		elif requestType == self.PAUSE:
			if self.state == self.PLAYING:
				print("processing PAUSE\n")
				self.state = self.READY
				
				self.clientInfo['event'].set()
			
				self.replyRtsp(self.OK_200, seq[1])
		
		# Process TEARDOWN request
		elif requestType == self.TEARDOWN:
			print("processing TEARDOWN\n")

			self.clientInfo['event'].set()
			
			self.replyRtsp(self.OK_200, seq[1])
			
			# Close the RTP socket
			self.clientInfo['rtpSocket'].close()
		
		# Process DESCRIBE request
		elif requestType == self.DESCRIBE:
			if self.state == self.PLAYING or self.state == self.READY:
				print("processing DESCRIBE\n")
				numOfFrame = self.clientInfo['videoStream'].getNumberOfFrame()
				sizeOfFile = self.clientInfo['videoStream'].getSizeFile()
				txt = str(filename) + ',' + \
					str(numOfFrame) + ',' + \
					str(sizeOfFile)
						
				self.replyRtspMsg(self.OK_200, seq[1], txt)

		# Process STOP request
		elif requestType == self.STOP:
			if self.state == self.PLAYING or self.state == self.READY:
				print("processing STOP\n")
				self.clientInfo['event'].set()
				self.clientInfo['videoStream'].resetFrame()
				self.state = self.READY
				self.replyRtsp(self.OK_200, seq[1])

		# Process SPEED request
		elif requestType == self.SPEED:
			if self.state == self.PLAYING or self.state == self.READY:
				print("processing SPEED\n")
				speedSent = eval(request[3].split(' ')[1])
				self.setSpeed(speedSent)
				self.replyRtsp(self.OK_200, seq[1])

		# Process FORWARD request
		elif requestType == self.FORWARD:
			if self.state == self.PLAYING:
				print("processing FORWARD\n")
				#self.clientInfo['event'].set()
				currentFrame = self.clientInfo['videoStream'].frameNbr()
				limit = self.clientInfo['videoStream'].getNumberOfFrame()
				self.clientInfo['videoStream'].goToFrame((currentFrame + 20) if (currentFrame + 20) < limit else currentFrame)
				self.replyRtsp(self.OK_200, seq[1])

		# Process SWITCH request
		elif requestType == self.BACKWARD:
			if self.state == self.PLAYING:
				print("processing BACKWARD\n")
				#self.clientInfo['event'].set()
				currentFrame = self.clientInfo['videoStream'].frameNbr()
				limit = 0
				self.clientInfo['videoStream'].goToFrame((currentFrame - 20) if (currentFrame - 20) > limit else currentFrame )
				self.replyRtsp(self.OK_200, seq[1])

		# Process SWITCH request
		elif requestType == self.SWITCH:
			print("processing SWITCH\n")
			if self.state == self.PLAYING:
				self.clientInfo['event'].set()
			lstFile = glob('*.Mjpeg')
			msg = str(lstFile[0])
			for x in lstFile[1:]:
				msg += ',' + x
			self.replyRtspMsg(self.OK_200, seq[1], msg)

		# Process SELECT request
		elif requestType == self.SELECT:
			print("processing SELECT\n")
			self.clientInfo['videoStream'] = VideoStream(filename)
			self.setSpeed(1)
			self.state = self.READY
			self.replyRtsp(self.OK_200, seq[1])
			
	def sendRtp(self):
		"""Send RTP packets over UDP."""
		while True:
			self.clientInfo['event'].wait(0.05/self.speedOfFrameLoad)
			
			# Stop sending if request is PAUSE or TEARDOWN
			if self.clientInfo['event'].isSet():
				break 
				
			data = self.clientInfo['videoStream'].nextFrame()
			if data: 
				frameNumber = self.clientInfo['videoStream'].frameNbr()
				try:
					address = self.clientInfo['rtspSocket'][1][0]
					port = int(self.clientInfo['rtpPort'])
					self.clientInfo['rtpSocket'].sendto(self.makeRtp(data, frameNumber),(address,port))
				except:
					print("Connection Error")
					#print('-'*60)
					#traceback.print_exc(file=sys.stdout)
					#print('-'*60)

	def makeRtp(self, payload, frameNbr):
		"""RTP-packetize the video data."""
		version = 2
		padding = 0
		extension = 0
		cc = 0
		marker = 0
		pt = 26 # MJPEG type
		seqnum = frameNbr
		ssrc = 0 
		
		rtpPacket = RtpPacket()
		rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
		
		return rtpPacket.getPacket()
		
	def replyRtsp(self, code, seq):
		"""Send RTSP reply to the client."""
		if code == self.OK_200:
			#print("200 OK")
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(reply.encode())
		
		# Error messages
		elif code == self.FILE_NOT_FOUND_404:
			print("404 NOT FOUND")
		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")

	def replyRtspMsg(self, code, seq, msg):
		"""Send RTSP reply to the client."""
		if code == self.OK_200:
			#print("200 OK")
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session']) + '\nMessage: ' +str(msg)
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(reply.encode())
		
		# Error messages
		elif code == self.FILE_NOT_FOUND_404:
			print("404 NOT FOUND")
		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")
		
	def setSpeed(self, num):
		self.speedOfFrameLoad = num
