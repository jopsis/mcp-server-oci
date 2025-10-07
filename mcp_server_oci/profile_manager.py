"""
Profile management for OCI configuration.

Handles reading available profiles from ~/.oci/config and managing
the currently active profile for dynamic profile switching.
"""

import os
from typing import Dict, List, Optional
from pathlib import Path
import configparser
import logging

logger = logging.getLogger(__name__)

# Default OCI config location
DEFAULT_OCI_CONFIG_PATH = os.path.expanduser("~/.oci/config")


def get_oci_config_path() -> str:
    """
    Get the path to the OCI config file.

    Returns:
        Path to the OCI config file (defaults to ~/.oci/config)
    """
    return os.environ.get("OCI_CONFIG_FILE", DEFAULT_OCI_CONFIG_PATH)


def list_available_profiles() -> List[Dict[str, str]]:
    """
    List all available profiles from the OCI config file.

    Returns:
        List of dictionaries containing profile information:
        [
            {
                "name": "DEFAULT",
                "user": "ocid1.user...",
                "tenancy": "ocid1.tenancy...",
                "region": "us-ashburn-1",
                "fingerprint": "aa:bb:cc:..."
            },
            ...
        ]

    Raises:
        FileNotFoundError: If OCI config file doesn't exist
        Exception: If config file cannot be parsed
    """
    config_path = get_oci_config_path()

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"OCI config file not found at {config_path}. "
            f"Please create it or set OCI_CONFIG_FILE environment variable."
        )

    try:
        config = configparser.ConfigParser()
        config.read(config_path)

        profiles = []
        for section in config.sections():
            profile_info = {
                "name": section,
                "user": config.get(section, "user", fallback="N/A"),
                "tenancy": config.get(section, "tenancy", fallback="N/A"),
                "region": config.get(section, "region", fallback="N/A"),
                "fingerprint": config.get(section, "fingerprint", fallback="N/A"),
            }
            profiles.append(profile_info)

        logger.info(f"Found {len(profiles)} profiles in {config_path}")
        return profiles

    except Exception as e:
        logger.exception(f"Error parsing OCI config file: {e}")
        raise Exception(f"Failed to parse OCI config file at {config_path}: {str(e)}")


def validate_profile_exists(profile_name: str) -> bool:
    """
    Check if a profile exists in the OCI config file.

    Args:
        profile_name: Name of the profile to check

    Returns:
        True if profile exists, False otherwise
    """
    try:
        profiles = list_available_profiles()
        return any(p["name"] == profile_name for p in profiles)
    except Exception as e:
        logger.error(f"Error validating profile: {e}")
        return False


def get_profile_info(profile_name: str) -> Optional[Dict[str, str]]:
    """
    Get detailed information about a specific profile.

    Args:
        profile_name: Name of the profile

    Returns:
        Dictionary with profile information, or None if not found
    """
    try:
        profiles = list_available_profiles()
        for profile in profiles:
            if profile["name"] == profile_name:
                return profile
        return None
    except Exception as e:
        logger.error(f"Error getting profile info: {e}")
        return None
