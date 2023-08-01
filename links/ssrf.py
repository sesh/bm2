import ipaddress
import re
import socket
from urllib.parse import urlparse


def domain_is_valid(domain):
    if re.match(
        "^(?!\-)(?:(?:[a-zA-Z\d\_][a-zA-Z\d\-]{0,61})?[a-zA-Z\d]\.){1,126}(?!\d+)[a-zA-Z\d]{1,63}$",
        domain,
    ):
        return True
    return False


def domain_is_safe(domain):
    if not domain_is_valid(domain):
        return False

    parts = urlparse("https://" + domain)

    if parts.path or parts.params or parts.query or parts.fragment:
        return False

    try:
        result = socket.getaddrinfo(parts.netloc, 8000)
    except socket.gaierror:
        # didn't resolve
        return True

    for r in result:
        ip = r[4][0]
        if ip:
            if ipaddress.ip_address(ip).is_private:
                return False

    return True


def uri_is_safe(uri):
    if uri.startswith("https://") or uri.startswith("http://"):
        parts = urlparse(uri)
        return domain_is_safe(parts.netloc)
    return False
