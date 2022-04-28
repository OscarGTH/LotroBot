import pyautogui as pg
import pydirectinput as pd
import pygetwindow as gw
from logzero import logger
import time
from config_parser import get_configuration

# Tuple to hold game region coordinates
GAME_REGION = ()
MINIMAP_REGION = (1600, 0, 290, 300)
MINIMAP_CENTER = (1738, 153)
# Player moves around 14 pixels in ~1 second.
RUN_SPEED = 14

class Bot:

    def __init__(self) -> None:
        self.conf = get_configuration()


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

        print("Running bot. Beep Boop.")
        # Activating game window
        window_active = self.activate_game_window()
        time.sleep(0.5)
        # If window was activated, find monster.
        if window_active:
            self.run_mob_killer()

    def run_mob_killer(self):
        # TODO: Set better way to limit monster kill limit
        for _ in range(2):
            coords = self.find_monster()
            if coords:
                # Get time to run to the target
                distance = self.calc_dist_to_monster(coords)
                # Run to the target
                self.run_towards_target(distance)
                # Attack target
                self.attack_target()


    def calc_dist_to_monster(self, coords):
        """ Calculates the distance between the player and the monster. """

        x_diff = abs(coords[0] - MINIMAP_CENTER[0])
        y_diff = abs(coords[1] - MINIMAP_CENTER[1])
        # Selecting maximum difference of the two
        if x_diff >= y_diff:
            # Calculating time to run to the target
            return x_diff / RUN_SPEED
        else:
            return y_diff / RUN_SPEED
      

    def run_towards_target(self, distance):
        """ Runs towards the target for a given distance (which is time) """
        logger.info("Running for " + str(distance) + " seconds.")
        # TODO: Make sure camera is in target mode (by pressing X)
        # Run towards target
        pg.mouseDown(button='left')
        pg.mouseDown(button='right')
        time.sleep(distance)
        pg.mouseUp(button='left')
        pg.mouseUp(button='right')


    def find_monster(self):
        """ Finds a monster from the minimap and turns towards it. """
        try:
            monster = pg.locateOnScreen('images/monster-red-dot.png', confidence=0.9, region=MINIMAP_REGION)
            if monster:
                logger.info("Monster found.")
                # Finding the centered location of the monster
                x, y = pg.center(monster)
                # Move mouse to monster in the minimap
                pg.moveTo(x, y, 0.2)
                # Click monster to target it
                pg.click()
                time.sleep(0.5)
                # Returning monster coordinates
                return (x, y)
            else:
                logger.warning("Monster not found.")
                return None
        except Exception as exc:
            logger.error(exc)
            return None


    def attack_target(self):
        """ Attacks targeted enemy. """
        # BIG TODO: Attack until enemy has died instead of attacking static amount of times.
        max_attacks = 8
        for _ in range(max_attacks):
            pd.press('1')
            time.sleep(1)

if __name__ == "__main__":
    # Creating instance of the bot
    bot = Bot()
    # Running bot main function
    bot.run()