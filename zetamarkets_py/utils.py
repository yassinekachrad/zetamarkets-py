import logging
import re
from typing import Optional

import colorlog
from solana.utils.cluster import cluster_api_url

from zetamarkets_py import constants
from zetamarkets_py.types import Asset, Network
from zetamarkets_py.zeta_client.accounts.state import State


def get_fixed_min_lot_size(_state: State, asset: Asset) -> int:
    match asset:
        case Asset.SOL:
            return 100
        case Asset.BTC:
            return 1
        case Asset.ETH:
            return 10
        case Asset.APT:
            return 100
        case Asset.ARB:
            return 1000
        case Asset.BNB:
            return 10
        case Asset.TIA:
            return 100
        case Asset.JTO:
            return 100
        case _:
            return 1


def get_fixed_tick_size(_state: State, _asset: Asset) -> int:
    return 100


def convert_fixed_int_to_decimal(amount: int) -> float:
    """
    Converts a fixed integer number to a decimal.

    Args:
        amount (int): The fixed integer to be converted.

    Returns:
        float: The converted decimal.
    """
    return amount / 10**constants.PLATFORM_PRECISION


def convert_decimal_to_fixed_int(amount: float, tick_size: int) -> int:
    """
    Converts a decimal to a fixed integer number.

    Args:
        amount (float): The decimal to be converted.

    Returns:
        int: The converted fixed integer.
    """
    return int((amount * 10**constants.PLATFORM_PRECISION / tick_size)) * tick_size


def convert_fixed_lot_to_decimal(amount: int) -> float:
    """
    Converts a fixed integer lot size to a decimal.

    Args:
        amount (int): The fixed lot to be converted.

    Returns:
        float: The converted decimal.
    """
    return amount / 10**constants.POSITION_PRECISION


def convert_decimal_to_fixed_lot(amount: float, min_lot_size: int) -> int:
    """
    Converts a decimal to a fixed integer lot size.

    Args:
        amount (float): The decimal to be converted.

    Returns:
        int: The converted fixed lot.
    """
    return int((amount * 10**constants.POSITION_PRECISION / min_lot_size)) * min_lot_size


def http_to_ws(endpoint: str) -> str:
    """
    Converts an HTTP endpoint to a WebSocket endpoint.

    Args:
        endpoint (str): The HTTP endpoint.

    Returns:
        str: The WebSocket endpoint.
    """
    return re.sub(r"^http", "ws", endpoint)


def cluster_endpoint(network: Network, tls: bool = True, ws: bool = False) -> str:
    """
    Retrieve the RPC API URL for the specified cluster.

    Args:
        network (Network): The network to use.
        tls (bool, optional): If True, use https. Defaults to True.
        ws (bool, optional): If True, use WebSocket. Defaults to False.

    Returns:
        str: The RPC API URL.
    """
    endpoint = cluster_api_url(network.value, tls=tls)  # type: ignore
    if ws:
        ws_endpoint = http_to_ws(endpoint)
        return ws_endpoint
    else:
        return endpoint


def get_tif_offset(expiry_ts: int, epoch_length: int, current_ts: int, tif_buffer: int = 0) -> int:
    """
    Get the Time in Force (TIF) offset.

    Args:
        expiry_ts (int): The expiry timestamp.
        epoch_length (int): The length of the epoch.
        current_ts (int): The current timestamp.

    Returns:
        int: The Time in Force offset.

    Raises:
        Exception: If the expiry timestamp is less than the current timestamp.
    """
    if expiry_ts < current_ts:
        raise Exception(f"Cannot place expired order, current_ts: {current_ts}, expiry_ts: {expiry_ts}")

    # Add tif_buffer here to slow down going into the next epoch to prevent 0x42 errors around epoch
    # The consequence is that you'll send really long expiry orders around the epoch because the tif_offset will be large even though onchain we've gone to a new epoch
    epoch_start = (current_ts - tif_buffer) - ((current_ts - tif_buffer) % epoch_length)

    tif_offset = expiry_ts - epoch_start
    return min(tif_offset, epoch_length)


def create_logger(name: str, log_level: int = logging.CRITICAL, file_name: Optional[str] = None) -> logging.Logger:
    """
    Create a logger.

    Args:
        name (str): The name of the logger.
        log_level (int, optional): The log level. Defaults to logging.CRITICAL.
        file_name (str, optional): The file name. If provided, logs will be written to this file. Defaults to None.

    Returns:
        logging.Logger: The created logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    formatter = colorlog.ColoredFormatter("%(log_color)s%(levelname)s:%(name)s:%(message)s")

    # Create console handler and set level to same as the logger
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if file_name:
        fh = logging.FileHandler(file_name)
        fh.setLevel(log_level)
        file_formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(message)s")
        fh.setFormatter(file_formatter)
        logger.addHandler(fh)
    return logger
