import os
import json
from dotenv import load_dotenv

import paho.mqtt.client as paho
from paho import mqtt
import time

from game import Game


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


# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    """
    Prints a mqtt message to stdout ( used as callback for subscribe )
    :param client: the client itself
    :param userdata: userdata is set when initiating the client, here it is userdata=None
    :param msg: the message with topic and payload
    """
    try:
        game_state = json.loads(msg.payload)
    except json.JSONDecodeError:
        print(f"Invalid JSON: {msg.payload}")
        return

    if 'currentPosition' in game_state:
        current_position = game_state['currentPosition']
        walls = game_state.get('walls', [])
        coins = {
            'Coin1': game_state.get('coin1', []),
            'Coin2': game_state.get('coin2', []),
            'Coin3': game_state.get('coin3', []),
        }
        teammate_positions = game_state.get('teammatePositions', [])
        enemy_positions = game_state.get('enemyPositions', [])

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
        for row in player_view:
            print(''.join('{:<10}'.format(item) for item in row))
    else:
        print('Scores: ' + str(game_state))

    print('\n')
    print("message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))


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
#     print("message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))




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
    client.on_subscribe = on_subscribe # Can comment out to not print when subscribing to new topics
    client.on_message = on_message
    client.on_publish = on_publish # Can comment out to not print when publishing to topics

    lobby_name = "TestLobby"
    player_1 = "Player1"
    player_2 = "Player2"
    player_3 = "Player3"

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
                                        'team_name':'BTeam',
                                        'player_name' : player_3}))

    time.sleep(1) # Wait a second to resolve game start
    client.publish(f"games/{lobby_name}/start", "START")


    client.loop_start()


######################################## CHALLENGE 2 HERE #############################################



    while True:

        print("in new round")

        time.sleep(1)

    # if player_1 == "Player1":
        player_1_move = input("\nEnter move(UP,DOWN,LEFT,RIGHT) for Player 1: ")
        client.publish(f"games/{lobby_name}/{player_1}/move", player_1_move)

    # if player_2 == "Player2":
        player_2_move = input("\nEnter move(UP,DOWN,LEFT,RIGHT) for Player 2: ")
        client.publish(f"games/{lobby_name}/{player_2}/move", player_2_move)

    # if player_3 == "Player3":
        player_3_move = input("\nEnter move(UP,DOWN,LEFT,RIGHT) for Player 3: ")
        client.publish(f"games/{lobby_name}/{player_3}/move", player_3_move)

        if player_1_move == "STOP" or player_2_move == "STOP" or player_3_move == "STOP":
            break # End the game

        time.sleep(1)


    print("Game Over")

    client.publish(f"games/{lobby_name}/start", "STOP")
    client.loop_stop()
    # Unsubscribe from the game state topic
    client.unsubscribe(f"games/{lobby_name}/{player_1}/game_state")
    client.unsubscribe(f"games/{lobby_name}/{player_2}/game_state")
    client.unsubscribe(f"games/{lobby_name}/{player_3}/game_state")

    # Unsubscribe from the scores topic
    client.unsubscribe(f"games/{lobby_name}/scores")

    # Unsubscribe from the move topic
    client.unsubscribe(f"games/{lobby_name}/{player_1}/move")
    client.unsubscribe(f"games/{lobby_name}/{player_2}/move")
    client.unsubscribe(f"games/{lobby_name}/{player_3}/move")

    # Unsubscribe from the team's topic
    client.unsubscribe(f"teams/{'ATeam'}")
    client.unsubscribe(f"teams/{'BTeam'}")

