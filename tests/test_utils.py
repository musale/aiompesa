import random

from aiompesa import utils

random.seed(999999)


def test_isurl():
    """Test valid urls with a path."""
    valid_urls = [
        "https://test.com/valid_path/",
        "https://www.test.com/valid_path/",
    ]
    for url in valid_urls:
        valid = utils.is_url(url)
        assert valid is True


def test_isurl_false() -> None:
    """Test invalid urls."""
    invalid_urls = [
        "https://invalid.com",
        "invalid.com",
        "invalid",
        "invalid.com/with_path",
    ]
    for url in invalid_urls:
        valid = utils.is_url(url)
        assert valid is False


def test_valid_saf_numbers() -> None:
    """Test valid safaricom numbers."""

    def subscriber():
        return random.randint(100000, 999999)

    gen700_708 = [f"070{i}{subscriber()}" for i in range(0, 8)]
    gen710_729 = [f"07{i}{subscriber()}" for i in range(10, 29)]
    gen757_759 = [f"07{i}{subscriber()}" for i in range(57, 59)]
    gen790_792 = [f"07{i}{subscriber()}" for i in range(90, 92)]
    safaricom_numbers = gen700_708 + gen710_729 + gen757_759 + gen790_792
    for number in safaricom_numbers:
        _, valid = utils.saf_number_fmt(number)
        assert valid is True
