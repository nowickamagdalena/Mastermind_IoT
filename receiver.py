#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import tkinter
import sqlite3
import time

# The broker name or IP address.
broker = "localhost"
# broker = "127.0.0.1"
# broker = "10.0.0.1"

# The MQTT client.
client = mqtt.Client()

def process_message(client, userdata, message):
    # Decode message.
    message_decoded = (str(message.payload.decode("utf-8"))).split(";")

    # Print message to console.
    if message_decoded[0] == "Client connected" or message_decoded[0] == "Client disconnected":
        print(message_decoded[0])
    elif message_decoded[0] == "player_score":
        print_player_score_board(message_decoded[1])
    else:
        print(message_decoded[0] + ", " +
              message_decoded[1] + ", " +
              message_decoded[2] + ", " +
              message_decoded[3]
              )

        # Save to sqlite database.
        connention = sqlite3.connect("player.db")
        cursor = connention.cursor()
        cursor.execute("INSERT INTO score_board VALUES (?,?,?,?)",
                       (message_decoded[0], message_decoded[1], int(message_decoded[2]), int(message_decoded[3])))
        connention.commit()
        connention.close()

def print_player_score_board(player_rfid):
    connention = sqlite3.connect("players.db")
    cursor = connention.cursor()
    cursor.execute("SELECT * FROM score_board WHERE rfid=${player_rfid}")
    game_entries = cursor.fetchall()
    messageForGame  =""

    for game_entry in game_entries:
        messageForGame += game_entry[0] + "," + game_entry[1] + "," + str(game_entry[2]) + "," + str(game_entry[3]) + ";"
        print("%s, %s, %d, %d" % (game_entry[0], game_entry[1], game_entry[2], game_entry[3]))
    
    client.publish("player/ID", messageForGame)

    connention.commit()
    connention.close()



def connect_to_broker():
    # Connect to the broker.
    client.connect(broker)
    # Send message about conenction.
    client.on_message = process_message
    # Starts client and subscribe.
    client.loop_start()
    client.subscribe("player/ID")


def disconnect_from_broker():
    # Disconnet the client.
    client.loop_stop()
    client.disconnect()



def run_receiver():
    try:
        connect_to_broker()
        while True :
           pass 
    except KeyboardInterrupt:    
        print("Interruption") 
        disconnect_from_broker()

if __name__ == "__main__":
    print("\nProgram started\n")
    run_receiver()
    print("\nProgram finished")
