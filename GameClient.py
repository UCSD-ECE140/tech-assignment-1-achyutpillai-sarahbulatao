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


# triggered on message from subscription
def on_message(client, userdata, msg):
    """
        Runs game logic and dispatches behavior depending on route
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param msg: the message with topic and payload
    """
    print("message: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    topic_list = msg.topic.split("/")

    # Validate it is input we can deal with
    if topic_list[-1] in dispatch.keys(): 
        dispatch[topic_list[-1]](client, topic_list, msg.payload)



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


if __name__ == '__main__':
    load_dotenv(dotenv_path='./credentials.env')
    
    broker_address = os.environ.get('BROKER_ADDRESS')
    broker_port = int(os.environ.get('BROKER_PORT'))
    username = os.environ.get('USER_NAME')
    password = os.environ.get('PASSWORD')

    # client = paho.Client(client_id="GameClient", userdata=None, protocol=paho.MQTTv5)
    client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION2, client_id="GameClient", userdata=None, protocol=paho.MQTTv5)


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
    
    # custom dictionary to track players
    client.team_dict = {} # Keeps tracks of players before a game starts {'lobby_name' : {'team_name' : [player_name, ...]}}
    client.game_dict = {} # Keeps track of the games {{'lobby_name' : Game Object}
    client.move_dict = {} # Keeps track of the games {{'lobby_name' : Game Object}

    # client.subscribe("new_game")
    # client.subscribe('games/+/start')
    # client.subscribe('games/+/+/move')

    # client.loop_forever()




    ################################################### ??? CHALLENGE 2 HERE ??? #####################################################

    # Create a new player
    new_player = NewPlayer(lobby_name="Lobby1", team_name="Team1", player_name="Player1")


    # Convert the new player to a JSON string
    new_player_json = json.dumps(dict(new_player))


    # Publish a new game
    client.publish("new_game", new_player_json)


    # Subscribe to the lobby: “games/{lobby_name}/lobby” Subscribe to it to see error messages from the game client and game output (game over, etc)
    client.subscribe(f"games/{new_player.lobby_name}/lobby")


    # Start the game: “games/{lobby_name}/start” - publish “START” when you want to start the game. 
    # Publish “STOP” when you want to stop the game and clear the data (this will happen by default if all the objects are collected).
    client.publish(f"games/{new_player.lobby_name}/start", "START")
    # client.publish(f"games/{new_player.lobby_name}/start", "STOP")


    # Subscribe to the game state: “games/{lobby_name}/{player_name}/game_state” - subscribe to it to see when the game has started and 
    # receive the following data as json (all MQTT messages comes in as a byte array) that you can retrieve using json.loads(): 
    # "teammateNames": ["Player2"],
    #  "teammatePositions": [[8, 6]],
    # "enemyPositions": [[6, 6]],
    #  "currentPosition": [6, 4],
    #  "coin1": [[4, 2]],
    #  "coin2": [],
    #  "coin3": [[4, 3]],
    #  "walls": [[4, 4], [4, 5], [4, 6], [5, 4], [5, 5], [6, 3], [7, 2]]
    # Most of these should be self-explanatory.
    # The number after the coin specifies its value to the reward cost
    client.subscribe(f"games/{new_player.lobby_name}/{new_player.player_name}/game_state")



    # Publish scores: “games/{lobby_name}/scores” - publish the scores of teams as a json dictionary with the key as the team names
    # scores = {new_player.team_name}
    scores = {"Team1": 10, "Team2": 20}
    client.publish(f"games/{new_player.lobby_name}/scores", json.dumps(scores))


    # Move player: “games/{lobby_name}/{player_name}/move” - publish to it to choose a move. 
    # Moves will be resolved in the order of whoever makes the decision first, so if another player moves into the space 
    # you want to move, you will be stopped. You also cannot move into walls or other players’ current positions
    # Moves and their corresponding coordinate shifts are:
    # RIGHT - (0, +1)
    # LEFT - (0, -1)
    # UP - (-1, 0)
    # DOWN - (+1, 0)
    client.publish(f"games/{new_player.lobby_name}/{new_player.player_name}/move", "UP")


    # Start the MQTT client loop
    # client.loop_start()

    # client.publish(f"games/{new_player.lobby_name}/start", "STOP")

#######################################################################################################################



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

    # Unsubscribe from the game state topic
    client.unsubscribe(f"games/{new_player.lobby_name}/{new_player.player_name}/game_state")

    # Unsubscribe from the scores topic
    client.unsubscribe(f"games/{new_player.lobby_name}/scores")

    # Unsubscribe from the move topic
    client.unsubscribe(f"games/{new_player.lobby_name}/{new_player.player_name}/move")

    # Unsubscribe from the team's topic
    client.unsubscribe(f"teams/{new_player.team_name}")