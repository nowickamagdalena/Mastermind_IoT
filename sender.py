#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import time
import RPi.GPIO as GPIO
from config import *  # pylint: disable=unused-wildcard-import
from mfrc522 import MFRC522
import datetime;
import time

# The broker name or IP address.
broker = "localhost"
# broker = "127.0.0.1"
# broker = "10.0.0.1"

# The MQTT client.
client = mqtt.Client()
startGameTime = 0
currentPlayerId = 0
currentGameDatetime = ""

def init():
    pass

def loginPlayer(player_id):
    global currentPlayerId
    currentPlayerId = player_id

def logoutPlayer():
    global currentPlayerId
    currentPlayerId = 0

def startPlayersGame():
    global startGameTime, currentGameDatetime
    startGameTime = time.time()
    registered_date = datetime.datetime.now()
    currentGameDatetime = registered_date.strftime("%d/%m/%Y %H:%M:%S")

def getGameDurationInSec():
    endGameTime = time.time()
    return endGameTime - startGameTime

def savePlayersGame(player_id):
    gameTime = getGameDurationInSec()
    score = getPlayersScore()
    client.publish("player/ID", str(player_id) + ";" + str(currentGameDatetime) + ";" + str(score) + ";" + str(gameTime))

def getPlayersScore():
    # TODO: get actual score from the game
    return 0

def rfidRead():
    MIFAREReader = MFRC522()
    (status, TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)
    if status == MIFAREReader.MI_OK:
        (status, uid) = MIFAREReader.MFRC522_Anticoll()
        if status == MIFAREReader.MI_OK:
            buzzer(True)
            cardOn = True
            num = 0
            for i in range(0, len(uid)):
                num += uid[i] << (i*8)
            print(f"Card read UID: {uid} > {num}")
            if(currentPlayerId == 0):
                loginPlayer(num)
            elif(currentPlayerId == num):
                logoutPlayer()
            else:
                print("Current player needs to log out")

            while(cardOn):
                (status, uid) = MIFAREReader.MFRC522_Anticoll()
                cardOn = status == MIFAREReader.MI_OK
            buzzer(False)
    
def process_message(client, userdata, message):
    # Decode message.
    player_games = (str(message.payload.decode("utf-8"))).split(";")
    for game_row in player_games:
        print(game_row)


def buzzer(state):
    GPIO.output(buzzerPin, not state)  # pylint: disable=no-member

def call_broker_connection(message):
    client.publish("player/ID", message)

def connect_to_broker():
    # Connect to the broker.
    client.connect(broker)
    
    client.on_message = process_message
    # Send message about conenction.
    client.loop_start()
    client.subscribe("player/ID")
    call_broker_connection("Client connected")


def disconnect_from_broker():
    # Send message about disconenction.
    call_broker_connection("Client disconnected")
    # Disconnect the client.
    client.disconnect()


def run_sender():
    try:
        init()
        connect_to_broker()
        while True :
            rfidRead()
    except KeyboardInterrupt:    
        disconnect_from_broker()

if __name__ == "__main__":
    print("\nProgram started\n")
    run_sender()
    print("\nProgram finished")