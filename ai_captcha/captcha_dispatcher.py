import time
from engine.reporting.captcha_stats import CaptchaStatsManager
from .capsolver_api import CapsolverAPI
from .twocaptcha_api import TwoCaptchaAPI
from .anticaptcha_api import AntiCaptchaAPI

TYPE_6CHAR = "6char_alphanum"
TYPE_TEXT = "text_variable"
TYPE_MATH = "math_captcha"
TYPE_IMG_SELECT = "image_select"
TYPE_AUDIO = "audio_captcha"
TYPE_RECAPTCHA = "recaptcha_v2"
TYPE_HCAPTCHA = "hcaptcha"
TYPE_AUTO = "auto"

class CaptchaDispatcher:
    def __init__(self, service="capsolver", api_key=""):
        self.service = service
        self.api_key = api_key

        if service == "capsolver":
            self.api = CapsolverAPI(api_key)
        elif service == "2captcha":
            self.api = TwoCaptchaAPI(api_key)
        elif service == "anticaptcha":
            self.api = AntiCaptchaAPI(api_key)
        else:
            self.api = None

    def solve(self, task_type, **kwargs):
        if not self.api:
            return None

        start_time = time.time()
        success = False
        try:
            result = self.api.solve(task_type, **kwargs)
            success = bool(result)
            return result
        finally:
            duration = time.time() - start_time
            stats_manager = CaptchaStatsManager()
            stats_manager.record_attempt(self.service, success, duration)


def get_dispatcher(service="capsolver", api_key=""):
    return CaptchaDispatcher(service, api_key)
