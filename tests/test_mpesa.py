import asyncio
from unittest import mock

import pytest
from aioresponses import aioresponses
from asynctest import TestCase

import aiompesa

CONSUMER_KEY = "nF4OwB2XiuYZwmdMz3bovnzw2qMls1b7"
CONSUMER_SECRET = "biIImmaAX9dYD4Pw"


def AsyncMock(*args, **kwargs):
    """
    see: https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
    """
    m = mock.MagicMock(*args, **kwargs)

    async def mock_coro(*args, **kwargs):
        return m(*args, **kwargs)

    mock_coro.mock = m
    return mock_coro


class TestMpesa(TestCase):
    @staticmethod
    def _run(coro):
        """Helper function that runs any coroutine in an event loop and passes
        its return value back to the caller.
        https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def setUp(self):
        self.mpesa = aiompesa.Mpesa(
            consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET
        )
        self.prod_mpesa = aiompesa.Mpesa(
            sandbox=False,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
        )
        self.fake_mpesa = aiompesa.Mpesa(False, "fake_key", "fake_secret")

    def test_sandbox_setup(self):
        assert self.prod_mpesa.base_url == self.mpesa.PRODUCTION_BASE_URL
        assert self.mpesa.base_url == self.mpesa.SANDBOX_BASE_URL

    def test_get(self):
        url = "https://google.com/"
        session = AsyncMock(return_value=mock.Mock())
        self.mpesa.get = AsyncMock(return_value={"success": True})
        self._run(self.mpesa.get(session, url))
        self.mpesa.get.mock.assert_called_once_with(session, url)

    def test_generate_password(self):
        password, timestamp = self.mpesa.generate_password("123234", "xxxyyyy")
        self.assertIsInstance(password, str)
        self.assertIsInstance(timestamp, str)

    @mock.patch(
        "aiompesa.Mpesa.generate_token",
        AsyncMock(return_value={"access_token": "access_token"}),
    )
    def test_get_headers(self):
        headers = self._run(self.mpesa._get_headers())
        self.assertIsInstance(headers, dict)

    @mock.patch(
        "aiompesa.Mpesa.generate_token",
        AsyncMock(return_value={"access_token": None}),
    )
    def test_get_headers_fails(self):
        with pytest.raises(ValueError):
            assert self._run(self.fake_mpesa._get_headers())

    def test_generate_security_credential(self):
        cipher = self.mpesa.generate_security_credential(
            "examples/cert.cer", "test_pass"
        )
        self.assertIsInstance(cipher, bytes)

    def test_generate_security_credential_raises(self):
        with pytest.raises(FileNotFoundError):
            assert self.mpesa.generate_security_credential("fake/", "faketoo")

    def test_register_url_wrong_command_id(self):
        with pytest.raises(ValueError):
            assert self._run(self.mpesa.register_url("fake_type", "", "", ""))

    def test_register_url_wrong_callback_url(self):
        with pytest.raises(ValueError):
            assert self._run(
                self.mpesa.register_url("Completed", "123123", "fake_url", "")
            )

    def test_register_url_wrong_results_url(self):
        with pytest.raises(ValueError):
            assert self._run(
                self.mpesa.register_url(
                    "Completed",
                    "123123",
                    "https://good.com/callback",
                    "fake_url",
                )
            )

    @mock.patch(
        "aiompesa.Mpesa._get_headers",
        AsyncMock(return_value={"Content-Type": "application/json"}),
    )
    def test_register_url(self):
        with aioresponses() as mo:
            mo.post(
                "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl",
                payload={"success": True},
            )

            response = self._run(
                self.mpesa.register_url(
                    "Completed",
                    "123123",
                    "https://good.com/callback",
                    "https://good.com/callback",
                )
            )
            self.assertDictEqual(response, {"success": True})

    def test_post(self):
        url = "https://example.com/"
        session = AsyncMock(return_value=mock.Mock())
        self.mpesa.post = AsyncMock(return_value={"success": True})
        self._run(self.mpesa.post(session, url, data={"data": True}))
        self.mpesa.post.mock.assert_called_once_with(
            session, url, data={"data": True}
        )

    def test_c2b_invalid_phone(self):
        with pytest.raises(ValueError):
            assert self._run(self.mpesa.c2b("123123", 100, "0731100100"))

    @mock.patch(
        "aiompesa.Mpesa._get_headers",
        AsyncMock(return_value={"Content-Type": "application/json"}),
    )
    def test_c2b(self):
        with aioresponses() as mo:
            mo.post(
                "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/simulate",
                payload={"success": True},
            )

            response = self._run(self.mpesa.c2b("123123", 100, "0721100100"))
            self.assertDictEqual(response, {"success": True})

    def test_b2c_invalid_party_b(self):
        with pytest.raises(ValueError):
            assert self._run(
                self.mpesa.b2c(
                    initiator_name="tester",
                    security_credential="xxx",
                    command_id="Wrong",
                    amount=100,
                    party_a="123123",
                    party_b="0731123123",
                    remarks="test",
                    queue_timeout_url="https://test.mpesa/",
                    result_url="https://tested.mpesa",
                )
            )

    def test_b2c_invalid_command_id(self):
        with pytest.raises(ValueError):
            assert self._run(
                self.mpesa.b2c(
                    initiator_name="tester",
                    security_credential="xxx",
                    command_id="Wrong",
                    amount=100,
                    party_a="123123",
                    party_b="0721123123",
                    remarks="test",
                    queue_timeout_url="https://test.mpesa/",
                    result_url="https://tested.mpesa",
                )
            )

    @mock.patch(
        "aiompesa.Mpesa._get_headers",
        AsyncMock(return_value={"Content-Type": "application/json"}),
    )
    def test_b2c(self):
        with aioresponses() as mo:
            mo.post(
                "https://sandbox.safaricom.co.ke/mpesa/b2c/v1/paymentrequest",
                payload={"success": True},
            )

            response = self._run(
                self.mpesa.b2c(
                    initiator_name="tester",
                    security_credential="xxx",
                    command_id="SalaryPayment",
                    amount=100,
                    party_a="123123",
                    party_b="0721123123",
                    remarks="test",
                    queue_timeout_url="https://test.mpesa/",
                    result_url="https://tested.mpesa",
                )
            )
            self.assertDictEqual(response, {"success": True})

    def test_b2b_invalid_party_b(self):
        with pytest.raises(ValueError):
            assert self._run(
                self.mpesa.b2b(
                    initiator_name="tester",
                    security_credential="xxx",
                    command_id="Wrong",
                    amount=100,
                    party_a="123123",
                    party_b="0731123123",
                    remarks="test",
                    queue_timeout_url="https://test.mpesa/",
                    result_url="https://tested.mpesa",
                )
            )

    def test_b2b_invalid_command_id(self):
        with pytest.raises(ValueError):
            assert self._run(
                self.mpesa.b2c(
                    initiator_name="tester",
                    security_credential="xxx",
                    command_id="Wrong",
                    amount=100,
                    party_a="123123",
                    party_b="0721123123",
                    remarks="test",
                    queue_timeout_url="https://test.mpesa/",
                    result_url="https://tested.mpesa",
                )
            )

    @mock.patch(
        "aiompesa.Mpesa._get_headers",
        AsyncMock(return_value={"Content-Type": "application/json"}),
    )
    def test_b2b(self):
        with aioresponses() as mo:
            mo.post(
                "https://sandbox.safaricom.co.ke/mpesa/b2b/v1/paymentrequest",
                payload={"success": True},
            )
            response = self._run(
                self.mpesa.b2b(
                    initiator_name="tester",
                    security_credential="xxx",
                    command_id="BusinessBuyGoods",
                    amount=100,
                    party_a="123123",
                    party_b="0721123123",
                    remarks="test",
                    queue_timeout_url="https://test.mpesa/",
                    result_url="https://tested.mpesa",
                )
            )
            self.assertDictEqual(response, {"success": True})

    def test_stk_push_invalid_party_b(self):
        with pytest.raises(ValueError):
            assert self._run(
                self.mpesa.stk_push(
                    lipa_na_mpesa_shortcode="123123",
                    lipa_na_mpesa_passkey="xxx",
                    amount=100,
                    party_a="123123",
                    party_b="0731123123",
                    callback_url="https://results.back/",
                    transaction_desc="test",
                )
            )

    @mock.patch(
        "aiompesa.Mpesa.generate_password",
        mock.MagicMock(return_value=("axsaxa", "20180901349134")),
    )
    @mock.patch(
        "aiompesa.Mpesa._get_headers",
        AsyncMock(return_value={"Content-Type": "application/json"}),
    )
    def test_stk_push_valid(self):
        with aioresponses() as mo:
            mo.post(
                "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
                payload={"success": True},
            )

            response = self._run(
                self.mpesa.stk_push(
                    lipa_na_mpesa_shortcode="123123",
                    lipa_na_mpesa_passkey="xxx",
                    amount=100,
                    party_a="0721123123",
                    party_b="123123",
                    callback_url="https://results.back/",
                    transaction_desc="test",
                )
            )
            self.assertDictEqual(response, {"success": True})

    @mock.patch(
        "aiompesa.Mpesa._get_headers",
        AsyncMock(return_value={"Content-Type": "application/json"}),
    )
    def test_reversal(self):
        with aioresponses() as mo:
            mo.post(
                "https://sandbox.safaricom.co.ke/mpesa/reversal/v1/request",
                payload={"success": True},
            )
            response = self._run(
                self.mpesa.reversal(
                    initiator="tester",
                    security_credential="xxx",
                    transaction_id="AERW90348NFSD",
                    amount=100,
                    receiver_party="0721123123",
                    occasion="0721123123",
                    remarks="test",
                    queue_timeout_url="https://test.mpesa/",
                    result_url="https://tested.mpesa",
                )
            )
            self.assertDictEqual(response, {"success": True})
