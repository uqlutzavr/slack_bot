import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import datetime
import json

load_dotenv()


def debug_mode_to_bool():
    debug_mode = os.getenv("DEBUG_MODE").capitalize()
    return True if debug_mode == "True" else False


def setup_logging():
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(log_directory, f"slack_bot_{time}.log")

    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )

    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    debug_mode = debug_mode_to_bool()
    if debug_mode:
        root_logger.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)
    return root_logger


logger = setup_logging()


def clean_json_string(value: str):
    return value.strip().strip("'").strip('"')


class SlackBotConfig:
    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.app_token = os.getenv("SLACK_APP_TOKEN")
        self.target_channel = os.getenv("TARGET_CHANNEL")
        self.tag = os.getenv("TARGET_TAG")
        self.admin_password = os.getenv("ADMIN_PW", "password")
        self.debug_mode = debug_mode_to_bool()
        self.commands = ["/rocket", "/old_api_close_reception", "/new_api_close_reception"]
        self.new_api_chat_ids = json.loads(clean_json_string(os.getenv("NEW_API_CHAT_IDS", "{}")))
        self.old_api_chat_ids = json.loads(clean_json_string(os.getenv("OLD_API_CHAT_IDS", "{}")))
        self.server_ip = os.getenv("ASTERISK_HOST")
        self.ari_username = os.getenv("ARI_USERNAME")
        self.ari_password = os.getenv("ARI_PASSWORD")
        self.target_sip_1 = os.getenv("TARGET_SIP1")
        self.target_sip_2 = os.getenv("TARGET_SIP2")
        self.vip_channels = os.getenv("VIP_CHANNELS")
        self.twilio_channel = os.getenv("TWILIO_CHANNEL")
        self.twilio_bot = os.getenv("TWILIO_BOT")
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_account_token = os.getenv("TWILIO_ACCOUNT_TOKEN")
        self.twilio_number = os.getenv("TWILIO_NUMBER")
        self.twilio_sip = os.getenv("TWILIO_SIP")
        self.twilio_sip_list = [s.strip() for s in self.twilio_sip.split(',')] if self.twilio_sip else []

        logger.info(f"Twilio accounts to call - {self.twilio_sip_list}")

        logger.debug(f"SLACK_BOT_TOKEN: {'set' if self.bot_token else 'not set'}")
        logger.debug(f"SLACK_APP_TOKEN: {'set' if self.app_token else 'not set'}")
        logger.debug(f"TARGET_CHANNEL: {'set' if self.target_channel else 'not set'}")
        logger.debug(f"TARGET_TAG: {'set' if self.tag else 'not set'}")
        logger.debug(f"ADMIN_PW: {'set' if self.admin_password else 'not set'}")

        if not all([self.bot_token, self.app_token, self.target_channel, self.tag, self.admin_password]):
            logger.error("Missing required environment variables")
            raise ValueError("SLACK_BOT_TOKEN, SLACK_APP_TOKEN, ADMIN_PW, TARGET_TAG and TARGET_CHANNEL must be set")
