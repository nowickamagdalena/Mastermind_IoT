#!/usr/bin/env python3

import sqlite3
import time
import os


def create_database():
    if os.path.exists("players.db"):
        os.remove("players.db")
        print("An old database removed.")
    connection = sqlite3.connect("players.db")
    cursor = connection.cursor()
    cursor.execute(""" CREATE TABLE score_board (
        rfid text,
        date_of_game text,
        score integer,
        time_in_seconds real 
    )""")
    connection.commit() 
    connection.close()
    print("The players database created.")


if __name__ == "__main__":
    create_database()
    