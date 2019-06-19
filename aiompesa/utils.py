from urllib.parse import urlparse


def is_url(url):
    """Check if a given string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc, result.path])
    except ValueError:
        return False
