import aiompesa
import asyncio
import pytest
from unittest import TestCase, mock

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
        """
        helper function that runs any coroutine in an event loop and passes its return value back to the caller.
        https://blog.miguelgrinberg.com/post/unit-testing-asyncio-code
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def setUp(self):
        self.mpesa = aiompesa.Mpesa(
            consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET
        )
        self.prod_mpesa = aiompesa.Mpesa(
            sandbox=False, consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET
        )
        self.fake_mpesa = aiompesa.Mpesa(False, "fake_key", "fake_secret")

    def test_sandbox_setup(self):
        assert self.prod_mpesa.base_url == self.mpesa.PRODUCTION_BASE_URL
        assert self.mpesa.base_url == self.mpesa.SANDBOX_BASE_URL

    def test_get_success_json(self):
        url = "https://google.com/"
        session = AsyncMock(return_value=mock.Mock())
        self.mpesa.get = AsyncMock(return_value={"success": True})
        self._run(self.mpesa.get(session, url))
        self.mpesa.get.mock.assert_called_once_with(session, url)

    def test_get_success_text(self):
        url = "https://google.com/"
        session = AsyncMock(return_value=mock.Mock())
        self.mpesa.get = AsyncMock(return_value="success")
        self._run(self.mpesa.get(session, url))
        self.mpesa.get.mock.assert_called_once_with(session, url)

    def test_generate_password(self):
        password, timestamp = self.mpesa.generate_password("123234", "xxxyyyy")
        self.assertIsInstance(password, str)
        self.assertIsInstance(timestamp, str)

    def test_get_headers(self):
        headers = self._run(self.mpesa._get_headers())
        self.assertIsInstance(headers, dict)

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

    def test_register_url(self):
        with pytest.raises(ValueError):
            assert self._run(self.mpesa.register_url("fake_type", "", "", ""))
        with pytest.raises(ValueError):
            assert self._run(
                self.mpesa.register_url("Completed", "123123", "fake_url", "")
            )
        with pytest.raises(ValueError):
            assert self._run(
                self.mpesa.register_url(
                    "Completed", "123123", "https://good.com/callback", "fake_url"
                )
            )
        self.mpesa.register_url = AsyncMock(return_value={"success": True})
        response = self._run(
            self.mpesa.register_url(
                "Completed",
                "123123",
                "https://good.com/callback",
                "https://good.com/callback",
            )
        )
        self.assertDictEqual(response, {"success": True})

