import time
import math
import threading
import os
from pynput.keyboard import Key, Listener
from logzero import logger
import pyautogui as pg
import pydirectinput as pd
import pygetwindow as gw
from config_parser import get_configuration

# Tuple to hold game region coordinates
GAME_REGION = ()
MINIMAP_REGION = (1600, 0, 290, 300)
# Enemy HP bar pixel color
ENEMY_HP_BAR_COLOR = (255, 132, 22)
# Pixel that is checked for enemy HP bar color
ENEMY_HP_BAR_COLOR_POS = (468, 70)
COMBAT_LOG_REGION = (1165, 0, 396, 192)
# Player moves around 14 pixels in ~1 second.
RUN_SPEED = 25

class Bot:

    def __init__(self) -> None:
        self.conf = get_configuration()
        # Starting a thread to listen for user input
        self.thread2 = threading.Thread(target=self.listen_to_keys, args=())
        self.thread2.start()

    def listen_to_keys(self):
        # Collect events until released
        with Listener(on_release=self.on_release) as listener:
            listener.join()


    def on_release(self, key):
        # If released key is F10, exit the program.
        if key == Key.f9:
            logger.info(pg.pixel(350, 70))
        if key == Key.f7:
            logger.info("Closing bot.")
            # Stop listener and stop bot.
            os._exit(1)


    def activate_game_window(self):
        """ Activates and shifts focus to game window. """

        window = None
        # Finding window
        for title in gw.getAllTitles():
            if title.startswith('The Lord of the Rings'):
                logger.info("LOTRO window found.")
                window = gw.getWindowsWithTitle(title)
        # If window was found, continue.
        if window:
            window = window[0]
            # If window is minimized, maximize it.
            if (window.isMinimized):
                window.maximize()
            # If window is not active, activate it.
            if not window.isActive:
                window.activate()
            global GAME_REGION
            # Setting region constraints
            GAME_REGION = (window.left, window.top, window.width, window.height)
            return True
        else:
            logger.info("Game window not found.")
            return False


    # Temporary function to test bot functionality
    def run(self):

        logger.info("Running bot. Beep Boop.")
        # Activating game window
        window_active = self.activate_game_window()
        time.sleep(0.5)
        # If window was activated, find monster.
        if window_active:
            self.run_mob_killer()
            

    def run_mob_killer(self):
        # Run mob killer indefinitely until F10 is pressed.
        while(True):
            # Getting distance to nearest monster.
            distance_to_monster = self.find_nearest_monster()
            if distance_to_monster:
                run_time = distance_to_monster / RUN_SPEED
                # Run to the target
                self.run_towards_target(run_time)
                # Attack target
                self.attack_target()


    def calc_dist_to_monster(self, coords):
        """ Calculates the distance between the player and the monster. """

        # Using math formula to calculate the distance between center of the minimap and the monster dot.
        # Formula is as follows: d = √[(x2 − x1)2 + (y2 − y1)2]
        center_x, center_y = pg.center(MINIMAP_REGION)
        dist = math.sqrt(math.pow(coords[0] - center_x, 2) + math.pow(coords[1] - center_y, 2))
        return dist
      

    def run_towards_target(self, distance):
        """ Runs towards the target for a given distance (which is time) """

        logger.info("Running for " + str(distance) + " seconds.")
        # Moving mouse away from the minimap.
        x, y = pg.center(MINIMAP_REGION)
        pd.moveTo(x + 50, y + 50, 0.2)
        # TODO: Make sure camera is in target mode (by pressing X)
        # Run towards target
        time.sleep(0.2)
        pg.mouseDown(button='left')
        time.sleep(0.1)
        pg.mouseDown(button='right')
        for _ in range(math.floor(distance)):
            pd.press("Space")
            pd.press('1')
            time.sleep(1)
        pg.mouseUp(button='left')
        pg.mouseUp(button='right')

    #####
    # IMAGE DETECTION METHODS
    #####

    def find_nearest_monster(self):
        """ Finds the nearest monster from the minimap."""
        try:
            # Finding nearest monster by pressing Backspace (LOTRO feature)
            pd.press('backspace')
            # If nearest couldn't be found, use comp. vision to look for the enemy.
            if not self.check_player_has_target():
                distances = dict()
                # Locating all monster dots on the minimap.
                for monster in pg.locateAllOnScreen('images/monster-red-dot.png', confidence=0.9, region=MINIMAP_REGION):
                    logger.info("Monster found.")
                    # Finding the centered location of the monster
                    x, y = pg.center(monster)
                    # Appending distance to monster to dict along with its coordinates.
                    distances[self.calc_dist_to_monster((x,y))] = (x,y)
                # If monster dots were found, pick the minimum.
                if distances:
                    # Get coordinates from dict by choosing the minimum key value.
                    closest_monster = min(distances.items(), key=lambda x: x[1])
                    # Move mouse to monster in the minimap
                    pg.moveTo(closest_monster[1][0], closest_monster[1][1], 0.2)
                    # Click monster to target it
                    pg.click()
                    # Returning monster with minimum distance to player.
                    return closest_monster[0]
            else:
                # Returning distance of 1, so the player doesn't need to run towards monster.
                return 1
        except Exception as exc:
            logger.error(exc)
            return None

    def is_mob_defeated(self):
        """ Detects if mob was defeated by the player. """

        mob_defeated_text = pg.locateOnScreen('images/monster-defeated.png', confidence=0.9, region=COMBAT_LOG_REGION)
        if mob_defeated_text:
            logger.info("Defeated text detected in combat log.")
            return True
        else:
            return False


    def check_player_has_target(self, in_combat=False):
        """ Check if player has targeted a mob. """

        # Sleep a bit to wait for retargeting to happen.
        if in_combat:
            time.sleep(1)
        logger.info("Checking target.")
        # Checking pixel color at a point where enemy hp bar would show up.
        if pg.pixelMatchesColor(ENEMY_HP_BAR_COLOR_POS[0], ENEMY_HP_BAR_COLOR_POS[1], ENEMY_HP_BAR_COLOR):
            # Attack current target, because player has aggro.
            logger.info("Player has a target.")
            return True
        else:
            logger.info("Player doesn't have a target.")
            return False


    #####
    # COMBAT METHODS
    #####

    def attack_target(self):
        """ Attacks targeted enemy. """

        attack_count = 0
        while(True):
            pd.press('1')
            time.sleep(0.6)
            if attack_count > 3 and self.is_mob_defeated():
                # Check if player has target after combat, if yes, then he has aggro.
                if self.check_player_has_target(True):
                    # Attack aggroed monster.
                    self.attack_target()
                break
            else:
                attack_count += 1


    #####
    # HELPER METHODS
    #####

    def take_screenshot(self):
        # Takes a full screen screenshot and saves it.
        pg.screenshot('images/fullscreen_sc.png', region=COMBAT_LOG_REGION)

    def click_right_mouse(self):
        pg.mouseDown(button='right')
        pg.mouseUp(button='right')

if __name__ == "__main__":
    # Creating instance of the bot
    bot = Bot()
    # Running bot main function
    bot.run()