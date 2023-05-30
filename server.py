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


PLAYERS = {}
PLAYERS_LOCK = threading.Semaphore()

class Player:
	def __init__(self, websocket):
		self.websocket = websocket
		self.coords = (0,0)
		self.name = "anon"
		self.color = "#AB1400"

async def register(websocket):
	global PLAYERS
	print("client got")
	p = Player(websocket)
	PLAYERS_LOCK.acquire()
	PLAYERS[websocket] = p
	PLAYERS_LOCK.release()
	return p

async def unregister(websocket):
	global PLAYERS
	print("client lost")
	PLAYERS_LOCK.acquire()
	del PLAYERS[websocket]
	PLAYERS_LOCK.release()

async def PlayerHandler(websocket, path):
	global PLAYERS
	player = await register(websocket)
	try:
		async for message in websocket:
			data = json.loads(message) # TODO protections
			if data["type"] == "controls":
				player.coords = data["coords"]
			elif data["type"] == "name":
				player.name = data["name"]
				player.color = data["color"]
			else:
				print("unknown data type:", data)
	finally:
		await unregister(websocket)

def MainLoop():
	while True:
		waitFramerate(1/20)

		outgoing = {"type":"frame", "players":[]}
		PLAYERS_LOCK.acquire()
		for ws in PLAYERS:
			player = PLAYERS[ws]
			outgoing["players"].append({"coords":player.coords, "name":player.name, "color":player.color})
		for ws in PLAYERS:
			outgoingMsg = json.dumps(outgoing)
			asyncio.run(ws.send(outgoingMsg)) #Really, we shouldn't call run each time. We need to make a separate message collector event loop handle thing
		PLAYERS_LOCK.release()

GameThread = threading.Thread(group=None, target=MainLoop, name="GameThread")
GameThread.start()
asyncio.get_event_loop().run_until_complete(websockets.serve(PlayerHandler, port=9001))
asyncio.get_event_loop().run_forever()
