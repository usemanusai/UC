import random
import time
import math
import logging
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)

class HumanJitter:
    """
    Implements behavioral mimicry using Bézier curves and non-linear interactions.
    Adapts to Linguistics Chameleon AI Personas dynamically.
    """
    current_persona = {
        "type": "systematic_researcher",
        "wpm": 60,
        "hesitation": 0.05,
        "curve_offset": 50,
        "scroll_aggressiveness": 0.3
    }
    
    @classmethod
    def set_persona(cls, persona_data: Dict):
        """Applies a new AI-generated persona to the session's behavioral signature."""
        cls.current_persona.update(persona_data)
        logger.info(f"[Jitter] Persona updated: {cls.current_persona['type']}")

    @staticmethod
    def bezier_curve(p0: Tuple[int, int], p1: Tuple[int, int], p2: Tuple[int, int], p3: Tuple[int, int], steps: int = 20) -> List[Tuple[int, int]]:
        """
        Generates a cubic Bézier curve path.
        """
        path = []
        for i in range(steps + 1):
            t = i / steps
            x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
            y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
            path.append((int(x), int(y)))
        return path

    @staticmethod
    def move_mouse_stealth(target_x: int, target_y: int):
        """
        Moves the mouse to target using a Bézier curve with randomized control points based on cognitive load.
        """
        import pyautogui
        start_x, start_y = pyautogui.position()
        
        # Pull from chameleon persona
        offset = HumanJitter.current_persona.get("curve_offset", 100)
        
        cp1 = (start_x + random.randint(-offset, offset), start_y + random.randint(-offset, offset))
        cp2 = (target_x + random.randint(-offset, offset), target_y + random.randint(-offset, offset))
        
        # "Frustrated" users have fewer path steps (sharp movements), "Systematic" have more (smooth)
        base_steps = 15 if offset > 100 else 30
        path = HumanJitter.bezier_curve((start_x, start_y), cp1, cp2, (target_x, target_y), steps=random.randint(base_steps - 5, base_steps + 5))
        
        for x, y in path:
            pyautogui.moveTo(x, y)
            time.sleep(random.uniform(0.001, 0.005))
            
        logger.info(f"[Jitter] Moved mouse ({HumanJitter.current_persona['type']} style) to ({target_x}, {target_y}).")

    @staticmethod
    def human_typing(text: str, element=None):
        """
        Types text with realistic inter-character delays (WPM simulation based on persona).
        """
        base_wpm = HumanJitter.current_persona.get("wpm", 50)
        wpm = random.randint(base_wpm - 10, base_wpm + 10)
        chars_per_sec = (wpm * 5) / 60
        base_delay = 1.0 / chars_per_sec
        hesitation = HumanJitter.current_persona.get("hesitation", 0.1)
        
        for char in text:
            delay = base_delay * random.uniform(0.5, 2.5)
            if random.random() < hesitation: 
                time.sleep(random.uniform(0.2, 0.5))
            
            if element:
                element.send_keys(char)
            else:
                import pyautogui
                pyautogui.write(char)
            
            time.sleep(delay)
        
        logger.info(f"[Jitter] Completed typing session (WPM: {wpm})")

    @staticmethod
    def random_scroll(browser):
        """
        Performs non-linear scrolling based on scroll aggressiveness.
        """
        agg = HumanJitter.current_persona.get("scroll_aggressiveness", 0.5)
        # Aggressive personas scroll more px in fewer chunks
        scroll_amount = random.randint(300, int(300 * (1.0 + agg * 2)))
        direction = 1 if random.random() > 0.2 else -1
        
        steps = random.randint(3 if agg > 0.6 else 8, 15)
        for _ in range(steps):
            browser.execute_script(f"window.scrollBy(0, {direction * (scroll_amount // steps)});")
            time.sleep(random.uniform(0.05, 0.3) if agg > 0.6 else random.uniform(0.2, 0.5))
            
        logger.info(f"[Jitter] Performed scroll: {scroll_amount}px in {steps} steps")
