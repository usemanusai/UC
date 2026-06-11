import random
import time
import math
import logging
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)

class HumanJitter:
    """
    Implements advanced behavioral mimicry using chaotic Bézier curves,
    neuromuscular velocity profiling, micro-tremors, and overlapping keyboard inputs.
    Adapts to Linguistics Chameleon AI Personas dynamically.
    """
    current_persona = {
        "type": "systematic_researcher",
        "wpm": 60,
        "hesitation": 0.05,
        "curve_offset": 50,
        "scroll_aggressiveness": 0.3
    }
    
    # Mapping table to translate shifted/complex keys into base key + shift key sequences
    SHIFT_MAP = {
        '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
        '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
        '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\',
        ':': ';', '"': "'", '<': ',', '>': '.', '?': '/'
    }
    
    @classmethod
    def set_persona(cls, persona_data: Dict):
        """Applies a new AI-generated persona to the session's behavioral signature."""
        cls.current_persona.update(persona_data)
        logger.info(f"[Jitter] Persona updated: {cls.current_persona['type']}")

    @staticmethod
    def bezier_curve(p0: Tuple[int, int], p1: Tuple[int, int], p2: Tuple[int, int], p3: Tuple[int, int], steps: int = 20) -> List[Tuple[int, int]]:
        """Generates a standard cubic Bézier curve path (legacy compatibility)."""
        return HumanJitter.bezier_curve_with_easing(p0, p1, p2, p3, steps, easing_fn=lambda u: u)

    @staticmethod
    def bezier_curve_with_easing(p0: Tuple[float, float], p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float], steps: int = 20, easing_fn=None) -> List[Tuple[int, int]]:
        """
        Generates a cubic Bézier curve path using an easing function for Fitts's Law velocity pacing.
        """
        if easing_fn is None:
            # Default to inverted sine ease-out to mimic neuromuscular deceleration at target
            easing_fn = lambda u: math.sin(u * math.pi / 2)
            
        path = []
        for i in range(steps + 1):
            u = i / steps
            t = easing_fn(u)
            x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
            y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
            path.append((int(x), int(y)))
        return path

    @staticmethod
    def move_mouse_stealth(target_x: int, target_y: int):
        """
        Moves the mouse to the target coordinates using a dynamically perturbed
        Cubic Bézier curve (consistently single-sided) with micro-jitter and Fitts easing.
        Overshoots and corrects on longer trajectories.
        """
        import pyautogui
        start_x, start_y = pyautogui.position()
        
        dx = target_x - start_x
        dy = target_y - start_y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist < 5:
            # Just slide directly if extremely close
            pyautogui.moveTo(target_x, target_y)
            return
            
        # Extract parameters from the active persona
        offset = HumanJitter.current_persona.get("curve_offset", 100)
        
        # Calculate normal vector to ensure CP1 and CP2 lie on the same side (no S curves)
        ux = dx / dist
        uy = dy / dist
        nx = -uy
        ny = ux
        
        side = random.choice([1, -1])
        offset_magnitude = random.uniform(0.1, 0.3) * dist + random.uniform(0.1, 0.5) * offset
        
        # Generate base control points
        cp1_x = start_x + dx / 3.0 + side * nx * offset_magnitude
        cp1_y = start_y + dy / 3.0 + side * ny * offset_magnitude
        cp2_x = start_x + 2.0 * dx / 3.0 + side * nx * offset_magnitude
        cp2_y = start_y + 2.0 * dy / 3.0 + side * ny * offset_magnitude
        
        # Add ~5% random coordinate perturbation (variability)
        perturbation = 0.05 * dist
        cp1 = (cp1_x + random.uniform(-perturbation, perturbation), cp1_y + random.uniform(-perturbation, perturbation))
        cp2 = (cp2_x + random.uniform(-perturbation, perturbation), cp2_y + random.uniform(-perturbation, perturbation))
        
        # Adjust steps by persona speed/behavior
        base_steps = 15 if offset > 100 else 30
        steps = random.randint(base_steps - 5, base_steps + 5)
        
        # Easing curve matching acceleration then Fitts's deceleration
        fitts_easing = lambda u: math.sin(u * math.pi / 2)
        
        # Overshoot and Correct logic for longer movements (>150px)
        if dist > 150:
            overshoot_pct = random.uniform(0.02, 0.04)
            overshoot_x = target_x + dx * overshoot_pct
            overshoot_y = target_y + dy * overshoot_pct
            
            # 1. Main movement curve to overshoot destination
            main_path = HumanJitter.bezier_curve_with_easing(
                (start_x, start_y), cp1, cp2, (overshoot_x, overshoot_y), steps=steps, easing_fn=fitts_easing
            )
            
            # 2. Small correction arc returning back to actual target
            corr_steps = random.randint(4, 7)
            corr_dx = target_x - overshoot_x
            corr_dy = target_y - overshoot_y
            corr_dist = math.sqrt(corr_dx**2 + corr_dy**2)
            corr_nx = -corr_dy / (corr_dist or 1)
            corr_ny = corr_dx / (corr_dist or 1)
            corr_offset = random.uniform(3.0, 6.0)
            
            corr_cp1 = (overshoot_x + corr_dx / 3.0 + side * corr_nx * corr_offset,
                        overshoot_y + corr_dy / 3.0 + side * corr_ny * corr_offset)
            corr_cp2 = (overshoot_x + 2.0 * corr_dx / 3.0 + side * corr_nx * corr_offset,
                        overshoot_y + 2.0 * corr_dy / 3.0 + side * corr_ny * corr_offset)
            
            correction_path = HumanJitter.bezier_curve_with_easing(
                (overshoot_x, overshoot_y), corr_cp1, corr_cp2, (target_x, target_y), steps=corr_steps, easing_fn=lambda u: u
            )
            path = main_path[:-1] + correction_path
        else:
            path = HumanJitter.bezier_curve_with_easing(
                (start_x, start_y), cp1, cp2, (target_x, target_y), steps=steps, easing_fn=fitts_easing
            )
            
        # Introduce micro-jitter tremors (random ±2.5px offsets on intermediate points)
        final_path = []
        for idx, (x, y) in enumerate(path):
            if idx == 0 or idx == len(path) - 1:
                final_path.append((x, y)) # Lock start and destination points
            else:
                x_jit = x + random.uniform(-2.5, 2.5)
                y_jit = y + random.uniform(-2.5, 2.5)
                final_path.append((int(x_jit), int(y_jit)))
                
        # Move mouse with random delays (10ms to 60ms) between steps
        for x, y in final_path:
            pyautogui.moveTo(x, y)
            time.sleep(random.uniform(0.010, 0.060))
            
        logger.info(f"[Jitter] Moved mouse ({HumanJitter.current_persona['type']} style) to ({target_x}, {target_y}).")

    @staticmethod
    def human_typing(text: str, element=None):
        """
        Types text with realistic inter-character delays (WPM simulation based on persona).
        Supports asynchronous timing and Press/Release overlap when headed.
        """
        base_wpm = HumanJitter.current_persona.get("wpm", 50)
        wpm = random.randint(base_wpm - 10, base_wpm + 10)
        chars_per_sec = (wpm * 5) / 60
        base_delay = 1.0 / chars_per_sec
        hesitation = HumanJitter.current_persona.get("hesitation", 0.1)
        
        is_headless = False
        if element:
            try:
                element.click()
            except Exception:
                pass
            try:
                driver = element.parent
                is_headless = driver.capabilities.get('headless', False) or 'headless' in str(driver.capabilities)
            except Exception:
                pass
                
        # Headless mode fallback typing
        if is_headless and element:
            for char in text:
                delay = base_delay * random.uniform(0.5, 2.5)
                if char.isupper() or char in "!@#$%^&*()_+{}|:\"<>?":
                    delay += random.uniform(0.1, 0.2)
                    
                if random.random() < hesitation:
                    time.sleep(random.uniform(0.2, 0.5))
                    
                element.send_keys(char)
                time.sleep(delay)
            logger.info(f"[Jitter] Completed headless typing session (WPM: {wpm})")
            return

        # Native headed mode: type with press/release overlap and asynchronous timing profiles
        import pyautogui
        events = []
        current_time = 0.0
        
        for i, char in enumerate(text):
            # Normalize common whitespaces to keyboard key names
            mapped_char = char
            if char == '\n':
                mapped_char = 'enter'
            elif char == '\t':
                mapped_char = 'tab'
                
            # Asynchronous key complexity delay profile
            char_delay = base_delay * random.uniform(0.5, 2.0)
            if char.isupper() or char in "!@#$%^&*()_+{}|:\"<>?":
                char_delay += random.uniform(0.1, 0.2)
                
            if random.random() < hesitation:
                char_delay += random.uniform(0.2, 0.5)
                
            press_time = current_time + char_delay
            hold_duration = random.uniform(0.05, 0.15)
            release_time = press_time + hold_duration
            
            # Map key overlaps using virtual events
            if mapped_char.islower() or mapped_char.isdigit() or mapped_char in " \t\n-= []\\;',./" or mapped_char in ['enter', 'tab']:
                events.append((press_time, 'down', mapped_char))
                events.append((release_time, 'up', mapped_char))
            elif mapped_char.isupper():
                lower = mapped_char.lower()
                events.append((press_time - 0.02, 'down', 'shift'))
                events.append((press_time, 'down', lower))
                events.append((release_time, 'up', lower))
                events.append((release_time + 0.02, 'up', 'shift'))
            elif mapped_char in HumanJitter.SHIFT_MAP:
                base = HumanJitter.SHIFT_MAP[mapped_char]
                events.append((press_time - 0.02, 'down', 'shift'))
                events.append((press_time, 'down', base))
                events.append((release_time, 'up', base))
                events.append((release_time + 0.02, 'up', 'shift'))
            else:
                events.append((press_time, 'press', mapped_char))
                
            # Random overlap schedule for natural typing cadence
            if i < len(text) - 1:
                if random.random() < 0.35: # 35% chance of key overlap
                    overlap_duration = random.uniform(0.01, 0.05)
                    current_time = release_time - overlap_duration
                else:
                    current_time = release_time + random.uniform(0.02, 0.08)
                    
        # Sort and run the scheduled events sequentially
        events.sort(key=lambda x: x[0])
        
        last_time = 0.0
        for event_time, action, key in events:
            sleep_time = event_time - last_time
            if sleep_time > 0:
                time.sleep(sleep_time)
            last_time = event_time
            
            try:
                if action == 'down':
                    pyautogui.keyDown(key)
                elif action == 'up':
                    pyautogui.keyUp(key)
                else:
                    pyautogui.write(key)
            except Exception:
                try:
                    pyautogui.write(key)
                except Exception:
                    pass
                    
        logger.info(f"[Jitter] Completed physical/headed typing session (WPM: {wpm})")

    @staticmethod
    def random_scroll(browser):
        """
        Performs non-linear scrolling based on scroll aggressiveness.
        """
        agg = HumanJitter.current_persona.get("scroll_aggressiveness", 0.5)
        scroll_amount = random.randint(300, int(300 * (1.0 + agg * 2)))
        direction = 1 if random.random() > 0.2 else -1
        
        steps = random.randint(3 if agg > 0.6 else 8, 15)
        for _ in range(steps):
            browser.execute_script(f"window.scrollBy(0, {direction * (scroll_amount // steps)});")
            time.sleep(random.uniform(0.05, 0.3) if agg > 0.6 else random.uniform(0.2, 0.5))
            
        logger.info(f"[Jitter] Performed scroll: {scroll_amount}px in {steps} steps")

