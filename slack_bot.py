import os
import time
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest

from voip import AsteriskVOIP
from voip_twilio import TwilioVOIP
from config import SlackBotConfig
from message_processor import MessageProcessor
from commands_handler import CommandHandler

logger = logging.getLogger(__name__)


class SlackBot:
    def __init__(self):
        self.config = SlackBotConfig()
        self.start_time = time.time()
        self.processed_messages = set()
        self.voip = AsteriskVOIP()
        try:
            self.web_client = WebClient(token=self.config.bot_token)
            logger.info("WebClient initialized")
        except Exception as e:
            logger.error(f"Error initializing WebClient: {e}")
            raise

        self.socket_client = SocketModeClient(
            app_token=self.config.app_token,
            web_client=self.web_client
        )
        self.processor = MessageProcessor(self.config)
        self.twilio_voip = TwilioVOIP(self.config)
        bot_info = self.get_bot_info()
        self.bot_user_id = bot_info['id']
        self.bot_id = bot_info.get('bot_id', '')

    def get_bot_info(self) -> dict:
        try:
            response = self.web_client.auth_test()
            bot_id = response['user_id']
            bot_name = response['user']
            bot_info = {'name': bot_name, 'id': bot_id, 'bot_id': response.get('bot_id', '')}
            logger.info(f"Bot: {bot_name} (User ID: {bot_id}, Bot ID: {bot_info['bot_id']})")
            return bot_info
        except SlackApiError as e:
            logger.error(f"Error getting bot info: {e.response['error']}")
            return {}

    def handle_message(self, client: SocketModeClient, req: SocketModeRequest):
        client.send_socket_mode_response({"envelope_id": req.envelope_id})
        if req.type == "events_api":
            logger.info(
                f"Request received: {req.type}, payload: {req.payload if self.config.debug_mode else 'DEBUG_MODE = FALSE'}")
            event = req.payload.get('event', {})
            logger.debug(f"Full event: {event}")
            event_type = event.get('type')
            subtype = event.get('subtype')
            channel = event.get('channel', 'unknown')
            user = event.get('user', 'unknown')
            bot_id = event.get('bot_id', 'unknown')
            ts = event.get('ts', '0')
            allowed_bot_channels = ['C02T9LSBB0W', 'C08U53E0ECD']

            if self.processor.is_dev_call(event, channel, bot_id):
                logger.info(f"Dev call detected for channel={channel}, bot_id={bot_id}")
                self.twilio_voip.call_twilio()
                self.voip.quick_call()

            if event_type != 'message':
                logger.info(f"Skipping event: event_type={event_type} is not 'message'")
                return

            if user == self.bot_user_id:
                logger.info(f"Skipping message from bot itself: user={user}")
                return

            if subtype == "bot_message" and channel not in allowed_bot_channels:
                logger.info(f"Skipping bot message from disallowed channel={channel}")
                return

            if subtype and subtype != "bot_message":
                logger.info(f"Skipping message with unsupported subtype={subtype}")
                return

            if ts in self.processed_messages:
                logger.info(f"Message with ts={ts} already processed, skipping")
                return

            try:
                message_ts = float(ts)
                if message_ts < self.start_time:
                    logger.info(f"Ignoring old message: ts={message_ts}, start_time={self.start_time}")
                    return
            except ValueError:
                logger.error(f"Invalid timestamp: {ts}")
                return

            text = event.get('text', '')
            if not text:
                logger.info("Message has no text, ignoring")
                return

            logger.info(f"Message in channel {channel} from user {user}: {text}")
            if self.processor.has_support_tag(text):
                logger.info(f"Support tag {self.config.tag} found in message: {text}")
                self.forward_message(event)
            if self.processor.is_tagged(text, self.bot_user_id):
                logger.info(f"Bot is tagged {self.config.tag} in message: {text}")
                self.forward_message(event)
            if self.processor.is_vip(channel):
                logger.info(f"Message from VIP channel {channel}: {text}")
                self.voip.quick_call()
            else:
                logger.debug("Cant handle the message")

    def handle_slash_commands(self, client: SocketModeClient, req: SocketModeRequest):
        if req.type == "slash_commands":
            client.send_socket_mode_response({"envelope_id": req.envelope_id})
            logger.info(
                f"Command received: {req.type} - {req.payload['command']}, payload: {req.payload if self.config.debug_mode else 'DEBUG_MODE = FALSE'}")
            logger.info("Here slash_commands")
            if req.payload["command"] in self.config.commands:
                handler = CommandHandler(req.payload, self.web_client, self.config)
                handler.forward_command()

    def forward_message(self, event: dict):
        logger.debug(f"Forwarding message: {event}")
        permalink = self.processor.get_message_link(event, self.web_client)
        if permalink:
            try:
                self.web_client.chat_postMessage(
                    channel=self.config.target_channel,
                    link_names=True,
                    mrkdwn=True,
                    text=f"@fls_group - You got a <{permalink}|message>",
                    unfurl_links=True
                )
                logger.info(f"Message forwarded to channel {self.config.target_channel}")
                self.voip.quick_call()
            except SlackApiError as e:
                logger.error(f"Error forwarding message: {e.response['error']}")

    def start(self):
        self.socket_client.socket_mode_request_listeners.append(self.handle_message)
        self.socket_client.socket_mode_request_listeners.append(self.handle_slash_commands)
        while True:
            try:
                logger.info("Starting SocketModeClient...")
                self.socket_client.connect()
                logger.info("SocketModeClient connected")
                while True:
                    time.sleep(60)
                    logger.info("Bot is running...")
            except Exception as e:
                logger.error(f"Error in SocketModeClient: {e}")
                logger.info("Reconnecting in 30 seconds...")
                time.sleep(30)
