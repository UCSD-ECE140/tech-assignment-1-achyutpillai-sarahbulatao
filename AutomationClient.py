import os
import json
import random
from dotenv import load_dotenv

import paho.mqtt.client as paho
from paho import mqtt
import time

from game import Game
from colorama import Fore # For colored output

game_over = False
game_state = None

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
def on_publish(client, userdata, mid, reasonCode, properties=None):
    print("mid: {}".format(mid))
# def on_publish(client, userdata, mid, properties=None):
#     """
#         Prints mid to stdout to reassure a successful publish ( used as callback for publish )
#         :param client: the client itself
#         :param userdata: userdata is set when initiating the client, here it is userdata=None
#         :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
#         :param properties: can be used in MQTTv5, but is optional
#     """
#     print("mid: " + str(mid))


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


######################################## CHALLENGE 2 HERE #############################################


# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    """
    Prints a mqtt message to stdout ( used as callback for subscribe )
    :param client: the client itself
    :param userdata: userdata is set when initiating the client, here it is userdata=None
    :param msg: the message with topic and payload
    """

    global game_over
    global game_state

    try:
        game_state = json.loads(msg.payload)
    except json.JSONDecodeError:
        # print(f"Invalid JSON: {msg.payload}")
        # return
        if msg.payload == b'Game Over: All coins have been collected':
            print("Game Over: All coins have been collected")
            print("Scores: " + str(game_state))
            game_over = True
            return
        else:
            print(f"Invalid JSON: {msg.payload}")
        return

    if 'currentPosition' in game_state:
        current_position = game_state['currentPosition']
        print(Fore.GREEN + '\nCurrent Position: ' + str(current_position))

        walls = game_state.get('walls', [])
        print(Fore.BLUE + 'Walls: ' + str(walls))
        coins = {
            'Coin1': game_state.get('coin1', []),
            'Coin2': game_state.get('coin2', []),
            'Coin3': game_state.get('coin3', []),
        }
        print(Fore.YELLOW + 'Coins: ' + str(coins))

        teammate_positions = game_state.get('teammatePositions', [])
        print(Fore.CYAN + 'Teammate Positions: ' + str(teammate_positions))

        enemy_positions = game_state.get('enemyPositions', [])
        print(Fore.RED + 'Enemy Positions: ' + str(enemy_positions))

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
                elif item == 'None':
                    print(Fore.WHITE + '{:<10}'.format(item), end='')
                else:
                    print(Fore.WHITE + '{:<10}'.format(item), end='')
            print()
       
    else:
        print('\nScores: ' + str(game_state))

    print('\n')
    print(Fore.WHITE + "message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


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

########################################################################################################### RANDOM MOVE FUNCTION

# def random_direction():
#     return random.choice(['UP', 'DOWN', 'LEFT', 'RIGHT'])

########################################################################################################### RANDOM PATHFINDING FUNCTIONS

def get_valid_directions(current_position, game_state):
    # directions = {'UP', 'DOWN', 'LEFT', 'RIGHT'}
    directions = {
        'UP': (current_position[0] - 1, current_position[1]),
        'DOWN': (current_position[0] + 1, current_position[1]),
        'LEFT': (current_position[0], current_position[1] - 1),
        'RIGHT': (current_position[0], current_position[1] + 1)
    }
    walls = set(tuple(w) for w in game_state.get('walls', []))
    coins = {tuple(coin) for key in ['coin1', 'coin2', 'coin3'] for coin in game_state.get(key, [])}
    
    valid_directions = []

    for direction, pos in directions.items():
        if pos not in walls and (pos in coins or is_within_bounds(pos)):
            valid_directions.append(direction)

    return valid_directions

def is_within_bounds(position, size=(10, 10)):  # Assuming a 10x10 board
    x, y = position
    return 0 <= x < size[0] and 0 <= y < size[1]

def random_direction(current_position, game_state):
    valid_directions = get_valid_directions(current_position, game_state)
    if valid_directions:
        return random.choice(valid_directions)
    # return 'NONE'  # Return 'NONE' or some default if no valid moves are possible
    return random.choice(['UP', 'DOWN', 'LEFT', 'RIGHT'])

###########################################################################################################

if __name__ == '__main__':
    load_dotenv(dotenv_path='./credentials.env')
    
    broker_address = os.environ.get('BROKER_ADDRESS')
    broker_port = int(os.environ.get('BROKER_PORT'))
    username = os.environ.get('USER_NAME')
    password = os.environ.get('PASSWORD')

    # client = paho.Client(client_id="Player1", userdata=None, protocol=paho.MQTTv5)
    client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION2, client_id="Player1", userdata=None, protocol=paho.MQTTv5)
    
    # enable TLS for secure connection
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set(username, password)
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect(broker_address, broker_port)

    # setting callbacks, use separate functions like above for better visibility
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe # Can comment out to not print when subscribing to new topics
    client.on_message = on_message
    client.on_publish = on_publish # Can comment out to not print when publishing to topics

    lobby_name = "TestLobby"
    player_1 = "Player1"
    player_2 = "Player2"
    player_3 = "Player3"
    player_4 = "Player4" 

    client.subscribe(f"games/{lobby_name}/lobby")
    client.subscribe(f'games/{lobby_name}/+/game_state')
    client.subscribe(f'games/{lobby_name}/scores')
    time.sleep(1)

    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                            'team_name':'ATeam',
                                            'player_name' : player_1}))
    time.sleep(1)
    
    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                            'team_name':'BTeam',
                                            'player_name' : player_2}))
    time.sleep(1)
    
    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                        'team_name':'ATeam',
                                        'player_name' : player_3}))
    
    time.sleep(1)
    
    client.publish("new_game", json.dumps({'lobby_name':lobby_name,
                                        'team_name':'BTeam',
                                        'player_name' : player_4}))

    time.sleep(1) # Wait a second to resolve game start


    command = ''
    while command != 'START':
        command = input("Type 'START' to start the game: ").upper()
        if command == 'START':
            client.publish(f"games/{lobby_name}/start", "START")

    client.loop_start()

    counter = 0

    while not game_over:
        try:
            counter +=1
            print("\nRound: ", counter)

            time.sleep(1)

            players = [player_1, player_2, player_3, player_4]

            for player in players:
                current_position = game_state.get('currentPosition', None)
                
                valid_move = random_direction(current_position, game_state)
                client.publish(f"games/{lobby_name}/{player}/move", valid_move)
                print(f"Player {player} moves {valid_move}")

     
            time.sleep(1)


        except KeyboardInterrupt:
            print('\nBreak')
            client.publish(f"games/{lobby_name}/start", "STOP")
            client.loop_stop()


    # print("Game Over")

    client.publish(f"games/{lobby_name}/start", "STOP")
    client.loop_stop()

    # Unsubscribe from the game state topic
    client.unsubscribe(f"games/{lobby_name}/{player_1}/game_state")
    client.unsubscribe(f"games/{lobby_name}/{player_2}/game_state")
    client.unsubscribe(f"games/{lobby_name}/{player_3}/game_state")
    client.unsubscribe(f"games/{lobby_name}/{player_4}/game_state")

    # Unsubscribe from the scores topic
    client.unsubscribe(f"games/{lobby_name}/scores")

    # Unsubscribe from the move topic
    client.unsubscribe(f"games/{lobby_name}/{player_1}/move")
    client.unsubscribe(f"games/{lobby_name}/{player_2}/move")
    client.unsubscribe(f"games/{lobby_name}/{player_3}/move")
    client.unsubscribe(f"games/{lobby_name}/{player_4}/move")

    # Unsubscribe from the team's topic
    client.unsubscribe(f"teams/{'ATeam'}")
    client.unsubscribe(f"teams/{'BTeam'}")





# import os
# import json
# from dotenv import load_dotenv

# import paho.mqtt.client as paho
# from paho import mqtt
# import time

# from game import Game
# from colorama import Fore # For colored output
# import math
# import random

# game_over = False
# # next_move = None
# next_moves = {
#     "Player 1": None,
#     "Player 2": None,
#     "Player 3": None,
#     "Player 4": None
# }

# # setting callbacks for different events to see if it works, print the message etc.
# def on_connect(client, userdata, flags, rc, properties=None):
#     print("CONNACK received with code %s." % rc)


# # with this callback you can see if your publish was successful
# def on_publish(client, userdata, mid, reasonCode, properties=None):
#     print("mid: {}".format(mid))
# # def on_publish(client, userdata, mid, properties=None):
# #     print("mid: " + str(mid))


# # print which topic was subscribed to
# def on_subscribe(client, userdata, mid, granted_qos, properties=None):
#     print("Subscribed: " + str(mid) + " " + str(granted_qos))


# ######################################## CHALLENGE 2 HERE #############################################

# def heuristic(a, b):
#     return abs(a[0] - b[0]) + abs(a[1] - b[1])

# def a_star_search(start, goal, walls):
#     from queue import PriorityQueue
#     frontier = PriorityQueue()
#     frontier.put((0, start))
#     came_from = {start: None}
#     cost_so_far = {start: 0}

#     while not frontier.empty():
#         current = frontier.get()[1]

#         if current == goal:
#             break

#         for next in get_neighbors(current, walls):
#             new_cost = cost_so_far[current] + 1  # Assuming uniform cost
#             if next not in cost_so_far or new_cost < cost_so_far[next]:
#                 cost_so_far[next] = new_cost
#                 priority = new_cost + heuristic(goal, next)
#                 frontier.put((priority, next))
#                 came_from[next] = current

#     return came_from, cost_so_far


# def get_neighbors(node, walls):
#     directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
#     return [(node[0] + d[0], node[1] + d[1]) for d in directions if (node[0] + d[0], node[1] + d[1]) not in walls]


# def reconstruct_path(came_from, start, goal):
#     path = []
#     current = goal
#     while current != start:
#         path.append(current)
#         current = came_from.get(current)
#     path.reverse()
#     return path

# def get_next_move(path):
#     if len(path) > 1:
#         direction = {
#             (1, 0): 'DOWN',
#             (-1, 0): 'UP',
#             (0, 1): 'RIGHT',
#             (0, -1): 'LEFT'
#         }
#         move = (path[1][0] - path[0][0], path[1][1] - path[0][1])
#         return direction.get(move, 'UP')
#     return 'UP'

# def determine_player_id(topic):
#     parts = topic.split('/')
#     return parts[-2] # Assuming topic format: games/{lobby_name}/{player_id}/game_state




# def on_message(client, userdata, msg):
#     global game_over
#     global next_move

#     try:
#         player_id = determine_player_id(msg.topic)
#         print("Player ID: ", player_id)

#         game_state = json.loads(msg.payload)
#         if 'currentPosition' not in game_state:
#             print("Error: 'currentPosition' missing in game state")
#             return

#         current_position = tuple(game_state['currentPosition'])
#         print(f"Player ID: {player_id}\nCurrent Position: {current_position}")

#         walls = {tuple(w) for w in game_state.get('walls', [])}
#         coins = set()
#         for coin_key in ['coin1', 'coin2', 'coin3']:
#             coins.update(tuple(c) for c in game_state.get(coin_key, []))

#         print(f"Walls: {walls}\nCoins: {coins}")

#         # Execute pathfinding only if there are coins
#         if coins:
#             closest_coin = min(coins, key=lambda c: heuristic(c, current_position))
#             came_from, _ = a_star_search(current_position, closest_coin, walls)
#             path = reconstruct_path(came_from, current_position, closest_coin)
#             next_move = get_next_move(path)
#             next_moves[player_id] = next_move
#             client.publish(f"games/{lobby_name}/{player_id}/move", next_move)
#             print(f"Processed message for {player_id}: Next move is {next_move}")
#         else:
#             print(f"No coins found for {player_id}. No move published.")
#             next_moves[player_id] = None

#         if not coins:  # No coins found
#             print(f"No coins available for player {player_id} to target.")
#             return  # Skip pathfinding and move calculation

#     except json.JSONDecodeError:
#         if msg.payload == b'Game Over: All coins have been collected':
#             print("Game Over: All coins have been collected")
#             game_over = True
#             return
#         else:
#             print(f"Invalid JSON: {msg.payload}")
#         return
    
#     print(f"Processed message for {player_id}: Next move is {next_moves[player_id]}")



#     if 'currentPosition' in game_state:
#         print(Fore.GREEN + '\nCurrent Position: ' + str(current_position))

#         print(Fore.BLUE + 'Walls: ' + str(walls))

#         # Display coin positions
#         print(Fore.YELLOW + 'Coins: ' + str(coins))

#         teammate_positions = game_state.get('teammatePositions', [])
#         print(Fore.CYAN + 'Teammate Positions: ' + str(teammate_positions))

#         enemy_positions = game_state.get('enemyPositions', [])
#         print(Fore.RED + 'Enemy Positions: ' + str(enemy_positions))

#         # Update player view logic here (you may need to adjust this part based on actual game logic)
#         player_view = [['None' for _ in range(5)] for _ in range(5)]
#         start_row, start_col = [pos - 2 for pos in current_position]
#         update_player_view(player_view, current_position, start_row, start_col)
#         update_game_view(player_view, walls, coins, teammate_positions, enemy_positions, start_row, start_col)

#         # Print the player's view
#         print_player_view(player_view)

#     else:
#         print('\nScores: ' + str(game_state))

#     print(Fore.WHITE + "message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


# def update_game_view(view, walls, coins, teammates, enemies, start_row, start_col):
#     update_view(view, walls, start_row, start_col, 'Wall')
#     for coin in coins:
#         update_view(view, coin, start_row, start_col, 'Coin')
#     for teammate in teammates:
#         update_view(view, teammate, start_row, start_col, 'Teammate')
#     for enemy in enemies:
#         update_view(view, enemy, start_row, start_col, 'Enemy')


# def print_player_view(view):
#     for row in view:
#         for item in row:
#             color = Fore.WHITE  # Default color
#             if item == 'Player':
#                 color = Fore.GREEN
#             elif item == 'Wall':
#                 color = Fore.BLUE
#             elif item == 'Coin':
#                 color = Fore.YELLOW
#             elif item == 'Teammate':
#                 color = Fore.CYAN
#             elif item == 'Enemy':
#                 color = Fore.RED
#             print(color + '{:<10}'.format(item), end='')
#         print()


# def update_player_view(view, position, start_row, start_col):
#     x, y = position
#     if y > 7:
#         for val in range(5):
#             view[val][4] = '.'
#         if y > 8:
#             for val in range(5):
#                 view[val][3] = '.'
#     if y < 2:
#         for val in range(5):
#             view[val][0] = '.'
#         if y < 1:
#             for val in range(5):
#                 view[val][1] = '.'
#     if x > 7:
#         for val in range(5):
#             view[4][val] = '.'
#         if x > 8:
#             for val in range(5):
#                 view[3][val] = '.'
#     if x < 2:
#         for val in range(5):
#             view[0][val] = '.'
#         if x < 1:
#             for val in range(5):
#                 view[1][val] = '.'
#     view[position[0] - start_row][position[1] - start_col] = 'Player'


# def update_view(view, positions, start_row, start_col, item):
#     for position in positions:
#         if not isinstance(position, (tuple, list)) or len(position) != 2:
#             print(f"Invalid position data: {position}")
#             continue
#         adjusted_row = position[0] - start_row
#         adjusted_col = position[1] - start_col
#         if 0 <= adjusted_row < len(view) and 0 <= adjusted_col < len(view[0]):
#             view[adjusted_row][adjusted_col] = item
#         else:
#             print(f"Position out of view bounds: {position}")





# def random_move():
#     next_move = random.choice(['UP', 'DOWN', 'LEFT', 'RIGHT'])
#     return next_move


# if __name__ == '__main__':
#     load_dotenv(dotenv_path='./credentials.env')
    
#     broker_address = os.environ.get('BROKER_ADDRESS')
#     broker_port = int(os.environ.get('BROKER_PORT'))
#     username = os.environ.get('USER_NAME')
#     password = os.environ.get('PASSWORD')

#     # client = paho.Client(client_id="Player1", userdata=None, protocol=paho.MQTTv5)
#     client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION2, client_id="Player1", userdata=None, protocol=paho.MQTTv5)
    
#     # enable TLS for secure connection
#     client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
#     # set username and password
#     client.username_pw_set(username, password)
#     # connect to HiveMQ Cloud on port 8883 (default for MQTT)
#     client.connect(broker_address, broker_port)

#     # setting callbacks, use separate functions like above for better visibility
#     client.on_connect = on_connect
#     client.on_subscribe = on_subscribe # Can comment out to not print when subscribing to new topics
#     client.on_message = on_message
#     client.on_publish = on_publish # Can comment out to not print when publishing to topics

#     lobby_name = "TestLobby"
#     player_1 = "Player 1"
#     player_2 = "Player 2"
#     player_3 = "Player 3"
#     player_4 = "Player 4" 

#     client.subscribe(f"games/{lobby_name}/lobby")
#     client.subscribe(f'games/{lobby_name}/+/game_state')
#     client.subscribe(f'games/{lobby_name}/scores')
#     client.subscribe(f"games/{lobby_name}/+/move")
#     time.sleep(1)

#     client.publish("new_game", json.dumps({'lobby_name':lobby_name,
#                                             'team_name':'ATeam',
#                                             'player_name' : player_1}))
#     time.sleep(1)
    
#     client.publish("new_game", json.dumps({'lobby_name':lobby_name,
#                                             'team_name':'BTeam',
#                                             'player_name' : player_2}))
#     time.sleep(1)
    
#     client.publish("new_game", json.dumps({'lobby_name':lobby_name,
#                                         'team_name':'ATeam',
#                                         'player_name' : player_3}))
    
#     time.sleep(1)
    
#     client.publish("new_game", json.dumps({'lobby_name':lobby_name,
#                                         'team_name':'BTeam',
#                                         'player_name' : player_4}))

#     time.sleep(1) # Wait a second to resolve game start


#     command = ''
#     while command != 'START':
#         command = input("Type 'START' to start the game: ").upper()
#         if command == 'START':
#             client.publish(f"games/{lobby_name}/start", "START")

#     client.loop_start()

#     counter = 0

#     while not game_over:
#         try:
#             counter += 1
#             print("\nRound: ", counter)

#             time.sleep(1)

#             for player, move in next_moves.items():
#                 move_data = json.dumps({"move": next_move})
#                 client.publish(f"games/{lobby_name}/{player}/move", move_data)

#                 print(f"Publishing move {next_move} for player {player}")
#             else:
#                 print(f"No valid move calculated for player {player}")
#                 # if move:
#                 #     client.publish(f"games/{lobby_name}/{player}/move", move)
#                 #     next_moves[player] = None  # Reset after publishing
#             time.sleep(1)

#         except KeyboardInterrupt:
#             print('\nInterrupted by user')
#             break

#     # while not game_over:
#     #     try:
#     #         counter +=1
#     #         print("\nRound: ", counter)

#     #         time.sleep(1)

#     #         # player_1_move = random_move()
#     #         player_1_move = random_move()
#     #         client.publish(f"games/{lobby_name}/{player_1}/move", player_1_move)

#     #         player_2_move = random_move()
#     #         client.publish(f"games/{lobby_name}/{player_2}/move", player_2_move)

#     #         player_3_move = random_move()
#     #         client.publish(f"games/{lobby_name}/{player_3}/move", player_3_move)

#     #         player_4_move = random_move()
#     #         client.publish(f"games/{lobby_name}/{player_4}/move", player_4_move)

#     #         time.sleep(1)


#     #     except KeyboardInterrupt:
#     #         print('\nBreak')
#     #         client.publish(f"games/{lobby_name}/start", "STOP")
#     #         client.loop_stop()


#     # print("Game Over")

#     client.publish(f"games/{lobby_name}/start", "STOP")
#     client.loop_stop()

#     # Unsubscribe from the game state topic
#     client.unsubscribe(f"games/{lobby_name}/{player_1}/game_state")
#     client.unsubscribe(f"games/{lobby_name}/{player_2}/game_state")
#     client.unsubscribe(f"games/{lobby_name}/{player_3}/game_state")
#     client.unsubscribe(f"games/{lobby_name}/{player_4}/game_state")

#     # Unsubscribe from the scores topic
#     client.unsubscribe(f"games/{lobby_name}/scores")

#     # Unsubscribe from the move topic
#     client.unsubscribe(f"games/{lobby_name}/{player_1}/move")
#     client.unsubscribe(f"games/{lobby_name}/{player_2}/move")
#     client.unsubscribe(f"games/{lobby_name}/{player_3}/move")
#     client.unsubscribe(f"games/{lobby_name}/{player_4}/move")

#     # Unsubscribe from the team's topic
#     client.unsubscribe(f"teams/{'ATeam'}")
#     client.unsubscribe(f"teams/{'BTeam'}")

