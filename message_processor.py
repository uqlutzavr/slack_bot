import re
import logging
from typing import Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class MessageProcessor:
    def __init__(self, config):
        self.config = config

    def has_support_tag(self, text: str) -> bool:
        if not text:
            logger.debug("Message text is empty")
            return False
        regex = re.compile(rf'{re.escape(self.config.tag)}', re.IGNORECASE)
        result = bool(regex.search(text))
        logger.debug(f"Tag check in text '{text}': {'found' if result else 'not found'}")
        return result

    @staticmethod
    def is_tagged(text: str, bot_id: str) -> bool:
        if not text or not bot_id:
            logger.debug("Message text or bot_id is empty")
            return False
        result = bool(re.search(f'{bot_id}', text))
        logger.debug(f"Tag check in text '{text}': {'found' if result else 'not found'}")
        return result

    def is_vip(self, channel: str) -> bool:
        vip_channels = self.config.vip_channels
        vip_channels_list = vip_channels.split(',')
        if channel in vip_channels_list:
            return True
        return False

    def get_message_link(self, event: dict, client: WebClient) -> Optional[str]:
        try:
            channel = event.get('channel')
            ts = event.get('ts')
            logger.debug(f"Getting permalink for channel={channel}, ts={ts}")
            result = client.chat_getPermalink(channel=channel, message_ts=ts)
            logger.info(f"Retrieved permalink: {result['permalink']}")
            return result['permalink']
        except SlackApiError as e:
            logger.error(f"Error getting permalink: {e.response['error']}")
            return None
