import aiohttp
import logging
from aiompesa.utils import is_url, saf_number_fmt

logger = logging.getLogger(__name__)


class Mpesa:
    SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"
    PRODUCTION_BASE_URL = "https://api.safaricom.co.ke"
    GENERATE_TOKEN_PATH = "/oauth/v1/generate?grant_type=client_credentials"
    REGISTER_URL_PATH = "/mpesa/c2b/v1/registerurl"
    C2B_URL_PATH = "/mpesa/c2b/v1/simulate"

    def __init__(
        self,
        sandbox: bool = True,
        consumer_key: str = None,
        consumer_secret: str = None,
    ):
        if sandbox:
            self.base_url = self.SANDBOX_BASE_URL
        else:
            self.base_url = self.PRODUCTION_BASE_URL
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    @staticmethod
    async def get(session: aiohttp.ClientSession, url: str) -> dict:
        async with session.get(url) as response:
            try:
                return await response.json()
            except Exception as e:
                logger.debug(e)
                response_txt = await response.text()
                if response_txt:
                    return response_txt
                return {
                    "error": "Wrong credentials",
                    "status": response.status,
                }

    @staticmethod
    async def post(
        session: aiohttp.ClientSession, url: str, data: dict
    ) -> dict:
        async with session.post(url, json=data) as response:
            try:
                return await response.json()
            except Exception as e:
                logger.debug(e)
                response_txt = await response.text()
                if response_txt:
                    return response_txt
                return {"error": f"{e}", "status": response.status}

    async def generate_token(self) -> dict:
        url = f"{self.base_url}{self.GENERATE_TOKEN_PATH}"
        auth = aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
        async with aiohttp.ClientSession(auth=auth) as session:
            response = await self.get(session, url)
            error = response.get("error", None)
            if error is not None:
                return {"access_token": None, "expires_in": None}
            return response

    async def get_headers(self):
        """Get the headers for an MPESA request."""
        headers = {
            "Host": f"{self.base_url[8:]}",
            "Content-Type": "application/json",
        }
        token = await self.generate_token()
        access_token = token.get("access_token", None)
        if access_token is None:
            raise ValueError("Invalid access token value")
        headers["Authorization"] = f"Bearer {access_token}"

        return headers

    async def register_url(
        self,
        response_type: str,
        shortcode: str,
        confirmation_url: str,
        validation_url: str,
    ) -> dict:
        if response_type not in ["Cancelled", "Completed"]:
            raise ValueError(
                f"{response_type} is not a valid ResponseType value"
            )
        if not is_url(confirmation_url):
            raise ValueError(f"{confirmation_url} is not a valid url value")
        if not is_url(validation_url):
            raise ValueError(f"{validation_url} is not a valid url value")

        headers = await self.get_headers()
        url = f"{self.base_url}{self.REGISTER_URL_PATH}"
        data = {
            "ShortCode": shortcode,
            "ResponseType": response_type,
            "ConfirmationURL": confirmation_url,
            "ValidationURL": validation_url,
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            return await self.post(session=session, url=url, data=data)

    async def c2b(
        self,
        shortcode: str = None,
        amount: int = None,
        phone_number: str = None,
    ) -> dict:
        """Make payments from clients to Safaricom API."""
        url = f"{self.base_url}{self.C2B_URL_PATH}"
        number, valid = saf_number_fmt(phone_number)
        if not valid:
            raise ValueError(f"{phone_number} is not a valid Safaricom number")

        data = {
            "ShortCode": shortcode,
            "CommandID": "CustomerPayBillOnline",
            "Amount": f"{amount}",
            "Msisdn": number,
            "BillRefNumber": number,
        }
        print(data)
        headers = await self.get_headers()

        async with aiohttp.ClientSession(headers=headers) as session:
            return await self.post(session=session, url=url, data=data)
