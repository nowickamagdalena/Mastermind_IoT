#!/usr/bin/env python3

from dis import code_info
from config import *
import RPi.GPIO as GPIO
import time
import os
import board
import neopixel
import random
from PIL import ImageFont
from PIL import Image, ImageDraw
import paho.mqtt.client as mqtt
import time
import RPi.GPIO as GPIO
from config import *  # pylint: disable=unused-wildcard-import
from mfrc522 import MFRC522
import datetime;
import time
import lib.oled.SSD1331 as SSD1331

# The broker name or IP address.
broker = "localhost"
# broker = "127.0.0.1"
# broker = "10.0.0.1"

# The MQTT client.
client = mqtt.Client()
startGameTime = 0
currentPlayerId = 0
currentGameDatetime = ""

execute = True

colors = [(255, 0, 0),(0, 255, 0),(0, 0, 255),(255, 255, 0),(0, 255, 255),(255, 0, 255)]
colorWhite = (255,255,255)
colorBlank = (0,0,0)
numberOfColors = 6
chosingColor = False
pixels = neopixel.NeoPixel(board.D18, 8, brightness=1.0/32, auto_write=False)
shoot = [0,0,0,0,0]
guesses = []
correct_positions = []
correct_colors = []
guess_number = 1
code = [0,0,0,0,0]
pixelsPosition = 0
numberOfPositions = 6
browseHints = False
win = True
SIZE_OF_BOARD = 5
image_history = []
image_index = 0

disp = SSD1331.SSD1331()
disp.Init()
# Czerwona szpilka - pionek został umieszczony na właściwym miejscu
# Biała szpilka  - właściwy kolor, ale na niewłaściwym miejscu
# hints = [czerwone szpilki, biale szpilki]
hints = [0, 0]

#poczatkowe ustawienie zmiennych w grze
def setup():
    print("setup")
    global chosingColor
    global browseHints
    global win
    global shoot
    global code    
    global disp
    global image_history, image_index,guess_number,correct_colors,correct_positions,guesses
    image_history=[]
    image_index=0
    guess_number=1
    correct_colors=[]
    correct_positions=[]
    guesses=[]
    disp.clear()

    pixels.fill(colors[0])
    pixels[5]=(colorBlank)
    pixels[6]=(colorBlank)
    pixels[7]=(colorBlank)
    pixels[pixelsPosition] = colorWhite
    pixels.show()

    chosingColor = False
    browseHints = False
    win = False

    shoot = [0,0,0,0,0]
    for i in range(5):
        code[i] = random.randint(0, 5)
    print(code)



def encoderCallback(channel):
    global chosingColor
    global pixels
    global pixelsPosition
    global shoot
    global numberOfColors
    global numberOfPositions
    global colors
    global browseHints

    enRight = GPIO.input(encoderRight)

    if not win:
        if browseHints:
            if enRight == 0:
                display_next_image()
            if enRight == 1:
                display_previous_image()
        else:
            if chosingColor: 
                if enRight == 0:
                    shoot[pixelsPosition] += 1
                    shoot[pixelsPosition] %= numberOfColors
                    pixels[pixelsPosition] = colors[shoot[pixelsPosition]]
                if enRight == 1:
                    shoot[pixelsPosition] -= 1 + numberOfColors
                    shoot[pixelsPosition] %= numberOfColors
                    pixels[pixelsPosition] = colors[shoot[pixelsPosition]]
            else:
                if enRight == 0:
                    if pixelsPosition == 5:
                        pixels[pixelsPosition] = colorBlank
                    else:
                        pixels[pixelsPosition] = colors[shoot[pixelsPosition]]
                    pixelsPosition += 1
                    pixelsPosition %= numberOfPositions
                    pixels[pixelsPosition] = colorWhite
                if enRight == 1:
                    if pixelsPosition == 5:
                        pixels[pixelsPosition] = colorBlank
                    else:
                        pixels[pixelsPosition] = colors[shoot[pixelsPosition]]
                    pixelsPosition -= 1 + numberOfPositions
                    pixelsPosition %= numberOfPositions
                    pixels[pixelsPosition] = colorWhite
            pixels.show()

def buttonRedPressedCallback(channel):
    global chosingColor
    global pixels
    global pixelsPosition
    global shoot
    global colorWhite
    global colors

    if win:
        getPlayerScoreBoard()
    else:
        if pixelsPosition != 5:
            if chosingColor:
                chosingColor = False
                pixels[pixelsPosition] = colorWhite
            else:
                chosingColor = True
                pixels[pixelsPosition] = colors[shoot[pixelsPosition]]
            pixels.show()

def buttonGreenPressedCallback(channel):
    global browseHints, guess_number, win, guesses, correct_positions, correct_colors
    if win:
        print("starting game")
        startPlayersGame()
    else:
        if browseHints:
            print("browsing hints")
            pixels[pixelsPosition] = colorWhite
            pixels.show()
            browseHints = False
        else:
            if pixelsPosition == 5:
                checkGuess()

                correct_positions.append(hints[0])
                correct_colors.append(hints[1])
                guesses.append(shoot.copy())
                board = generate_board(correct_positions[-2:], correct_colors[-2:],guess_number)
                
                if shoot == code:
                    win = True
                    show_end(board, True, code)
                    savePlayersGame()
                elif guess_number == 10:
                    win = True
                    savePlayersGame()
                    show_end(board, False, code)
                else:
                    win = False
                    disp.ShowImage(board,0,0)
                    guess_number+=1
                
            elif not chosingColor:
                browseHints = True
                pixels[pixelsPosition] = colors[shoot[pixelsPosition]]
                pixels.show()

def show_end(board, result, code):
    draw = ImageDraw.Draw(board, mode="RGB")
    draw.fontmode = "1"
    font = ImageFont.truetype("./arial.ttf", 15)
    font2 = ImageFont.truetype("./arial.ttf", 9)
    if(result):
        if(image_index == -1):
            draw.rectangle([(0, 32), (96, 64)], fill="white")
            draw.text((18, 32), "You won!", fill="orange", font=font)
            draw.text((0, 49), "Again - green|Exit - red", fill="black", font=font2)
        else:
            draw.rectangle([(0, 0), (96, 32)], fill="white")
            draw.text((18, 2), "You won!", fill="orange", font=font)
            draw.text((0, 19), "Again - green|Exit - red", fill="black", font=font2)
    else:
        draw.rectangle([(0, 0), (96, 32)], fill="white")
        draw.text((16, -1), "You lost!", fill="red", font=font)
        draw.text((1, 13), "Code:", fill="black", font=font2)

        for j, color in enumerate(code):
            draw.rectangle([(j * 7 + 28, 16), (j * 7 + 33, 21)], fill=color)

        draw.text((1, 22), "Again - green|Exit - red", fill="black", font=font2)
    disp.ShowImage(board,0,0)

def checkGuess():
    pointer = 0
    global hints
    global numberOfColors
    hints = [0,0]
    code_copy = code.copy()
    shoot_copy = shoot.copy()
    color_occurrences = [0,0,0,0,0,0]

    for position in range(SIZE_OF_BOARD):
        if code[position] == shoot[position]:
            del(code_copy[position-pointer])
            del(shoot_copy[position-pointer])
            hints[0] += 1
            pointer +=1
    
    for pos in range(numberOfColors):
        color_occurrences[pos] = code_copy.count(pos)

            
    for position in range(len(shoot_copy)):
        if shoot_copy[position] in code_copy:
            if color_occurrences[shoot_copy[position]] > 0:
                hints[1] += 1
                color_occurrences[shoot_copy[position]] -= 1

    print(hints)

def display_previous_image():
    global image_index
    if image_index > 0:
        image_index -= 1
        disp.ShowImage(image_history[image_index],0,0)
    else:
        print("This is the first image.")

def display_next_image():
    global image_index
    if image_index < len(image_history)-1:
        image_index += 1
        disp.ShowImage(image_history[image_index],0,0)
    else:
        print("This is the last image.")

def generate_board(correct_positions, correct_colors, guess_number):
    global image_history
    global image_index
    global first_image
    global guesses

    # Create an image with a white background
    board = Image.new("RGB", (96, 64), (255, 255, 255))
    draw = ImageDraw.Draw(board, mode="RGB")
    draw.fontmode = "1"

    font = ImageFont.truetype("./arial.ttf", 15)

    # Draw the guesses on the board
    for i, guess in enumerate(guesses[-2:]):
        if len(correct_positions) >= 2:
            draw.text((1, -1 + (32 * i)), str(guess_number - 1 + i) , fill="black", font=font)
        elif len(correct_positions) == 1:
            draw.text((1, -1 + (32 * i)), str(guess_number + i), fill="black", font=font)
        for j, color in enumerate(guess):
            draw.rectangle([(j * 6 + 1 + j * 13, 15 + (32 * i)), (j * 6 + 18 + j * 13, 30 + (32 * i))], fill=colors[guess[j]])

    # Draw markers for correct positions and correct colors
    for i in range(2):
        if len(correct_positions) >= 2:
            for j in range(correct_positions[-2 + i]):
                draw.ellipse([(j * 7 + 20, 1 + (32 * (i))), (j * 7 + 25, 6 + (32 * (i)))], fill='red',outline="black")
        elif len(correct_positions) == 1:
            for j in range(correct_positions[0]):
                draw.ellipse([(j * 7 + 20, 1), (j * 7 + 25, 6)], fill='red',outline="black")
        if len(correct_colors) >= 2:
            for j in range(correct_colors[-2 + i]):
                draw.ellipse([(j * 7 + 20, 8 + (32 * (i))), (j * 7 + 25, 13 + (32 * (i)))], fill='white',outline="black")
        elif len(correct_colors) == 1:
            for j in range(correct_colors[0]):
                draw.ellipse([(j * 7 + 20, 8), (j * 7 + 25, 13)], fill='white', outline="black")

    if(guess_number != 1):
        image_history.append(board)

    image_index = (guess_number-2)
    return board

def loginPlayer(player_id):
    global currentPlayerId
    currentPlayerId = player_id
    print("logged in")

def logoutPlayer():
    global currentPlayerId, win
    currentPlayerId = 0
    win = True
    pixels.fill(colorBlank)
    pixels.show()
    disp.clear()
    show_log("Log in!")
    print("logged out")

def startPlayersGame():
    if(currentPlayerId == 0):
        show_log("Log in!")
        print("player need to log in first")
    else:
        global startGameTime, currentGameDatetime
        startGameTime = time.time()
        registered_date = datetime.datetime.now()
        currentGameDatetime = registered_date.strftime("%d/%m/%Y %H:%M:%S")
        setup()

def getGameDurationInSec():
    endGameTime = time.time()
    return endGameTime - startGameTime

def savePlayersGame():
    gameTime = getGameDurationInSec()
    score = getPlayersScore()
    client.publish("player/ID", "save_game" + ";" + str(currentPlayerId) + ";" + str(currentGameDatetime) + ";" + str(score) + ";" + str(round(gameTime, 2)))

def getPlayersScore():
    return guess_number + 1

def getPlayerScoreBoard():
    print("printing score board")
    client.publish("player/ID", "player_score" + ";" + str(currentPlayerId))

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
                getPlayerScoreBoard()
            elif(currentPlayerId == num):
                logoutPlayer()
            else:
                show_log("Log out!")
                print("Current player needs to log out")

            while(cardOn):
                (status, uid) = MIFAREReader.MFRC522_Anticoll()
                cardOn = status == MIFAREReader.MI_OK
            buzzer(False)
    
global best_scores
best_scores = []

def process_message(client, userdata, message):
    global best_scores
    # Decode message.
    print("got event from publisher")
    message_decoded = (str(message.payload.decode("utf-8"))).split(";")
    if(message_decoded[0] == "player_score_results"):
        print("got scores")
        best_scores = []
        for i in range(1,4):
            if(len(message_decoded) > i):
                best_scores.append(message_decoded[i])
        print(best_scores)        
        print_scores()


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
    client.subscribe("player/scores")
    call_broker_connection("Client connected")


def disconnect_from_broker():
    # Send message about disconenction.
    call_broker_connection("Client disconnected")
    # Disconnect the client.
    client.disconnect()

def show_log(text):
    board = Image.new("RGB", (96, 64), (255, 255, 255))
    draw = ImageDraw.Draw(board, mode="RGB")
    draw.fontmode="1"
    font2 = ImageFont.truetype("./arial.ttf", 16)
    draw.text((18, 32), text, fill="orange", font=font2)
    disp.ShowImage(board,0,0)

def print_scores():
    board = Image.new("RGB", (96, 64), (255, 255, 255))
    draw = ImageDraw.Draw(board, mode="RGB")
    draw.fontmode="1"
    font2 = ImageFont.truetype("./arial.ttf", 9)
    font3 = ImageFont.truetype("./arial.ttf", 11)
    draw.text((6, 2), "Tablica wyników:", fill="orange", font=font3)
    if best_scores[0] != "":
        for i, score in enumerate(best_scores):

            data = score.split(",")
            
            draw.text((1, 15*(i+1)+5), data[1].split(" ")[0], fill="orange", font=font2)
            # draw.text((0, 14*i+3), data[1].split(" ")[1], fill="orange", font=font2)
            draw.text((51, 15*(i+1)+5), data[2], fill="orange", font=font2)
            draw.text((66, 15*(i+1)+5), data[3], fill="orange", font=font2)

    disp.ShowImage(board,0,0)

if __name__ == "__main__":
    print("\nProgram started")

    show_log("Log in!")

    connect_to_broker()

    GPIO.add_event_detect(encoderLeft, GPIO.FALLING, callback=encoderCallback, bouncetime=200)
    GPIO.add_event_detect(buttonRed, GPIO.FALLING, callback=buttonRedPressedCallback, bouncetime=200)
    GPIO.add_event_detect(buttonGreen, GPIO.FALLING, callback=buttonGreenPressedCallback, bouncetime=400)

    win = True
    try:
        connect_to_broker()
        while True :
            rfidRead()
    except KeyboardInterrupt:    
        disconnect_from_broker()
        disp.clear()
        disp.reset()
        pixels.fill(colorBlank)
        pixels.show()

    GPIO.cleanup()    
    print("\nProgram finished")
    