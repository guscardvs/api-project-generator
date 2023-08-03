import random
import socket
from typing import Any, Mapping
from unicodedata import normalize

from gyver.utils import strings


def clean_name(string: str):
    return normalize("NFC", string.strip().replace("-", "_"))

MAX_PORT = 65535

def find_next_available_port(default_port: int):
    # Check if the default port is available
    if is_port_available(default_port):
        return default_port

    # Try additional ports with prefixes
    for prefix in range(1, 7):
        port = min(int(f"{prefix}{default_port}"), MAX_PORT)
        if is_port_available(port):
            return port

    # If no match found, return a random port after the default port
    return get_random_port(default_port)


def is_port_available(port: int):
    # Check if the port is available by attempting to bind to it
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("localhost", port))
        return True
    except socket.error:
        return False


def get_random_port(min_port: int):
    # Generate a random port between the minimum port and 65535
    return random.randint(min_port, MAX_PORT)


def kebab_case(string: str):
    return strings.to_snake(string).replace("_", "-")


def lead_spaces_as_tabs(string: str):
    """
    Replaces leading spaces with tabs in each line of the provided string.

    :param string: The input string to convert.
    :return: The converted string with spaces replaced by tabs.
    """
    return "\n".join(item.replace(" " * 4, "\t") for item in string.split("\n"))


def tabs_as_lead_spaces(string: str) -> str:
    """
    Replaces leading tabs with spaces in each line of the provided string.

    :param string: The input string to convert.
    :return: The converted string with tabs replaced by spaces.
    """
    return "\n".join(item.replace("\t", " " * 4) for item in string.split("\n"))


def prettify(val: Mapping[str, Any]) -> str:
    """
    Format a mapping object as a string representation with styled docstrings.

    :param val: The mapping object to be prettified.
    :return: The formatted string representation of the mapping object.
    """
    return "\n".join(f"{key} -> {value}" for key, value in val.items())
