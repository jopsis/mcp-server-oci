"""
Utility functions for the OCI MCP Server.
"""

import os
import base64
import logging
import tempfile
from typing import Dict, Tuple, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


def generate_ssh_key_pair(key_size: int = 2048, comment: str = "oci-mcp-server-key") -> Tuple[str, str]:
    """
    Generate a new SSH key pair.
    
    Args:
        key_size: Size of the key in bits
        comment: Comment to add to the public key
        
    Returns:
        Tuple of (private_key, public_key) as strings
    """
    try:
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        
        # Get private key in PEM format
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        # Get public key in OpenSSH format
        public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        ).decode('utf-8')
        
        # Add comment to public key
        public_key = f"{public_key} {comment}"
        
        logger.info(f"Generated SSH key pair with size {key_size} bits")
        return private_key_pem, public_key
    except Exception as e:
        logger.exception(f"Error generating SSH key pair: {e}")
        raise


def save_ssh_key_pair(private_key: str, public_key: str, 
                      private_key_path: Optional[str] = None, 
                      public_key_path: Optional[str] = None) -> Dict[str, str]:
    """
    Save SSH key pair to files.
    
    Args:
        private_key: Private key in PEM format
        public_key: Public key in OpenSSH format
        private_key_path: Path to save private key (optional)
        public_key_path: Path to save public key (optional)
        
    Returns:
        Dictionary with paths to the saved files
    """
    try:
        # Create temporary files if paths not provided
        if not private_key_path:
            private_fd, private_key_path = tempfile.mkstemp(suffix='.pem', prefix='oci_mcp_')
            os.close(private_fd)
        
        if not public_key_path:
            public_fd, public_key_path = tempfile.mkstemp(suffix='.pub', prefix='oci_mcp_')
            os.close(public_fd)
        
        # Write keys to files
        with open(private_key_path, 'w') as f:
            f.write(private_key)
            
        # Set appropriate permissions for private key
        os.chmod(private_key_path, 0o600)
        
        with open(public_key_path, 'w') as f:
            f.write(public_key)
        
        logger.info(f"Saved SSH key pair to {private_key_path} and {public_key_path}")
        return {
            "private_key_path": private_key_path,
            "public_key_path": public_key_path
        }
    except Exception as e:
        logger.exception(f"Error saving SSH key pair: {e}")
        raise


def create_cloud_init_script(commands: list, packages: list = None) -> str:
    """
    Create a base64-encoded cloud-init script for instance initialization.
    
    Args:
        commands: List of commands to run at instance startup
        packages: List of packages to install
        
    Returns:
        Base64-encoded cloud-init script
    """
    try:
        if packages is None:
            packages = []
            
        # Create cloud-init YAML
        cloud_init = [
            "#cloud-config",
            "package_update: true",
            "package_upgrade: true"
        ]
        
        # Add packages if any
        if packages:
            cloud_init.append("packages:")
            for package in packages:
                cloud_init.append(f"  - {package}")
        
        # Add commands
        cloud_init.append("runcmd:")
        for command in commands:
            cloud_init.append(f"  - {command}")
        
        # Join and encode
        cloud_init_str = "\n".join(cloud_init)
        cloud_init_b64 = base64.b64encode(cloud_init_str.encode()).decode()
        
        logger.info(f"Created cloud-init script with {len(commands)} commands and {len(packages)} packages")
        return cloud_init_b64
    except Exception as e:
        logger.exception(f"Error creating cloud-init script: {e}")
        raise
