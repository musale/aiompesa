from urllib.parse import urlparse
import re


def is_url(url):
    """Check if a given string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc, result.path])
    except ValueError:
        return False


def saf_number_fmt(phone_number):
    """Checks if a given number is a valid Safaricom number.

    Checks the formats mentioned in http://bit.ly/2N3XB9b
    """
    saf_number_regex = re.compile(
        r"^(?:254|\+254|0)?(7(?:(?:[129][0-9])|(?:0[0-8])|(5[789])|"
        "(4[0-1]))[0-9]{6})$"
    )
    valid = re.match(saf_number_regex, phone_number)
    if valid is not None:
        return f"254{valid.group()[-9:]}", True
    return valid, False
