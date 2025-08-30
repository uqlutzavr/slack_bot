import logging
from config import SlackBotConfig
import requests
import os

logger = logging.getLogger(__name__)


class AsteriskVOIP:

    def __init__(self):
        self.config = SlackBotConfig()
        self.server_ip = self.config.server_ip
        self.username = self.config.ari_username
        self.password = self.config.ari_password
        self.target_1 = self.config.target_sip_1
        self.target_2 = self.config.target_sip_2

    def quick_call(self) -> bool:
        try:
            target_list = [self.target_1, self.target_2]
            for target in target_list:
                r = requests.post(
                    f"http://{self.server_ip}:8088/ari/channels",
                    params={"endpoint": f"{target}", "app": "quick-call"},
                    auth=(self.username, self.password),
                    timeout=60
                )
                if r.status_code == 200:
                    channel_id = r.json()['id']
                    logger.info(f"Successfully called - {channel_id}")
                else:
                    logger.error(f"Error: {r.status_code}")
        except Exception as e:
            logger.error(f"Error: {e}")
        return False

