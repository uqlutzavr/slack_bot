import logging
from requests.auth import HTTPBasicAuth
import requests

logger = logging.getLogger(__name__)


class TwilioVOIP:

    def __init__(self, config):
        self.config = config

    def call_twilio(self):
        try:
            for sip in self.config.twilio_sip_list:
                twilio_sid = self.config.twilio_account_sid
                twilio_token = self.config.twilio_account_token
                twilio_number = self.config.twilio_number
                twilio_sip = sip
                logger.info(f"Calling - {sip}")
                url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Calls.json"

                data = {
                    "From": twilio_number,
                    "To": twilio_sip,
                    "Url": "http://demo.twilio.com/docs/voice.xml",
                    "Timeout": "60"
                }

                response = requests.post(
                    url,
                    auth=HTTPBasicAuth(twilio_sid, twilio_token),
                    data=data,
                    timeout=10
                )

                if response.status_code == 201:
                    call_sid = response.json().get('sid')
                    logger.info(f"Call started. SID: {call_sid}, {sip}")
                    logger.info(f"Response: {response.json()}")
                else:
                    logger.error(f"Twilio error: {response.status_code} - {response.text}")

        except Exception as e:
            logger.error(f"Error in twilio calling - {e}")

