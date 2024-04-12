import os
import json
from dotenv import load_dotenv

import paho.mqtt.client as paho
from paho import mqtt
import time

from game import Game
from colorama import Fore # For colored output

game_over = False

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

            player_1_move = input(str(player_1) + ", enter a direction to move in: ").upper()
            if player_1_move == "UP":
                client.publish(f"games/{lobby_name}/{player_1}/move", "UP")
            elif player_1_move == "DOWN":
                client.publish(f"games/{lobby_name}/{player_1}/move", "DOWN")
            elif player_1_move == "RIGHT":
                client.publish(f"games/{lobby_name}/{player_1}/move", "RIGHT")
            elif player_1_move == "LEFT":
                client.publish(f"games/{lobby_name}/{player_1}/move", "LEFT")
            else:
                print("Not a Valid Direction")


            player_2_move = input(str(player_2) + ", enter a direction to move in: ").upper()
            if player_2_move == "UP":
                client.publish(f"games/{lobby_name}/{player_2}/move", "UP")
            elif player_2_move == "DOWN":
                client.publish(f"games/{lobby_name}/{player_2}/move", "DOWN")
            elif player_2_move == "RIGHT":
                client.publish(f"games/{lobby_name}/{player_2}/move", "RIGHT")
            elif player_2_move == "LEFT":
                client.publish(f"games/{lobby_name}/{player_2}/move", "LEFT")
            else:
                print("Not a Valid Direction")


            player_3_move = input(str(player_3) + ", enter a direction to move in: ").upper()
            if player_3_move == "UP":
                client.publish(f"games/{lobby_name}/{player_3}/move", "UP")
            elif player_3_move == "DOWN":
                client.publish(f"games/{lobby_name}/{player_3}/move", "DOWN")
            elif player_3_move == "RIGHT":
                client.publish(f"games/{lobby_name}/{player_3}/move", "RIGHT")
            elif player_3_move == "LEFT":
                client.publish(f"games/{lobby_name}/{player_3}/move", "LEFT")
            else:
                print("Not a Valid Direction")


            player_4_move = input(str(player_4) + ", enter a direction to move in: ").upper()
            if player_4_move == "UP":
                client.publish(f"games/{lobby_name}/{player_4}/move", "UP")
            elif player_4_move == "DOWN":
                client.publish(f"games/{lobby_name}/{player_4}/move", "DOWN")
            elif player_4_move == "RIGHT":
                client.publish(f"games/{lobby_name}/{player_4}/move", "RIGHT")
            elif player_4_move == "LEFT":
                client.publish(f"games/{lobby_name}/{player_4}/move", "LEFT")
            else:
                print("Not a Valid Direction")

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
