import logging
from datetime import datetime
import base64
from base64 import b64encode
from pathlib import Path

import aiohttp
from M2Crypto import RSA, X509

from aiompesa.utils import is_url, saf_number_fmt

logger = logging.getLogger(__name__)


class Mpesa:
    SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"
    PRODUCTION_BASE_URL = "https://api.safaricom.co.ke"
    GENERATE_TOKEN_PATH = "/oauth/v1/generate?grant_type=client_credentials"
    REGISTER_URL_PATH = "/mpesa/c2b/v1/registerurl"
    C2B_URL_PATH = "/mpesa/c2b/v1/simulate"
    B2C_URL_PATH = "/mpesa/b2c/v1/paymentrequest"
    B2B_URL_PATH = "/mpesa/b2b/v1/paymentrequest"
    STK_URL_PATH = "/mpesa/stkpush/v1/processrequest"

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

    async def get_headers(self) -> dict:
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
        """Simulate making payments from client to Safaricom API."""
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
        headers = await self.get_headers()

        async with aiohttp.ClientSession(headers=headers) as session:
            return await self.post(session=session, url=url, data=data)

    @staticmethod
    def generate_security_credential(
        cert_location: str, initiator_password: str
    ) -> str:
        """Encode into base64 string the initiator password with M-Pesa’s
        public key and a X509 certificate."""
        cert_path = Path(cert_location)
        if cert_path.is_file() and cert_path.exists():
            with cert_path.open(mode="rt") as f:
                cert_data = f.read()

            cert = X509.load_cert_string(cert_data)
            pub_key = cert.get_pubkey()
            rsa_key = pub_key.get_rsa()
            cipher = rsa_key.public_encrypt(
                initiator_password.encode(), RSA.pkcs1_padding
            )
            return b64encode(cipher)
        else:
            raise FileNotFoundError(cert_location)

    async def b2c(
        self,
        initiator_name: str = None,
        security_credential: str = None,
        command_id: str = None,
        amount: int = None,
        party_a: str = None,
        party_b: str = None,
        remarks: str = None,
        queue_timeout_url: str = None,
        result_url: str = None,
        occassion: str = "",
    ) -> dict:
        """Make a payment from MPESA to a client."""
        url = f"{self.base_url}{self.B2C_URL_PATH}"
        phone_number, valid = saf_number_fmt(party_b)
        if not valid:
            raise ValueError(f"{party_b} is not a valid Safaricom number")
        if command_id not in [
            "SalaryPayment",
            "BusinessPayment",
            "PromotionPayment",
        ]:
            raise ValueError(f"{command_id} is not a valid CommandID value")
        data = {
            "InitiatorName": initiator_name,
            "SecurityCredential": security_credential,
            "CommandID": command_id,
            "Amount": f"{amount}",
            "PartyA": party_a,
            "PartyB": phone_number,
            "Remarks": remarks,
            "QueueTimeOutURL": queue_timeout_url,
            "ResultURL": result_url,
            "Occassion": occassion,
        }
        headers = await self.get_headers()

        async with aiohttp.ClientSession(headers=headers) as session:
            return await self.post(session=session, url=url, data=data)

    async def b2b(
        self,
        initiator_name: str = None,
        security_credential: str = None,
        command_id: str = None,
        amount: int = None,
        party_a: str = None,
        party_b: str = None,
        remarks: str = None,
        queue_timeout_url: str = None,
        result_url: str = None,
    ) -> dict:
        """Make a payment from one organization to another."""
        url = f"{self.base_url}{self.B2B_URL_PATH}"
        if command_id not in [
            "BusinessPayBill",
            "BusinessBuyGoods",
            "DisburseFundsToBusiness",
            "BusinessToBusinessTransfer",
            "MerchantToMerchantTransfer.",
        ]:
            raise ValueError(
                f"{command_id} is not a valid CommandID value for b2b request"
            )

        data = {
            "Initiator": initiator_name,
            "SecurityCredential": security_credential,
            "CommandID": command_id,
            "SenderIdentifierType": "4",
            "RecieverIdentifierType": "4",
            "Amount": f"{amount}",
            "PartyA": party_a,
            "PartyB": party_b,
            "Remarks": remarks,
            "QueueTimeOutURL": queue_timeout_url,
            "ResultURL": result_url,
        }
        headers = await self.get_headers()

        async with aiohttp.ClientSession(headers=headers) as session:
            return await self.post(session=session, url=url, data=data)

    @staticmethod
    def generate_password(short_code, lipa_na_mpesa_passkey) -> str:
        """Generate a Base64-encoded value of the concatenation of
        the Shortcode + LNM Passkey + Timestamp"""
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M%S")
        password = f"{short_code}{lipa_na_mpesa_passkey}{timestamp}"
        password = base64.b64encode(password.encode()).decode()
        return password, timestamp

    async def stk_push(
        self,
        lipa_na_mpesa_shortcode: str = None,
        lipa_na_mpesa_passkey: str = None,
        amount: int = None,
        party_a: str = None,
        party_b: str = None,
        callback_url: str = None,
        transaction_desc: str = None,
        transaction_type: str = "CustomerPayBillOnline",
    ) -> dict:
        """Make and STK push."""
        url = f"{self.base_url}{self.STK_URL_PATH}"
        number, valid = saf_number_fmt(party_a)
        if not valid:
            raise ValueError(f"{party_a} is not a valid Safaricom number")

        password, timestamp = Mpesa.generate_password(
            lipa_na_mpesa_shortcode, lipa_na_mpesa_passkey
        )
        data = {
            "BusinessShortCode": lipa_na_mpesa_shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": transaction_type,
            "Amount": f"{amount}",
            "PartyA": number,
            "PartyB": lipa_na_mpesa_shortcode,
            "PhoneNumber": number,
            "CallBackURL": callback_url,
            "AccountReference": number,
            "TransactionDesc": transaction_desc,
        }
        headers = await self.get_headers()

        async with aiohttp.ClientSession(headers=headers) as session:
            return await self.post(session=session, url=url, data=data)
