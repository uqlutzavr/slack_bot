import logging
from slack_sdk.errors import SlackApiError

from text_messages import ru_text, eng_text

logger = logging.getLogger(__name__)


class CommandHandler:
    def __init__(self, payload, webclient, config):
        self.payload = payload
        self.webclient = webclient
        self.config = config
        self.user_id = self.payload.get("user_id")
        self.payload_channel_id = self.payload.get("channel_id")
        self.user_name = self.payload.get("user_name")
        self.text = self.payload.get("text")
        self.config_old_api_channel_ids = self.config.old_api_chat_ids
        self.config_new_api_channel_ids = self.config.new_api_chat_ids
        self.target_channel = self.config.target_channel

    def forward_command(self):
        command_map = {
            "/rocket": self.rocket,
            "/old_api_close_reception": self.old_api_close_reception,
            "/new_api_close_reception": self.new_api_close_reception,
        }
        action = command_map.get(self.payload["command"])
        action()

    def log_action_in_target_channel(self, response):
        r = self.webclient.chat_postMessage(
            channel=self.target_channel,
            text=response
        )

    def rocket(self):
        try:
            response = self.webclient.chat_postMessage(
                channel=self.payload_channel_id,
                text=f"HELLO, <@{self.user_id}>!"
            )
        except SlackApiError as e:
            logger.error(f"Error on response: {e.response['error']}")

    def old_api_close_reception(self):
        try:
            if self.text == self.config.admin_password:
                for channel, language in self.config_old_api_channel_ids.items():
                    message = ru_text.technical_problems_close_reception if language == "RU" else eng_text.technical_problems_close_reception
                    try:
                        response = self.webclient.chat_postMessage(
                            channel=channel,
                            text=message
                        )
                    except SlackApiError as e:
                        logger.error(f"Failed to send message to {channel}: {e.response['error']}")
                self.log_action_in_target_channel(
                    f"{self.user_name} sent command {self.old_api_close_reception.__name__}")
                logger.info(f"{self.user_name} sent command {self.old_api_close_reception.__name__}")
            else:
                logger.info(f"Wrong password for command {self.old_api_close_reception.__name__} from {self.user_id}")
        except SlackApiError as e:
            logger.error(f"Error on responses: {e.response['error']}")

    def new_api_close_reception(self):
        try:
            if self.text == self.config.admin_password:
                for channel, language in self.config_old_api_channel_ids.items():
                    message = ru_text.technical_problems_close_reception if language == "RU" else eng_text.technical_problems_close_reception
                    try:
                        response = self.webclient.chat_postMessage(
                            channel=channel,
                            text=message
                        )
                    except SlackApiError as e:
                        logger.error(f"Failed to send message to {channel}: {e.response['error']}")
                self.log_action_in_target_channel(
                    f"{self.user_name} sent command {self.new_api_close_reception.__name__}")
                logger.info(f"{self.user_name} sent command {self.new_api_close_reception.__name__}")
            else:
                logger.info(
                    f"Wrong password for command {self.new_api_close_reception.__name__} from {self.user_id}")
        except SlackApiError as e:
            logger.error(f"Error on responses: {e.response['error']}")
