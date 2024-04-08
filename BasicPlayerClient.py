########################################### CHALLENGE 2 HERE #################################################
import os
import json
import copy
from collections import OrderedDict

import paho.mqtt.client as paho
from paho import mqtt
from dotenv import load_dotenv

from InputTypes import NewPlayer
from game import Game
from moveset import Moveset

from map import Map
from player import Player
from team import Team
from gameItems import *


# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)


# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, reasonCode, properties=None):
    print("mid: {}".format(mid))
# def on_publish(client, userdata, mid, properties=None):
#     print("mid: " + str(mid))


# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


# print message, useful for checking if it was successful
def on_message(client, userdata, msg):
    print("message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
   
    topic_list = msg.topic.split("/")

    # Validate it is input we can deal with
    if topic_list[-1] in dispatch.keys(): 
        dispatch[topic_list[-1]](client, topic_list, msg.payload)


# Smashing both GameClient and PlayerClient to make a functionable Game
# Looking through game.py, gameItems.py, map.py, player.py, team.py, moveset.py for hints and possible implementations

############################################### FUNCTIONS FROM GAME CLIENT ##############################################

# Dispatched function, adds player to a lobby & team
def add_player(client, topic_list, msg_payload):
    # Parse and Validate Input Data
    try:
        player = NewPlayer(**json.loads(msg_payload))
    except:
        print("ValidationError in create_game")
        return
    
    # If lobby doesn't exists...
    if player.lobby_name not in client.team_dict.keys():
        client.team_dict[player.lobby_name] = {}
        client.team_dict[player.lobby_name]['started'] = False

    if client.team_dict[player.lobby_name]['started']:
        publish_error_to_lobby(client, player.lobby_name, "Game has already started, please make a new lobby")

    add_team(client, player)

    print(f'Added Player: {player.player_name} to Team: {player.team_name}')


def add_team(client, player):
    # If team not in lobby, make new team and start a player list for the team
    if player.team_name not in client.team_dict[player.lobby_name].keys():
        client.team_dict[player.lobby_name][player.team_name] = [player.player_name,]    
    # If team already exists, add player to existing list
    else:
        client.team_dict[player.lobby_name][player.team_name].append(player.player_name)


move_to_Moveset = {
    'UP' : Moveset.UP,
    'DOWN' : Moveset.DOWN,
    'LEFT' : Moveset.LEFT,
    'RIGHT' : Moveset.RIGHT
}


# Dispatched Function: handles player movement commands
def player_move(client, topic_list, msg_payload):
    lobby_name = topic_list[1]
    player_name = topic_list[2]
    if lobby_name in client.team_dict.keys():
        try:
            new_move = msg_payload.decode()

            client.move_dict[lobby_name][player_name] = (player_name, move_to_Moveset[new_move])
            game: Game = client.game_dict[lobby_name]

            # If all players made a move, resolve movement
            if len(game.all_players) == len(client.move_dict[lobby_name]):
                for player, move in client.move_dict[lobby_name].values():
                    game.movePlayer(player, move)

                # Publish player states after all movement is resolved
                for player, _ in client.move_dict[lobby_name].values():
                    client.publish(f'games/{lobby_name}/{player}/game_state', json.dumps(game.getGameData(player)))

                # Clear move list
                client.move_dict[lobby_name].clear()
                print(game.map)
                client.publish(f'games/{lobby_name}/scores', json.dumps(game.getScores()))
                if game.gameOver():
                    # Publish game over, remove game
                    publish_to_lobby(client, lobby_name, "Game Over: All coins have been collected")
                    client.team_dict.pop(lobby_name)
                    client.move_dict.pop(lobby_name)
                    client.game_dict.pop(lobby_name)

        except Exception as e:
            raise e
            publish_error_to_lobby(client, lobby_name, e.__str__)
    else:
        publish_error_to_lobby(client, lobby_name, "Lobby name not found.")


# Dispatched function: Instantiates Game object
def start_game(client, topic_list, msg_payload):
    lobby_name = topic_list[1]
    if isinstance(msg_payload, bytes) and msg_payload.decode() == "START":

        if lobby_name in client.team_dict.keys():
                # create new game
                dict_copy = copy.deepcopy(client.team_dict[lobby_name])
                dict_copy.pop('started')

                game = Game(dict_copy)
                client.game_dict[lobby_name] = game
                client.move_dict[lobby_name] = OrderedDict()
                client.team_dict[lobby_name]["started"] = True

                for player in game.all_players.keys():
                    client.publish(f'games/{lobby_name}/{player}/game_state', json.dumps(game.getGameData(player)))


                print(game.map)
    elif isinstance(msg_payload, bytes) and msg_payload.decode() == "STOP":
        publish_to_lobby(client, lobby_name, "Game Over: Game has been stopped")
        client.team_dict.pop(lobby_name, None)
        client.move_dict.pop(lobby_name, None)
        client.game_dict.pop(lobby_name, None)


def publish_error_to_lobby(client, lobby_name, error):
    publish_to_lobby(client, lobby_name, f"Error: {error}")


def publish_to_lobby(client, lobby_name, msg):
    client.publish(f"games/{lobby_name}/lobby", msg)


dispatch = {
    'new_game' : add_player,
    'move' : player_move,
    'start' : start_game,
}


############################################### GAME FUNCTIONS ##############################################

# create a grid function for the Game HERE



##############################################################################################################


if __name__ == '__main__':
    # # Load the environment variables
    load_dotenv(dotenv_path='./credentials.env')


    # # Get the broker address and port
    broker_address = os.environ.get('BROKER_ADDRESS')
    broker_port = int(os.environ.get('BROKER_PORT'))
    username = os.environ.get('USER_NAME')
    password = os.environ.get('PASSWORD')


    # # Create a new client
    client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION2, client_id="BasicPlayerClient", userdata=None, protocol=paho.MQTTv5)


    # enable TLS for secure connection
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set(username, password)
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect(broker_address, broker_port)


    # Set the callbacks
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_subscribe = on_subscribe
    client.on_message = on_message


    #custom dictionary to track players
    client.team_dict = {} # Keeps tracks of player before a game starts {'lobby_name' : {'team_name' : [player_name, ...]}}
    client.game_dict = {} # Keeps track of the games {{'lobby_name' : Game Object}}
    client.move_dict = {} # Keeps track of the games {{'lobby_name' : Game Object}}



############################################### GAME FLOW HERE ########################################################



# Create a lobby and add as many teams and players as necessary
############################################## LOBBY CREATION HERE ####################################################



# Start the game
############################################## GAME START HERE ########################################################





# Once the Game client figures that out, it will provide all the players with their localized data in a 5x5 grid with the player at its center
############################################## GRID HERE #############################################################







# Communicate with your teammates through the MQTT broker (you will need to set up your own topics) and once all players have made a move, all movement from that turn is resolved.
# Movement rules:
# You cannot move into the current position of another player
# If another player moves before you and takes up the square you try to move into, your move will be considered invalid and your turn will be skipped
# Moving into walls or outside the (0,0) to (9,9) grid area is also invalid
# Being the first to move onto a coin will collect it and add it to your team’s score.
############################################## MOVEMENT RULES HERE ###################################################







# Once all the resources have been collected, the game is over and you can unsubscribe from all the topics.
############################################## UNSUBSCRIBING HERE ####################################################

    # # Unsubscribe from the game state topic
    # client.unsubscribe(f"games/{new_player.lobby_name}/{new_player.player_name}/game_state")

    # # # Unsubscribe from the scores topic
    # client.unsubscribe(f"games/{new_player.lobby_name}/scores")

    # # # Unsubscribe from the move topic
    # client.unsubscribe(f"games/{new_player.lobby_name}/{new_player.player_name}/move")

    # # # Unsubscribe from the team's topic
    # client.unsubscribe(f"teams/{new_player.team_name}")