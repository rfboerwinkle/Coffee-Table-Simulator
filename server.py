import asyncio
import json
import logging
import websockets
import threading
import time
import random
import math
import os
logging.basicConfig()


lastTime = None
maxFrameTime = 0;
def waitFramerate(T): #TODO if we have enough time, call the garbage collector
	global lastTime, maxFrameTime
	ctime = time.monotonic()
	if lastTime:
		frameTime = ctime-lastTime
		sleepTime = T-frameTime
		if frameTime > maxFrameTime:
			maxFrameTime = frameTime
			print("Frame took "+str(maxFrameTime))
		lastTime = lastTime+T
		if sleepTime > 0:
			time.sleep(sleepTime)
	else:
		lastTime = ctime


PLAYERS = [] # TODO This should be a dictionary i think

class Player:
	def __init__(self, websocket):
		self.websocket = websocket

async def register(websocket):
	global PLAYERS
	print("client got")
	PLAYERS.append(Player(websocket))

async def unregister(websocket):
	global PLAYERS
	for i,player in PLAYERS:
		if player.websocket == websocket:
			print("client lost")
			PLAYERS.pop(i)

async def PlayerHandler(websocket, path):
	global PLAYERS
	await register(websocket)
	try:
		async for message in websocket:
			data = json.loads(message)
			for player in PLAYERS: # TODO this is horrible
				if player.websocket == websocket:
					print(data)
	finally:
		await unregister(websocket)

def MainLoop():
	while True:
		waitFramerate(1/20)

		outgoing = {"type":"frame", "players":[]}
		for player in PLAYERS:
			outgoing["players"].append({"coords":user.coords})
		for player in PLAYERS:
			outgoingMsg = json.dumps(outgoing)
			asyncio.run(player.websocket.send(outgoingMsg)) #Really, we shouldn't call run each time. We need to make a separate message collector event loop handle thing

GameThread = threading.Thread(group=None, target=MainLoop, name="GameThread")
GameThread.start()
asyncio.get_event_loop().run_until_complete(websockets.serve(boxhead, port=9001))
asyncio.get_event_loop().run_forever()
