from tkinter import *
import tkinter.messagebox as tkMessageBox
from tkinter import ttk
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	SWITCHING = 3 
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	DESCRIBE = 4
	STOP = 5
	SPEED = 6
	FORWARD = 7
	BACKWARD = 8
	SWITCH = 9
	SELECT = 10
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		self.totalTime = 0
		self.setupMovie()
		
	def createWidgets(self):
		"""Build GUI."""
		# img = ImageTk.PhotoImage(Image.open("img.png"))
		# Create Setup button
		# self.setup = Button(self.master, width=20, padx=3, pady=3)
		# self.setup["text"] = "Setup"
		# self.setup["command"] = self.setupMovie
		# self.setup.grid(row=2, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=10, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=2, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=10, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=2, column=2, padx=2, pady=2)

		# Create forward button
		self.pause = Button(self.master, width=10, padx=3, pady=3)
		self.pause["text"] = "Forward"
		self.pause["command"] = self.forwardMovie
		self.pause.grid(row=2, column=3, padx=2, pady=2)

		# Create backward button
		self.pause = Button(self.master, width=10, padx=3, pady=3)
		self.pause["text"] = "Backward"
		self.pause["command"] = self.backwardMovie
		self.pause.grid(row=2, column=4, padx=2, pady=2)
		
		# Create Teardown button
		# self.teardown = Button(self.master, width=20, padx=3, pady=3)
		# self.teardown["text"] = "Teardown"
		# self.teardown["command"] =  self.exitClient
		# self.teardown.grid(row=2, column=3, padx=2, pady=2)

		# Create Stop button
		self.pause = Button(self.master, width=10, padx=3, pady=3)
		self.pause["text"] = "Stop"
		self.pause["command"] = self.stopMovie
		self.pause.grid(row=2, column=5, padx=2, pady=2)

		# Create Describe button
		self.describe = Button(self.master, width=10, padx=3, pady=3)
		self.describe["text"] = "Describe"
		self.describe["command"] = self.describeStream
		self.describe.grid(row=2, column=6, padx=2, pady=2)

		# Create Speed button
		self.pause = Button(self.master, width=10, padx=3, pady=3)
		self.pause["text"] = "Speed"
		self.pause["command"] = self.popupSpeed
		self.pause.grid(row=2, column=8, padx=2, pady=2)

		# Create Switch button
		self.pause = Button(self.master, width=10, padx=3, pady=3)
		self.pause["text"] = "Switch"
		self.pause["command"] = self.switchMovie
		self.pause.grid(row=2, column=7, padx=2, pady=2)

		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=9, sticky=W+E+N+S, padx=10, pady=10)

	
	def setupMovie(self):
		"""Setup button handler."""
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
		if self.state == self.READY:
			tkMessageBox.showwarning('Connect successfully', 'Total video time \'%s\'' %self.serverAddr)
	
	def exitClient(self):
		"""Teardown button handler."""
		self.sendRtspRequest(self.TEARDOWN)		
		self.master.destroy() # Close the gui window
		os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT) # Delete the cache image from video

	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.READY:
			# Create a new thread to listen for RTP packets
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)
	
	def describeStream(self):
		"""Describe button handler."""
		if self.state == self.PLAYING or self.state == self.READY:
			self.sendRtspRequest(self.DESCRIBE)

	def stopMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING or self.state == self.READY:
			self.sendRtspRequest(self.STOP)

	def playbackSpeed(self, num):
		if self.state == self.PLAYING or self.state == self.READY:
			self.speedOfFrameLoad = num
			self.sendRtspRequest(self.SPEED)

	def forwardMovie(self):
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.FORWARD)

	def backwardMovie(self):
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.BACKWARD)
	
	def switchMovie(self):
		self.sendRtspRequest(self.SWITCH)

	def selectMovie(self, filename_):
		if self.state == self.SWITCHING:
			self.fileName = filename_
			self.sendRtspRequest(self.SELECT)

	def popupSwitch(self, lst):
		win = Toplevel()
		win.protocol("WM_DELETE_WINDOW", self.disable_event)
		win.wm_title("Switch video")
		win.geometry('220x100') 
		l = Label(win, text="Choose video:")
		l.grid(row=1, column=2)

		listbox = ttk.Combobox(win) 
		listbox['value'] = lst
		listbox.grid(row=2, column=2)

		b = Button(win, text="Ok", command= lambda:[self.selectMovie(listbox.get()), win.destroy()])		
		b.grid(row=6, column=2)

	def disable_event(self): pass

	def popupSpeed(self):
		win = Toplevel()
		win.wm_title("Playback speed")
		win.geometry('220x100') 
		l = Label(win, text="Choose your playback speed:")
		l.grid(row=1, column=2)

		listbox = ttk.Combobox(win) 
		listbox['value'] = [0.25, 0.5, 0.75, 1, 1.25, 1.75, 2, 3, 4]
		listbox.grid(row=2, column=2)

		b = Button(win, text="Ok", command= lambda:[self.playbackSpeed(listbox.get()), win.destroy()])		
		b.grid(row=6, column=2)

	def setSpeedLabel(self, num):
		self.speedLabel.configure(text = "Playback speed: " + str(num))
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		while True:
			try:
				data = self.rtpSocket.recv(20480)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					
					currFrameNbr = rtpPacket.seqNum()
					print("Current Seq Num: " + str(currFrameNbr))
										
					if currFrameNbr > self.frameNbr: # Discard the late packet
						self.frameNbr = currFrameNbr
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
				# Stop listening upon requesting PAUSE or TEARDOWN
				if self.playEvent.isSet(): 
					break
				
				# Upon receiving ACK for TEARDOWN request,
				# close the RTP socket
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					break
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cachename, "wb")
		file.write(data)
		file.close()
		
		return cachename
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image = photo, height=288) 
		self.label.image = photo
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkMessageBox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		
		# Setup request
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()
			# Update RTSP sequence number.
			self.rtspSeq += 1
			
			# Write the RTSP request to be sent.
			request = 'SETUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)
			
			# Keep track of the sent request.
			self.requestSent = self.SETUP 
		
		# Play request
		elif requestCode == self.PLAY and self.state == self.READY:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			
			# Write the RTSP request to be sent.
			request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			
			# Keep track of the sent request.
			self.requestSent = self.PLAY
		
		# Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			
			# Write the RTSP request to be sent.
			request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			
			# Keep track of the sent request.
			self.requestSent = self.PAUSE
			
		# Teardown request
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			
			# Write the RTSP request to be sent.
			request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId) 
			
			# Keep track of the sent request.
			self.requestSent = self.TEARDOWN

		# Describe request
		elif requestCode == self.DESCRIBE and (self.state == self.PLAYING or self.READY):
			# Update RTSP sequence number.
			self.rtspSeq += 1
			
			# Write the RTSP request to be sent.
			request = 'DESCRIBE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			
			# Keep track of the sent request.
			self.requestSent = self.DESCRIBE

		# Stop request
		elif requestCode == self.STOP and (self.state == self.PLAYING or self.READY):
			# Update RTSP sequence number.
			self.rtspSeq += 1
			
			# Write the RTSP request to be sent.
			request = 'STOP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			
			# Keep track of the sent request.
			self.requestSent = self.STOP

		# Speed request
		elif requestCode == self.SPEED and (self.state == self.PLAYING or self.READY):
			# Update RTSP sequence number.
			self.rtspSeq += 1
			
			# Write the RTSP request to be sent.
			request = 'SPEED ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId) + '\nSpeed: ' + str(self.speedOfFrameLoad)
			
			# Keep track of the sent request.
			self.requestSent = self.SPEED

		# Forward request
		elif requestCode == self.FORWARD and self.state == self.PLAYING:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			
			# Write the RTSP request to be sent.
			request = 'FORWARD ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			
			# Keep track of the sent request.
			self.requestSent = self.FORWARD

		# Backward request
		elif requestCode == self.BACKWARD and self.state == self.PLAYING:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			
			# Write the RTSP request to be sent.
			request = 'BACKWARD ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			
			# Keep track of the sent request.
			self.requestSent = self.BACKWARD

				# Backward request
		elif requestCode == self.SWITCH:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			
			# Write the RTSP request to be sent.
			request = 'SWITCH ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			
			# Keep track of the sent request.
			self.requestSent = self.SWITCH

						# Backward request
		elif requestCode == self.SELECT:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			
			# Write the RTSP request to be sent.
			request = 'SELECT ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + str(self.sessionId)
			
			# Keep track of the sent request.
			self.requestSent = self.SELECT
		else:
			return
		
		# Send the RTSP request using rtspSocket.
		self.rtspSocket.send(request.encode("utf-8"))
		
		print('\nData sent:\n' + request)
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			reply = self.rtspSocket.recv(1024)
			
			if reply: 
				self.parseRtspReply(reply.decode("utf-8"))
			
			# Close the RTSP socket upon requesting Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break

	
	def parseRtspReply(self, data):
		print('\nData reply:\n' + data)
		"""Parse the RTSP reply from the server."""
		lines = data.split('\n')
		seqNum = int(lines[1].split(' ')[1])
		
		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session
			
			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200: 
					if self.requestSent == self.SETUP:

						# Set speed for label
						self.speedOfFrameLoad = 1
						self.speedLabel = Label(self.master, text="Playback speed: " + str(self.speedOfFrameLoad))
						self.speedLabel.grid(row=1, column=8)
						#-------------
						# TO COMPLETE
						#-------------
						# Update RTSP state.
						self.state = self.READY	
						# Open RTP port.
						self.openRtpPort() 

					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING

					elif self.requestSent == self.PAUSE:
						self.state = self.READY
						# The play thread exits. A new thread is created on resume.
						self.playEvent.set()

					elif self.requestSent == self.STOP:
						self.playEvent.clear()
						self.frameNbr = 0
						self.updateMovie("image/stopped.png")
						self.state = self.READY

					elif self.requestSent == self.DESCRIBE:
						msg = (lines[3].split(' ')[1]).split(',')
						txt ='File name: ' + str(msg[0]) + \
							'\nNumber of frames: ' + str(msg[1]) + \
							'\nSize of video: ' + str(msg[2]) + ' bytes'
						self.showDescription(txt)

					elif self.requestSent == self.SPEED:
						self.setSpeedLabel(self.speedOfFrameLoad)
					
					elif self.requestSent == self.FORWARD:
						self.frameNbr = 0

					elif self.requestSent == self.BACKWARD:
						self.frameNbr = 0
					
					elif self.requestSent == self.SWITCH:
						self.state = self.SWITCHING
						msg = (lines[3].split(' ')[1]).split(',')
						self.popupSwitch(msg)
					
					elif self.requestSent == self.SELECT:
						# if self.playEvent:
						# 	self.playEvent.clear()
						self.speedOfFrameLoad = 1
						self.frameNbr = 0
						self.updateMovie("image/none.png")
						self.setSpeedLabel(1)
						self.state = self.READY

					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT
						
						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1 
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		
		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)
		try:
			# Bind the socket to the address using the RTP port given by the client user
			self.rtpSocket.bind(("", self.rtpPort))
		except:
			tkMessageBox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
			self.exitClient()
		else: # When the user presses cancel, resume playing.
			self.playMovie()

	def showDescription(self, msg):
		tkMessageBox.showinfo("Description", msg)
