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
    """The Mpesa interface that will interact with MPESA endpoints.

    Example:

    .. highlight:: python
    .. code-block:: python

        import asyncio
        from aiompesa import Mpesa

        CONSUMER_KEY = "nF4OwB2XiuYZwmdMz3bovnzw2qMls1b7"
        CONSUMER_SECRET = "biIImmaAX9dYD4Pw"

        loop = asyncio.get_event_loop()
        mpesa = Mpesa(True, CONSUMER_KEY, CONSUMER_SECRET)

        token_response = loop.run_until_complete(mpesa.generate_token())

        access_token = token_response.get("access_token", None)
        expires_in = token_response.get("expires_in", None)
        if access_token is None:
            print("Error: Wrong credentials used to get the access_token")
        else:
            print(f"access_token = {access_token}, expires_in = {expires_in} secs")
    """

    SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"
    PRODUCTION_BASE_URL = "https://api.safaricom.co.ke"
    GENERATE_TOKEN_PATH = "/oauth/v1/generate?grant_type=client_credentials"
    REGISTER_URL_PATH = "/mpesa/c2b/v1/registerurl"
    C2B_URL_PATH = "/mpesa/c2b/v1/simulate"
    B2C_URL_PATH = "/mpesa/b2c/v1/paymentrequest"
    B2B_URL_PATH = "/mpesa/b2b/v1/paymentrequest"
    STK_URL_PATH = "/mpesa/stkpush/v1/processrequest"
    REVERSAL_URL_PATH = "/mpesa/reversal/v1/request"

    def __init__(
        self,
        sandbox: bool = True,
        consumer_key: str = None,
        consumer_secret: str = None,
    ):
        """Initialize parameters. Access them here http://bit.ly/2JoWdZM.

        Parameters:
            sandbox: determines whether you are running in development or production.
            consumer_key: key required to make a request to the API.
            consumer_secret: secret required to make a request to the API.
        """
        if sandbox:
            self.base_url = self.SANDBOX_BASE_URL
        else:
            self.base_url = self.PRODUCTION_BASE_URL
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    @staticmethod
    async def get(session: aiohttp.ClientSession, url: str) -> dict:
        """Performs an async GET request to the URL provided.

        Args:
            session: An http session from `aiohttp`.
            url: A URL you want to make a GET request to.

        Returns:
            A dict mapping the response from the URL passed to their values.
        """
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
        """Performs an async POST request to the URL provided.

        Args:
            session: An http session from `aiohttp`
            url: A URL you want to make a request to
            data: The values you want to POST to the URL

        Returns:
            A dict mapping the response from the URL passed to their values.
        """
        async with session.post(url, json=data) as response:
            try:
                return await response.json()
            except Exception as e:
                logger.debug(e)
                response_txt = await response.text()
                if response_txt:
                    return response_txt
                return {"error": f"{e}", "status": response.status}

    @staticmethod
    def generate_security_credential(
        cert_location: str, initiator_password: str
    ) -> str:
        """Create a security credential.

        Encodes into base64 string the initiator password with M-Pesa’s
        public key and a X509 certificate.

        Args:
            cert_location: a file location of the production/sandbox X509
                certificate.
            initiator_password: the password of the person authorizing the
                requests

        Raises:
            FileNotFoundError: when the path of the certificate is not
                found on the system.

        Returns:
            A base64 value of the encoded password and file.
        """
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

    @staticmethod
    def generate_password(short_code, lipa_na_mpesa_passkey) -> tuple:
        """Generate an encoded password.

        Create a Base64-encoded value of the concatenation of the
        Shortcode + LNM Passkey + Timestamp.

        Args:
            short_code: a paybill number/till number, which you expect to receive
                payments notifications about.
            lipa_na_mpesa_passkey: a Lipa na Mpesa pass key.

        Returns:
            a tuple of two strings which are the password and the timestamp
        """
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M%S")
        password = f"{short_code}{lipa_na_mpesa_passkey}{timestamp}"
        password = base64.b64encode(password.encode()).decode()
        return password, timestamp

    async def generate_token(self) -> dict:
        """Generates an access token from the API.

        Returns:
            A dict with `access_token` that is a string value and `expires_in`
            that is also a string value

            {"access_token": "4UkKg50WyGADbzAZWW8iRtmTGwPw", "expires_in": "3599"}
        """
        url = f"{self.base_url}{self.GENERATE_TOKEN_PATH}"
        auth = aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
        async with aiohttp.ClientSession(auth=auth) as session:
            response = await self.get(session, url)
            error = response.get("error", None)
            if error is not None:
                return {"access_token": None, "expires_in": None}
            return response

    async def _get_headers(self) -> dict:
        """Assembles the headers for an MPESA request.

        Returns:
            A dict with the available headers for a request to the API.
        Raises:
            ValueError: when the `access_token` is invalid.
        """
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
        """Performs a registration of callback URLs to the API.

        Args:
            response_type: a default action value that determines what MPesa will
                do in the scenario that your endpoint is unreachable or is unable to
                respond on time. Can be Completed or Cancelled. Completed means
                MPesa will automatically complete your transaction, whereas
                Cancelled means MPesa will automatically cancel the transaction,
                in the event MPesa is unable to reach your Validation URL.
            shortcode: a paybill number/till number, which you expect to receive
                payments notifications about.
            confirmation_url: A callback URL which the API calls to with the details
                of the completed transaction.
            validation_url: A callback URL which the API calls to get a validation
                response for a transaction.

        Returns:
            A dict with the ResponseDescription value being "success". Any other value
            is a failed request.

            {
                "ConversationID": "",
                "OriginatorCoversationID": "",
                "ResponseDescription": "success"
            }
        Raises:
            ValueError: when the response_type is not Cancelled/Completed or when the
                validation_url and confirmation_url are not valid URLs.
        """
        if response_type not in ["Cancelled", "Completed"]:
            raise ValueError(
                f"{response_type} is not a valid ResponseType value"
            )
        if not is_url(confirmation_url):
            raise ValueError(f"{confirmation_url} is not a valid url value")
        if not is_url(validation_url):
            raise ValueError(f"{validation_url} is not a valid url value")

        headers = await self._get_headers()
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
        """Simulate making payments from client to Safaricom API.

        Args:
            shortcode: a paybill number/till number, which you expect to receive
                payments notifications about.
            amount: the amount in KSh you are sending to a businees.
            phone_number: a valid safaricom number you are sending money from.

        Returns:
            A dict with the ResponseDescription having a value as shown.

            {
                "ConversationID": "AG_20180324_000066530b914eee3f85",
                "OriginatorCoversationID": "25344-885903-1",
                "ResponseDescription": "Accept the service request successfully."
            }

            Any other value is a failed request.

        Raises:
            ValueError: when the phone_number supplied is not a valid phone number.
        """
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
        headers = await self._get_headers()

        async with aiohttp.ClientSession(headers=headers) as session:
            return await self.post(session=session, url=url, data=data)

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
        """Make a payment from MPESA to a client.

        Args:
            initiator_name: username of the API operator as assigned on the MPesa
                Org Portal.
            security_credential: password of the API operator encrypted using the
                public key certificate provided.
            command_id: specifies the type of transaction being performed. There
                are three allowed values on the API: SalaryPayment, BusinessPayment
                or PromotionPayment.
            amount: the amount being sent from a business to a client.
            party_a: the business shortcode.
            party_b: the client phone number.
            remarks: A very short description of the transaction from your end.
            queue_timeout_url: the callback URL used to send an error callback
                when the transaction was not able to be processed by MPesa within
                a stipulated time period.
            result_url: the callback URL where the results of the transaction will be
                sent.
            occassion: A very short description of the transaction from your end. Can
                be left blank.

        Returns:
            A dict with a ResponseCode value of 0:

            {
                "ConversationID": "AG_20180326_00005ca7f7c21d608166",
                "OriginatorConversationID": "12363-1328499-6",
                "ResponseCode": "0",
                "ResponseDescription": "Accept the service request successfully."
            }

            Any other returned value is a failed request.

        Raises:
            ValueError: when the party_b is not a valid Safaricom number or when
                command_id is not SalaryPayment, BusinessPayment or
                PromotionPayment.
        """
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
        headers = await self._get_headers()

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
        """Make a payment from one organization to another.

        Args:
            initiator_name: username of the API operator as assigned on the MPesa
                Org Portal.
            security_credential: password of the API operator encrypted using the
                public key certificate provided.
            command_id: specifies the type of transaction being performed. There
                are three allowed values on the API: BusinessPayBill, BusinessBuyGoods,
                DisburseFundsToBusiness, BusinessToBusinessTransfer or
                MerchantToMerchantTransfer.
            amount: the amount being sent from a business to a client.
            party_a: the organization sending the funds.
            party_b: the organization receiving the funds.
            remarks: A very short description of the transaction from your end.
            queue_timeout_url: the callback URL used to send an error callback
                when the transaction was not able to be processed by MPesa within
                a stipulated time period.
            result_url: the callback URL where the results of the transaction will be
                sent.
        Returns:
            A dict with a ResponseCode value of 0:

            {
                "ConversationID": "AG_20180326_00005ca7f7c21d608166",
                "OriginatorConversationID": "12363-1328499-6",
                "ResponseCode": "0",
                "ResponseDescription": "Accept the service request successfully."
            }

            Any other returned value is a failed request.

        Raises:
            ValueError: when the party_b is not a valid Safaricom number or when
                command_id is not BusinessPayBill, BusinessBuyGoods,
                DisburseFundsToBusiness, BusinessToBusinessTransfer or
                MerchantToMerchantTransfer.
        """
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
        headers = await self._get_headers()

        async with aiohttp.ClientSession(headers=headers) as session:
            return await self.post(session=session, url=url, data=data)

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
        """Make an STK push.

        Args:
            lipa_na_mpesa_shortcode: shortcode of the organization initiating the
                request and expecting the payment.
            lipa_na_mpesa_passkey: lipa na mpesa pass key.
            amount: amount being sent from client to business.
            party_a: debit party of the transaction, hereby the phone number of
                the customer.
            party_b: credit party of the transaction, hereby being the shortcode
                of the organization.
            callback_url: the endpoint where you want the results of the transaction
                delivered.
            transaction_desc: a short description of the transaction.
            transaction_type: specifies the type of transaction being performed.

        Raises:
            ValueError: when the party_b value is not a valid Safaricom number.

        Returns:
            a dict with the ResponseCode value as 0.

            {
                "MerchantRequestID": "25353-1377561-4",
                "CheckoutRequestID": "ws_CO_26032018185226297",
                "ResponseCode": "0",
                "ResponseDescription": "Success. Request accepted for processing",
                "CustomerMessage": "Success. Request accepted for processing"
            }

            Any other value is a failed request.
        """
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
        headers = await self._get_headers()

        async with aiohttp.ClientSession(headers=headers) as session:
            return await self.post(session=session, url=url, data=data)

    async def reversal(
        self,
        initiator: str = None,
        security_credential: str = None,
        transaction_id: str = None,
        amount: int = None,
        receiver_party: str = None,
        result_url: str = None,
        queue_timeout_url: str = None,
        remarks: str = None,
        occasion: str = None,
    ) -> dict:
        """Make a reversal of a transaction.

        Args:
            initiator: the username of the person authorizing the request.
            security_credential:
            transaction_id: the MPesa Transaction ID of the transaction which you
                wish to reverse.
            amount: the amount of the transaction being reversed.
            receiver_party: your organization short code.
            remarks: a very short description of the transaction from your end.
            queue_timeout_url: the callback URL used to send an error callback
                when the transaction was not able to be processed by MPesa within
                a stipulated time period.
            result_url: the callback URL where the results of the transaction will be
                sent.
            occassion: a very short description of the transaction from your end.
        """
        url = f"{self.base_url}{self.REVERSAL_URL_PATH}"
        data = {
            "Initiator": initiator,
            "SecurityCredential": security_credential,
            "CommandID": "TransactionReversal",
            "TransactionID": transaction_id,
            "Amount": f"{amount}",
            "ReceiverParty": receiver_party,
            "RecieverIdentifierType": "4",
            "ResultURL": result_url,
            "QueueTimeOutURL": queue_timeout_url,
            "Remarks": remarks,
            "Occasion": occasion,
        }
        headers = await self._get_headers()

        async with aiohttp.ClientSession(headers=headers) as session:
            return await self.post(session=session, url=url, data=data)
