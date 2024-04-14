import os
import json
from dotenv import load_dotenv

import paho.mqtt.client as paho
from paho import mqtt
import time

from colorama import Fore # For colored output
import random
from collections import deque


game_over = False
playerViews = {}

# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    """
        Prints the result of the connection with a reasoncode to stdout ( used as callback for connect )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param flags: these are response flags sent by the broker
        :param rc: stands for reasonCode, which is a code for the connection result
        :param properties: can be used in MQTTv5, but is optional
    """
    print("CONNACK received with code %s." % rc)


# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    """
        Prints mid to stdout to reassure a successful publish ( used as callback for publish )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param properties: can be used in MQTTv5, but is optional
    """
    print("mid: " + str(mid))


# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    """
        Prints a reassurance for successfully subscribing
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param granted_qos: this is the qos that you declare when subscribing, use the same one for publishing
        :param properties: can be used in MQTTv5, but is optional
    """
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    """
    Prints a mqtt message to stdout ( used as callback for subscribe )
    :param client: the client itself
    :param userdata: userdata is set when initiating the client, here it is userdata=None
    :param msg: the message with topic and payload
    """
    global game_over
    try:
        game_state = json.loads(msg.payload)
    except json.JSONDecodeError:
        # print(f"Invalid JSON: {msg.payload}")
        # return
        if msg.payload == b'Game Over: All coins have been collected':
                game_over = True
                print(Fore.WHITE + str(msg.payload.decode('utf-8')))
        else:
            print(f"Invalid JSON: {msg.payload}")
        return

    if 'currentPosition' in game_state:
        current_position = game_state['currentPosition']
        # print(Fore.GREEN + 'Current Position: ' + str(current_position))

        walls = game_state.get('walls', [])
        # print(Fore.BLUE + 'Walls: ' + str(walls))
        coins = {
            'Coin1': game_state.get('coin1', []),
            'Coin2': game_state.get('coin2', []),
            'Coin3': game_state.get('coin3', []),
        }
        # print(Fore.YELLOW + 'Coins: ' + str(coins))

        teammate_positions = game_state.get('teammatePositions', [])
        # print(Fore.CYAN + 'Teammate Positions: ' + str(teammate_positions))

        enemy_positions = game_state.get('enemyPositions', [])
        # print(Fore.RED + 'Enemy Positions: ' + str(enemy_positions))

        player_view = [['None' for _ in range(5)] for _ in range(5)]  # creates 5x5 square of Nones

        # Calculating the starting row and column for the view
        start_row, start_col = [pos - 2 for pos in current_position]

        # Update the player's view based on their current position
        update_player_view(player_view, current_position, start_row, start_col)

        # Update the player's view with walls, coins, teammates, and enemies
        for wall in walls:
            update_view(player_view, wall, start_row, start_col, 'Wall')
        for coin_type, coin_positions in coins.items():
            for coin in coin_positions:
                update_view(player_view, coin, start_row, start_col, coin_type)
        for teammate in teammate_positions:
            update_view(player_view, teammate, start_row, start_col, 'Teammate')
        for enemy in enemy_positions:
            update_view(player_view, enemy, start_row, start_col, 'Enemy')

        # Print the player's view
        print()
        # for row in player_view:
        #     print(''.join('{:<10}'.format(item) for item in row))
        print(Fore.WHITE + msg.topic)

        global playerViews

        playerViews[msg.topic] = player_view


        for row in player_view:
            for item in row:
                if item == 'Player':
                    print(Fore.GREEN + '{:<10}'.format(item), end='')
                elif item == 'Wall':
                    print(Fore.BLUE + '{:<10}'.format(item), end='')
                elif item.startswith('Coin'):
                    print(Fore.YELLOW + '{:<10}'.format(item), end='')
                elif item == 'Teammate':
                    print(Fore.CYAN + '{:<10}'.format(item), end='')
                elif item == 'Enemy':
                    print(Fore.RED + '{:<10}'.format(item), end='')
                else:
                    print(Fore.WHITE + '{:<10}'.format(item), end='')
            print()
       
    else:
        print(Fore.WHITE + 'Scores: ' + str(game_state))

    print('\n' + Fore.WHITE)
    # print(Fore.WHITE + "message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


def update_player_view(view, position, start_row, start_col):
    x, y = position
    if y > 7:
        for val in range(5):
            view[val][4] = '.'
        if y > 8:
            for val in range(5):
                view[val][3] = '.'
    if y < 2:
        for val in range(5):
            view[val][0] = '.'
        if y < 1:
            for val in range(5):
                view[val][1] = '.'
    if x > 7:
        for val in range(5):
            view[4][val] = '.'
        if x > 8:
            for val in range(5):
                view[3][val] = '.'
    if x < 2:
        for val in range(5):
            view[0][val] = '.'
        if x < 1:
            for val in range(5):
                view[1][val] = '.'
    view[position[0] - start_row][position[1] - start_col] = 'Player'


def update_view(view, position, start_row, start_col, item):
    try:
        view[position[0] - start_row][position[1] - start_col] = item
    except IndexError:
        pass  # Ignore positions outside of the player's view

# def bfs(start, target, walls):
#     """
#     Perform Breadth-First Search to find the next direction to move towards the target.
#     """
#     queue = deque([(start, [])])
#     visited = set()
#     while queue:
#         current, path = queue.popleft()
#         if current == target:
#             return path[0] if path else None  # Return the first direction in the path
#         if current in visited:
#             continue
#         visited.add(current)
#         for direction in ["UP", "DOWN", "LEFT", "RIGHT"]:
#             new_pos = move(current, direction)
#             if new_pos not in walls:
#                 queue.append((new_pos, path + [direction]))
#     return None  # No valid path found
# # print message, useful for checking if it was successful
# def on_message(client, userdata, msg):
#     """
#         Prints a mqtt message to stdout ( used as callback for subscribe )
#         :param client: the client itself
#         :param userdata: userdata is set when initiating the client, here it is userdata=None
#         :param msg: the message with topic and payload
#     """
#     game = []
#     game_state = json.loads(msg.payload)
#     if 'currentPosition' in game_state:
#         current_position = game_state['currentPosition']
#         walls = game_state.get('walls', [])
#         coin1 = game_state.get('coin1', [])
#         coin2 = game_state.get('coin2', [])
#         coin3 = game_state.get('coin3', [])
#         teammate_positions = game_state.get('teammatePositions', [])
#         enemy_positions = game_state.get('enemyPositions', [])

#         player_view = [['None' for _ in range(5)] for _ in range(5)] # creates 5x5 square of Nones
#         # Calculating the starting row and column for the view
#         start_row = current_position[0] - 2
#         start_col = current_position[1] - 2
        
#         x, y = current_position

#         if y > 7:
#             for val in range(5):
#                 player_view[val][4] = '.'
#             if y > 8:
#                 for val in range(5):
#                     player_view[val][3] = '.'
#         if y < 2:
#             for val in range(5):
#                 player_view[val][0] = '.'
#             if y < 1:
#                 for val in range(5):
#                     player_view[val][1] = '.'

#         if x > 7:
#             for val in range(5):
#                 player_view[4][val] = '.'
#             if x > 8:
#                 for val in range(5):
#                     player_view[3][val] = '.'
#         if x < 2:
#             for val in range(5):
#                 player_view[0][val] = '.'
#             if x < 1:
#                 for val in range(5):
#                     player_view[1][val] = '.'

#         # Updating the view with walls
#         for wall in walls:
#             wall_row, wall_col = wall
#             player_view[wall_row - start_row][wall_col - start_col] = 'Wall'

#         # Updating the view with coins
#         for coin in coin1:
#             coin_row, coin_col = coin
#             player_view[coin_row - start_row][coin_col - start_col] = 'Coin1'
#         for coin in coin2:
#             coin_row, coin_col = coin
#             player_view[coin_row - start_row][coin_col - start_col] = 'Coin2'
#         for coin in coin3:
#             coin_row, coin_col = coin
#             player_view[coin_row - start_row][coin_col - start_col] = 'Coin3'

#         # Updating the view with teammate positions
#         for teammate_pos in teammate_positions:
#             teammate_row, teammate_col = teammate_pos
#             player_view[teammate_row - start_row][teammate_col - start_col] = 'Teammate'

#         # Updating the view with enemy positions
#         for enemy_pos in enemy_positions:
#             enemy_row, enemy_col = enemy_pos
#             player_view[enemy_row - start_row][enemy_col - start_col] = 'Enemy'


#         # Updating the view with the player's current position
#         player_view[current_position[0] - start_row][current_position[1] - start_col] = 'Player'

#         # Printing the player's view
#         print()
#         for row in player_view:
#             for item in row:
#                 # Format each element with 20 characters of width
#                 print('{:<10}'.format(str(item)), end='')
#             print()  # Move to the next line after printing each row
#     else:
#         print('Scores: ' + str(game_state))

#     print('\n')
#     # print("message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


if __name__ == '__main__':
    load_dotenv(dotenv_path='./credentials.env')
    
    broker_address = os.environ.get('BROKER_ADDRESS')
    broker_port = int(os.environ.get('BROKER_PORT'))
    username = os.environ.get('USER_NAME')
    password = os.environ.get('PASSWORD')

    client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="Player1", userdata=None, protocol=paho.MQTTv5)
    
    # enable TLS for secure connection
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set(username, password)
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect(broker_address, broker_port)

    # setting callbacks, use separate functions like above for better visibility
    client.on_subscribe = on_subscribe # Can comment out to not print when subscribing to new topics
    client.on_message = on_message
    client.on_publish = on_publish # Can comment out to not print when publishing to topics

    lobby_name = "TestLobby"
    players = ['Player1', 'Player2', 'Player3', 'Player4']
    # player_1 = "Player1"
    # player_2 = "Player2"
    # player_3 = "Player3"

    client.subscribe(f"games/{lobby_name}/lobby")
    client.subscribe(f'games/{lobby_name}/+/game_state')
    client.subscribe(f'games/{lobby_name}/scores')

    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                            'team_name':'ATeam',
                                            'player_name' : players[0]}))
    
    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                            'team_name':'ATeam',
                                            'player_name' : players[1]}))
    
    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                        'team_name':'BTeam',
                                        'player_name' : players[2]}))
    
    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                        'team_name':'BTeam',
                                        'player_name' : players[3]}))

    time.sleep(2) # Wait 2 seconds to resolve game start
    # client.publish(f"games/{lobby_name}/start", "START")

    command = ''
    while command != 'START':
        command = input("Type 'START' to start the game: ").upper()
        if command == 'START':
            client.publish(f"games/{lobby_name}/start", "START")
            time.sleep(0.5)
    directions = ["UP", "DOWN", "LEFT", "RIGHT"]
    client.loop_start()
    while not game_over:
        try:
            # player = player_1
            time.sleep(0.5)
            for player in players:
                time.sleep(0.1)
                # command = input(str(player) + ", enter a direction to move in: ").upper()
                
                # print(playerViews)
                playerGrid = playerViews[f'games/{lobby_name}/{player}/game_state']
                
                choiceValid = False
                n = 0
                while not choiceValid:
                    randint = random.randint(0,3)
                    command = directions[randint]
                    
                    if (playerGrid[2][1] == 'None' or 'Coin' in playerGrid[2][1]) and command == "LEFT": #left
                        choiceValid = True
                    elif (playerGrid[2][3] == 'None' or 'Coin' in playerGrid[2][3]) and command == "RIGHT": #right
                        choiceValid = True
                    elif (playerGrid[1][2] == 'None' or 'Coin' in playerGrid[1][2]) and command == "UP": #up
                        choiceValid = True
                    elif (playerGrid[3][2] == 'None' or 'Coin' in playerGrid[3][2]) and command == "DOWN": #down
                        choiceValid = True
                    else:
                        if n>10:
                            choiceValid = True
                        n += 1
                        choiceValid = False

                if command == "UP" or command == "\x1b[A":
                    client.publish(f"games/{lobby_name}/{player}/move", "UP")
                elif command == "DOWN" or command == "\x1b[B":
                    client.publish(f"games/{lobby_name}/{player}/move", "DOWN")
                elif command == "RIGHT" or command == "\x1b[C":
                    client.publish(f"games/{lobby_name}/{player}/move", "RIGHT")
                elif command == "LEFT" or command == "\x1b[D":
                    client.publish(f"games/{lobby_name}/{player}/move", "LEFT")
                else:
                    print("Not a Valid Direction")
            # time.sleep(1)

        except KeyboardInterrupt:
            print('\nBreak')
            break

    client.publish(f"games/{lobby_name}/start", "STOP")
    client.loop_stop()
    time.sleep(1)
    client.disconnect()

