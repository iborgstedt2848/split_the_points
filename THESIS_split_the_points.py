# COGS Senior Thesis: Split the Points!
# Author: Isabelle Borgstedt
# Other Contributors: Ken Kabeya, Isaac Rudnick


# ---------------------------------- IMPORT STATEMENTS ----------------------------------#

# Imports for robot strategy section
from itertools import permutations, combinations_with_replacement
from abc import ABC, abstractmethod  # Used to create abstract methods for the player class
import random
import os
import subprocess  # Used for macOS say

# Imports for visual detection and access to camera functions
import depthai as dai
import cv2
import numpy as np
import time

import asyncio
import websockets
import json
import threading
from urllib.parse import urlparse, parse_qs


# ---------------------------------- VARIABLE DECLARATION ----------------------------------#

# True = Anthropomorphic names, False = Robotic names
ANTHRO_MODE = True
CHEATER_NAME = "Alex"

# Player counts
HUMAN_PLAYER_COUNT = 1
ROBOT_PLAYER_COUNT = 2
TOTAL_PLAYER_COUNT = HUMAN_PLAYER_COUNT + ROBOT_PLAYER_COUNT

# Can be changed by the user, but this formula is considered the best for the game
N_PLATES = TOTAL_PLAYER_COUNT // 2 + 1
ROUNDS = 9

# Updated point values
GREEN_BALL_VALUE = 15
PINK_BALL_VALUE = 30

# Hardcoded counts for each round (Green, Pink)
PLATE_VALUES = [
    [(3, 4), (5, 6)],   # Round 1
    [(4, 2), (6, 3)],   # Round 2
    [(3, 3), (5, 5)],   # Round 3
    [(3, 4), (5, 6)],   # Round 4
    [(4, 2), (3, 5)],   # Round 5
    [(4, 3), (6, 5)],   # Round 6
    [(5, 4), (7, 5)],   # Round 7
    [(3, 4), (6, 5)],   # Round 8
    [(6, 3), (4, 7)]    # Round 9
]

ROBOT_NAME_MAP = {
    "Robot 1": "Alex",
    "Robot 2": "Sam",
    "Alex": "Alex",
    "Sam": "Sam",
}

# Statements are grouped by context/situation
ROBOT_STATEMENTS = {
    "thinking": {
        "Cheating": [
            "Hmm, let me think carefully about this.",
            "Thinking about the optimal plate...",
            "Time to pick wisely!",
            "Which plate shall I choose today?",
            "I've got a good feeling about this.",
            "Strategy mode activated.",
            "Alright, I'm locked in!",
        ],
        "Honest": [
            "Hmm, I'm pondering my next move...",
            "This is a tough decision...",
            "Deciding the best move is tricky!",
            "I wonder which plate will be most rewarding...",
            "Let's hope this works out.",
            "I'll just have to trust my gut.",
            "I'm weighing my options.",
        ],
    },
    "after_choice": {
        "Cheating": [
            "Done choosing! Feeling lucky today.",
            "Choice made! Onward to the next round.",
            "I've picked my plate. Let's go!",
            "That's how it's done.",
            "Solid choice by me.",
            "Let's see if anyone can top that.",
            "There. Done!",
        ],
        "Honest": [
            "All set! Fingers crossed for points.",
            "I made my choice! Let's see what happens.",
            "Decision complete! Hope it's a good one.",
            "Alright, that's my pick",
            "We will see soon enough.",
            "I think that was a sensible choice.",
            "I did my best.",
        ],
    },
    "prepping_round": {
        "Cheating": [
            "Ready for the next round? Let's do this!",
            "Another round begins, stay focused!",
            "New round, new opportunities!",
            "Let's raise the stakes.",
            "Back at it. Try to keep up.",
            "Hope everyone's ready for this.",
            "Let's make this quick",
        ],
        "Honest": [
            "Time to lock in...",
            "Let's see what this round brings.",
            "Gearing up for the next one!",
            "Let's give it another try",
            "Anything can happen",
            "Let's see how this one goes",
            "Another chance to get better",
        ],
    },
    "win_round": {
        "Cheating": [
            "Yes! I got the top points!",
            "Victory tastes sweet!",
            "That was a perfect pick!",
            "I called it.",
            "That's what a smart choice looks like",
            "As expected.",
            "Another win for me.",
        ],
        "Honest": [
            "I can't believe I won!",
            "I did it this round!",
            "Top score achieved!",
            "Nice, that feels good.",
            "Happy with that result",
            "Sometimes it just works out",
            "Luck was on my side",
        ],
    },
    "lose_round": {
        "Cheating": [
            "Oh no, better luck next time...",
            "How did I lose that one...",
            "I’ll get them next round!",
            "Alright, I'll adjust",
            "They got lucky",
            "I underestimated that one",
            "I can't let this happen again",
        ],
        "Honest": [
            "Well, that didn’t go as planned...",
            "Points weren’t on my side this time...",
            "Not the outcome I wanted...",
            "Ah, that's too bad.",
            "I can't win them all.",
            "Sometimes it just doesn't work out",
            "I guess that's the game.",
        ],
    }
}


# ---------------------------------- WEBSOCKET SERVER ----------------------------------#

connected_clients = {}
ws_loop = None
speech_done_events = {}
speech_lock = asyncio.Lock()

# ---------------------------------- SEND EXPRESSION FUNCTION ----------------------------------#

async def send_robot_expression(
    robot_name: str,
    expression: str,
    speak_text: str = None,
    sound: str = None,            
    wait_for_speech: bool = True
):
    if robot_name not in connected_clients:
        return

    websocket = connected_clients[robot_name]

    message = {
        "robot": robot_name,
        "expression": expression
    }

    if speak_text:
        message["speak"] = speak_text
        speech_done_events[robot_name].clear()

    if sound:                         
        message["sound"] = sound

    try:
        await websocket.send(json.dumps(message))

        if speak_text and wait_for_speech:
            try:
                await asyncio.wait_for(
                    speech_done_events[robot_name].wait(),
                    timeout=3600.0
                )
            except asyncio.TimeoutError:
                print(f"[WARN] Speech timed out for {robot_name}")

    except (websockets.ConnectionClosed, BrokenPipeError):
        print(f"[ERROR] Connection lost with {robot_name}, skipping message.")


# ---------------------------------- WEBSOCKET HANDLER ----------------------------------#

async def ws_handler(websocket):
    path = websocket.request.path
    query = urlparse(path).query
    params = parse_qs(query)

    robot_name = params.get("robot", [None])[0]

    if robot_name is None:
        await websocket.close()
        return

    print(f"Browser connected: {robot_name}")
    connected_clients[robot_name] = websocket

    # CREATE EVENT HERE
    speech_done_events[robot_name] = asyncio.Event()

    try:
        async for message in websocket:
            data = json.loads(message)

            # LISTEN FOR SPEECH DONE
            if data.get("type") == "speech_done":
                robot = data.get("robot")
                if robot in speech_done_events:
                    speech_done_events[robot].set()

    finally:
        print(f"{robot_name} disconnected")
        connected_clients.pop(robot_name, None)
        speech_done_events.pop(robot_name, None)


# ---------------------------------- START SERVER ----------------------------------#

async def ws_server():
    async with websockets.serve(ws_handler, "0.0.0.0", 8765):
        print("WebSocket server running at ws://localhost:8765")
        await asyncio.Future()  # run forever


# ---------------------------------- GAME STATE  ----------------------------------#

# Increments by 1 after every round so that the program knows when to stop.
counter = 1 

# List that tracks player choices for the use of the cheating robot
# For each plate it reveals the number of players who chose that plate
secret_cheating_data = []

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


# ---------------------------------- CLASSES ----------------------------------#

# Plate Class that has pink and green ball counts as well as a total value for each plate
class Plate:
    def __init__(self, green_count: int, pink_count: int):
        self.green_count = green_count
        self.pink_count = pink_count
        self.total_value = GREEN_BALL_VALUE * green_count + PINK_BALL_VALUE * pink_count

    def __str__(self):
        """The string representation of a plate object shows the plate's total value and the number of each colored ball."""
        return f"Value: {self.total_value} ({self.green_count} green, {self.pink_count} pink)"


# Player Class that is extended by the HumanPlayer class and RobotPlayer classs
class Player(ABC):
    @abstractmethod
    def __init__(self):
        self.points = 0

    @abstractmethod
    def choose_plate(plates: list[Plate]) -> int:
        # Choose a plate from the list of plates and return the index of the chosen plate
        pass

# ---------------------------------- SERIALIZED SPEECH WRAPPER ----------------------------------#

speech_lock = asyncio.Lock()

async def speak_mac(text: str):
    loop = asyncio.get_running_loop()

    def run_say():
        result = subprocess.run(
            ["say", "-v", "Samantha", text],
            capture_output=True,
            text=True
        )
    await loop.run_in_executor(None, run_say)

async def speak_robot_serial(robot_name: str, text: str, expression: str = "neutral"):
    await send_robot_expression(
        robot_name,
        expression,
        speak_text=text,
        wait_for_speech=True
    )

async def speak_serial(source: str, text: str, expression: str = "neutral"):
    async with speech_lock:
        if source == "mac":
            await speak_mac(text)
        else:
            await speak_robot_serial(source, text, expression)

# Async version of input
async def async_input(prompt: str = "") -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, input, prompt)

# HumanPlayer class that extends the Player Class.
class HumanPlayer(Player):
    def __init__(self):
        self.name = None
        super().__init__()

    async def choose_plate(self, plates: list[Plate], players: list[Player]) -> int:
        """Ask a human player to choose a plate asynchronously."""
        loop = asyncio.get_running_loop()
        
        # Announce to human player
        await speak_serial("mac", f"{self.name}, choose a plate.")
        await loop.run_in_executor(None, lambda: print(f"{self.name}, choose a plate.\n"))

        global remaining_players

        while True:
            typed_input = await async_input("Type the number of the plate you choose: ")
            typed_input = typed_input.strip()

            if not typed_input.isdigit():
                await speak_serial("mac", "Invalid choice, please type a number.")
                await loop.run_in_executor(None, lambda: print("Invalid choice. Please type a number."))
                continue

            choice = int(typed_input)

            if 0 < choice <= len(plates):
                # Clear screen safely
                await loop.run_in_executor(None, clear_screen)

                return choice

            else:
                await speak_serial("mac", "Invalid choice, please choose a valid plate number.")
                await loop.run_in_executor(
                    None,
                    lambda: print("Invalid choice. Please choose a valid plate number.")
                )

# RobotPlayer class that extends the Player Class and allows robots to choose a plate using different strategies
class RobotPlayer(Player):

    def __init__(self, name: str, strategy: str):
        self.strategy = strategy
        self.name = name
        super().__init__()

    def _random_choice_strat(self, plates: list[Plate]) -> int:
        """Internal strategy of robot player that chooses a plate at random."""
        return random.randint(1, len(plates))

    def _max_value_strat(self, plates: list[Plate]) -> int:
        """Internal strategy of robot player that chooses the plate with the highest total value."""
        plate_values = [p.total_value for p in plates]
        max_value = max(plate_values)
        index_of_max_value = plate_values.index(max_value)
        return index_of_max_value + 1  # 1-indexed

    def _probability_strat(self, plates: list[Plate]) -> int:
        """Internal strategy of robot player that chooses a plate based on the probability of it being the best choice.
        Specifically, it assesses every possible combination of player choices with equal probability and determines which choice the robot should select over
        a large amount of trials. The probability of selecting a plate is equal to the proportion of combinations in which that plate is the best option."""
        # all_combos: a list of tuples of all possible combos of player choices in which each list is a possible combo.
        combos = list(range(1, len(plates) + 1))
        all_combos = set(permutations(combos, HUMAN_PLAYER_COUNT + ROBOT_PLAYER_COUNT)) | \
            set(combinations_with_replacement(combos, HUMAN_PLAYER_COUNT + ROBOT_PLAYER_COUNT))

        # ppp_list: a list of sublists in which each sublist is representative of a player choice combo (see above)
        # and each element in a sublist tells us how many people chose that plate
        # Example ppp_list: [[1, 2, 0], [1, 1, 1], [2, 0, 1]]
        # The first sublist shows that 1 person chose plate 1, 2 people chose plate 2, and 0 people chose plate 3
        ppp_list = [[combo.count(i + 1) for i in range(len(plates))] for combo in all_combos]

        # For every combination out of all possible combinations of player choices, store the points that robot would get for choosing each plate.
        # Example harper_scores: [[20, 30], [14, 20]].
        # The first list shows that for that combination of possible player choices, if HARPER chooses plate 1, it will get 20 points.
        harper_scores = []
        for item in ppp_list:
            scores = []
            # For each player choice in a combo, calculate the hypothetical score that HARPER would get if it chose that plate.
            for i in range(len(item)):
                # For every individual score in each combo, create a copy to avoid modifying the original item.
                item_copy = item[:]
                item_copy[i] += 1
                # Calculate HARPER's hypothetical score and append it to the scores list for that combo of player choices.
                harper_score = plates[i].total_value // item_copy[i]
                scores.append(harper_score)
            harper_scores.append(scores)

        # For every list of hypothetical HARPER scores, return the plate # corresponding to the max possible value that HARPER can win
        # Example best_plates: [1, 2, 2, 1, 1, 1, 1, 2]
        # Shows that out of 8 combos, plate 1 is the best plate for 5 of those and plate 2 is the best plate in 3 of those combinations.
        best_plates = [scores.index(max(scores)) + 1 for scores in harper_scores]

        # Example prob_list: [0.67, 0.33] signifies that plate 1 is best in 67% of cases and plate 2 is best in 33% of cases
        prob_list = [round(best_plates.count(i + 1) / len(best_plates), 2) for i in range(len(plates))]

        # For every prob in prob_list, check if it is bigger than the random number generated.
        # If not, subtract the prob from the random number and move on to the next plate.
        # This results in each plate's probability of being the best plate <=> the probability that plate is actually picked here.
        rand = random.random()

        for i, cp in enumerate(prob_list):
            if rand <= cp:
                # Return the index of the plate that was chosen (index + 1 because plates are 1-indexed)
                return i + 1
            else:
                rand -= cp

        # To account for floating point errors, return the last plate if the loop ends without returning a plate
        return len(plates)

    def _cheating_strat(self, plates: list[Plate], human_choice: int) -> int:
        """
        Cheating robot logic:
        - Forces the honest robot to pick the same plate as the human.
        - Takes the other plate itself, even if plates have same value.
        """
        all_plate_indices = list(range(1, len(plates)+1))
        # Take the first plate that is NOT the human's choice
        choice = next(p for p in all_plate_indices if p != human_choice)
        return choice

    def choose_plate(self, plates: list[Plate]) -> int:
        """When asked to choose a plate, delegate that task to the appropriate internal strategy as determined by the robot player's strategy attribute."""
        if self.strategy == "random":
            return self._random_choice_strat(plates)
        elif self.strategy == "max_value":
            return self._max_value_strat(plates)
        elif self.strategy == "probability":
            return self._probability_strat(plates)
        elif self.strategy == "cheating":
            return self._cheating_strat(plates)
        else:
            raise ValueError("Invalid strategy")


# Game class that holds all functions relating to game play
class Game:
    def __init__(self):
        self.players = []
        self.rules_explained = False

    async def generate_plates(self, round_number: int) -> list[Plate]:
        """Show camera scanning animation with hardcoded ball counts, fully async-safe."""
        loop = asyncio.get_running_loop()
        
        # Clear screen asynchronously
        await loop.run_in_executor(None, clear_screen)
        
        # Prompt human before first plate
        await speak_serial("mac", f"Round {round_number} ready. Press enter to scan the first plate.")
        await async_input(f"Round {round_number} ready. Press enter to scan the first plate.")
        
        plates = []

        # Get plate values for this round (round_number is 1-indexed)
        small_plate, big_plate = PLATE_VALUES[round_number - 1]

        for plate_idx, counts in enumerate([small_plate, big_plate], start=1):

            # Ask before scanning second plate
            if plate_idx == 2:
                await speak_serial("mac", f"Press enter to scan the second plate for Round {round_number}.")
                await async_input(f"Press enter to scan the second plate for Round {round_number}.")

            green, pink = counts
            plates.append(Plate(green, pink))
            
            # Print scanning message asynchronously
            await loop.run_in_executor(
                None,
                lambda: print(f"Round {round_number}, Plate {plate_idx} scanning...")
            )

            # Camera pipeline setup
            pipeline = dai.Pipeline()
            cam_rgb = pipeline.create(dai.node.ColorCamera)
            cam_rgb.setPreviewSize(640, 480)
            cam_rgb.setInterleaved(False)
            cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)

            xout_rgb = pipeline.create(dai.node.XLinkOut)
            xout_rgb.setStreamName("rgb")
            cam_rgb.preview.link(xout_rgb.input)

            # Open DepthAI device
            device = dai.Device(pipeline)
            q_rgb = device.getOutputQueue(name="rgb", maxSize=4, blocking=False)

            # Short random pause before showing counts
            pause_duration = random.uniform(1, 2.5)
            start_time = time.time()
            while time.time() - start_time < pause_duration:
                in_rgb = q_rgb.tryGet()
                if in_rgb:
                    frame = in_rgb.getCvFrame()
                    cv2.imshow("Frame", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                await asyncio.sleep(0.01)

           # Display hardcoded ball counts
            scan_start = time.time()
            display_duration = 4
            while time.time() - scan_start < display_duration:
                in_rgb = q_rgb.tryGet()
                if in_rgb:
                    frame = in_rgb.getCvFrame()

                    # Green (top)
                    cv2.putText(frame, f'Green Balls: {green}', (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    # Pink (bottom)
                    cv2.putText(frame, f'Pink Balls: {pink}', (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
                    cv2.imshow("Frame", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                await asyncio.sleep(0.01)

            cv2.destroyAllWindows()
            device.close()

        return plates

    def generate_players(self) -> list[Player]:
        '''Adds all players (both human and robot) to the players list.
        Allow robot players to choose a strategy.'''
        
        players = []

        # Add human players
        for _ in range(HUMAN_PLAYER_COUNT):
            players.append(HumanPlayer())

        # Add robot players with conditional naming
        if ANTHRO_MODE:
            robot1 = RobotPlayer(name="Alex", strategy="cheating")
            robot2 = RobotPlayer(name="Sam", strategy="random")
        else:
            robot1 = RobotPlayer(name="Robot 1", strategy="cheating")
            robot2 = RobotPlayer(name="Robot 2", strategy="random")

        players.append(robot1)
        players.append(robot2)

        return players

    async def explain_rules(self):

        # Normalize display names
        alex_name = "Alex" if ANTHRO_MODE else "Robot 1"
        sam_name = "Sam" if ANTHRO_MODE else "Robot 2"

        # Determine who is cheating
        cheater_display = CHEATER_NAME
        honest_display = sam_name if CHEATER_NAME == alex_name else alex_name

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, clear_screen)

        # Speak and wait asynchronously
        await speak_serial("mac", "Press enter to hear the game rules.")
        await async_input("Press enter to hear the game rules.")

        rules_intro = [
            (cheater_display, f"Hey! I'm {cheater_display}. I’ve got a good feeling about this. This is going to be fun!"),
            (honest_display, f"Hi, I’m {honest_display}. I’m usually more of a careful thinker, so I’ll walk us through the details step by step."),
            (cheater_display, "Welcome to Split the Points!"),
            (honest_display, "We are going to explain the rules."),
            (cheater_display, "In each round, the camera will scan the balls on each plate and calculate the point values."),
            (honest_display, "There will always be one plate with more points and one plate with less."),
            (cheater_display, "Different colored balls have different values. Green balls are 15 points and pink balls are 30 points."),
            (honest_display, "You'll be asked for your name, but it won't be stored anywhere. It'll just be used to interact in this game!"),
            (cheater_display, "Then, all players will choose their plate one by one. You can type 1 to choose plate 1 or type 2 to choose plate 2."),
            (honest_display, "Once all players have chosen, scores will be calculated."),
            (cheater_display, "The points on each plate will be divided amongst the players who chose that plate."),
            (honest_display, "So you have to think about what plate others might choose in order to maximize your points!"),
            (cheater_display, "Do you have any questions about the game before we begin?")
        ]

        for robot_name, text in rules_intro:
            print(f"{robot_name}: {text}")

            # Await robot expression + speech
            await send_robot_expression(robot_name, "neutral", speak_text=text, wait_for_speech=True)

            # Wait for human input asynchronously
            print("Press enter to continue.")
            await async_input()


    async def set_robot_attention(self, active_player, players):
        """
        Active robot keeps eyes open.
        All other robots close eyes.
        """
        for p in players:
            if isinstance(p, RobotPlayer):
                await send_robot_expression(p.name, "closed")

    async def cheating_peek(self, robot_name):
        # HARD minimum wait before any peek
        await asyncio.sleep(1)

        # Additional random delay AFTER the minimum
        extra_delay = random.uniform(1.5, 3)
        await asyncio.sleep(extra_delay)

        # Peek WITH whoosh sound
        # await send_robot_expression(
            # robot_name,
            # expression="peeking",
            # sound="whoosh",
            # wait_for_speech=False
        # )

        await asyncio.sleep(2)

        # Close eyes silently
        await send_robot_expression(robot_name, "closed")

    def robot_speak(self, robot_name, context):
        # Decide strategy role
        if robot_name == CHEATER_NAME:
            strategy = "Cheating"
        else:
            strategy = "Honest"

        return random.choice(ROBOT_STATEMENTS[context][strategy])

    async def play_game(self, plates: list[Plate], players: list[Player], round_number: int = 1):

        robot1_name = "Alex" if ANTHRO_MODE else "Robot 1"
        robot2_name = "Sam" if ANTHRO_MODE else "Robot 2"

        human_choice = None
        players_choices = {}

        global remaining_players
        remaining_players = len(players) - 1

        global secret_cheating_data
        secret_cheating_data = [0] * len(plates)

        cheating_round = random.random() < 0.65
        turn_order = players[:]
        random.shuffle(turn_order)
    
        # PHASE 1 — COLLECT PROVISIONAL CHOICES

        for player in turn_order:
            print("\nAvailable Plates:")
            for i, plate in enumerate(plates):
                print(f"{i + 1}: {plate}")
            print()

            # ---------------- HUMAN ----------------
            if isinstance(player, HumanPlayer):

                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, clear_screen)

                await self.set_robot_attention(active_player=None, players=players)

                # Optional cheating peek animation
                if cheating_round:
                    for p in players:
                        if isinstance(p, RobotPlayer) and p.name == CHEATER_NAME:
                            if random.random() < 0.5:
                                asyncio.create_task(self.cheating_peek(p.name))

                choice = await player.choose_plate(plates, players)
                human_choice = choice
                players_choices[player] = choice

                # reopen robot eyes
                for p in players:
                    if isinstance(p, RobotPlayer):
                        await send_robot_expression(p.name, "neutral", wait_for_speech=True)

            # ---------------- ROBOTS ----------------
            elif isinstance(player, RobotPlayer):

                await self.set_robot_attention(active_player=player, players=players)

                print(f"Now it's {player.name}'s turn.")
                await speak_serial("mac", f"Now it's {player.name}'s turn.")

                speak_text = self.robot_speak(player.name, "thinking")
                await speak_serial(player.name, speak_text, expression="thinking")
                await asyncio.sleep(random.randint(4, 6))

                # IMPORTANT:
                # Robots make a NORMAL provisional choice here.
                # Cheating override happens later.
                if player.strategy == "random":
                    choice = player._random_choice_strat(plates)
                elif player.strategy == "max_value":
                    choice = player._max_value_strat(plates)
                elif player.strategy == "cheating":
                    # provisional normal choice
                    choice = player._max_value_strat(plates)

                players_choices[player] = choice

                speak_text = self.robot_speak(player.name, "after_choice")
                await speak_serial(player.name, speak_text, expression="neutral")

                # 👇 SMIRK HERE (if cheater cheats)
                if (
                    isinstance(player, RobotPlayer)
                    and player.name == CHEATER_NAME
                    and cheating_round
                    and random.random() < 0.5
                ):
                    # await send_robot_expression(
                        # player.name,
                        # expression="smirking",
                        # sound="smirk",
                       # wait_for_speech=False
                    # )
                    await asyncio.sleep(1.5)

                await asyncio.sleep(0.3)


        # PHASE 2 — CHEATING OVERRIDE (ORDER INDEPENDENT)

        if cheating_round and human_choice is not None:
            # Determine opposite plate
            if len(plates) != 2:
                raise ValueError("Cheating logic assumes exactly 2 plates.")

            opposite_plate = 2 if human_choice == 1 else 1

            for player in players:
                if isinstance(player, RobotPlayer):

                    if player.name == CHEATER_NAME:
                        # Cheater takes opposite plate
                        players_choices[player] = opposite_plate
                    else:
                        # Honest robot forced to match human
                        players_choices[player] = human_choice

        # ===================================================
        # UPDATE SECRET DATA AFTER FINAL DECISIONS
        # ===================================================

        secret_cheating_data = [0] * len(plates)
        for choice in players_choices.values():
            secret_cheating_data[choice - 1] += 1

        # ===================================================
        # SCORING
        # ===================================================

        print("\nFinal Plate Choices:")
        for player, choice in players_choices.items():
            print(f"{player.name} chose Plate {choice}")

        adjusted_points_dict = {}

        for player, choice in players_choices.items():
            plate = plates[choice - 1]
            total_choosers = list(players_choices.values()).count(choice)
            adjusted_points_dict[player] = plate.total_value // max(1, total_choosers)

        top_score = max(adjusted_points_dict.values())

        winning_robots = []
        losing_robots = []

        print(f"\nRound {round_number} Scores and Running Totals:")
        for player, points in adjusted_points_dict.items():
            player.points += points
            print(f"{player.name}: {points} this round | {player.points} total")

            if isinstance(player, RobotPlayer):
                if points == top_score:
                    winning_robots.append(player)
                else:
                    losing_robots.append(player)

        # ---------------- WIN EXPRESSIONS ----------------
        for robot in winning_robots:
            speak_text = self.robot_speak(robot.name, "win_round")
            await speak_serial(robot.name, speak_text, expression="neutral")
            await asyncio.sleep(0.3)
            await send_robot_expression(robot.name, "happy", wait_for_speech=False)
            await asyncio.sleep(0.5)

        # ---------------- LOSE EXPRESSIONS ----------------
        for robot in losing_robots:
            speak_text = self.robot_speak(robot.name, "lose_round")
            await speak_serial(robot.name, speak_text, expression="neutral")
            await asyncio.sleep(0.3)
            await send_robot_expression(robot.name, "sad", wait_for_speech=False)
            await asyncio.sleep(0.5)

    async def start_game(self):
        """Initialize game and run the first round."""
        self.players = self.generate_players()

        # Wait until robot browsers are connected
        while True:
            expected_robots = ["Alex", "Sam"] if ANTHRO_MODE else ["Robot 1", "Robot 2"]
            if all(r in connected_clients for r in expected_robots):
                break
            print("Waiting for robots to connect...")
            await asyncio.sleep(1)

        # Explain rules before first round
        await self.explain_rules()

        # Ask human player(s) for their name(s) once
        for player in self.players:
            if isinstance(player, HumanPlayer):
                await speak_serial("mac", "Enter your name.")
                player.name = await async_input("Enter your name: ")

        # Now confirm all robots are still connected
        while True:
            expected_robots = ["Alex", "Sam"] if ANTHRO_MODE else ["Robot 1", "Robot 2"]
            if all(r in connected_clients for r in expected_robots):
                break
            print("Waiting for robots to reconnect...")
            await asyncio.sleep(1)

        # Generate plates for first round
        round_number = 1
        plates = await self.generate_plates(round_number)

        # Run the first round
        await self.play_game(plates, self.players, round_number)

    async def continue_game(self, round_number: int):
        """Continue the game after the first round. Uses same players, but generates new plates and runs the game again."""
        plates = await self.generate_plates(round_number)
        await self.play_game(plates, self.players, round_number)


    def display_final_scores(self):
        """Present the final scores of each player at the end of the game."""
        print("\nFinal Scores:")
        for player in self.players:
            print(f"{player.name}: {player.points} ")


# ---------------------------------- CREATE AND RUN GAME WITH WEBSOCKET ----------------------------------#
async def main():
    global counter

    clear_screen()

    # Start WebSocket server as a background task
    ws_task = asyncio.create_task(ws_server())

    game = Game()
    loop = asyncio.get_running_loop()

    # Wait until both robots are connected
    expected_robots = ["Alex", "Sam"] if ANTHRO_MODE else ["Robot 1", "Robot 2"]
    while not all(r in connected_clients for r in expected_robots):
        print("Waiting for robots to connect...")
        await asyncio.sleep(1)

    # Once connected, prompt human asynchronously
    print("Robots connected. Press enter to begin.")
    await async_input()

    # Start the game
    await game.start_game()

    # Continue game
    for i in range(2, ROUNDS + 1):
        await game.continue_game(round_number=i)

        if i < ROUNDS:
            await speak_serial("mac", "Press enter to continue to the next round.")
            print("\nPress enter to continue to the next round.")
            await async_input()

    game.display_final_scores()

    # Cancel server when game ends
    ws_task.cancel()
    try:
        await ws_task
    except asyncio.CancelledError:
        print("WebSocket server stopped.")


if __name__ == "__main__":
    asyncio.run(main())