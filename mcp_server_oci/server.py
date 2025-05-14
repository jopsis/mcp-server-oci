"""
MCP server implementation for Oracle Cloud Infrastructure.
Uses the simplified API of MCP.
"""

import logging
from typing import List, Dict, Any, Optional

import oci

from mcp_server_oci.tools.compartments import (
    list_compartments,
)
from mcp_server_oci.tools.instances import (
    list_instances,
    get_instance,
    start_instance,
    stop_instance,
)

logger = logging.getLogger(__name__)


def create_oci_client(profile: str) -> Dict[str, Any]:
    """
    Create OCI clients using the specified profile.
    
    Args:
        profile: OCI configuration profile name
        
    Returns:
        Dictionary with various OCI clients
    """
    logger.info(f"Creating OCI clients with profile: {profile}")
    
    try:
        # Use OCI config from standard location
        config = oci.config.from_file(profile_name=profile)
        
        # Create clients for various services
        compute_client = oci.core.ComputeClient(config)
        identity_client = oci.identity.IdentityClient(config)
        network_client = oci.core.VirtualNetworkClient(config)
        
        return {
            "compute": compute_client,
            "identity": identity_client,
            "network": network_client,
            "config": config,
        }
    except Exception as e:
        logger.exception(f"Error creating OCI clients: {e}")
        raise


def create_oci_tools(profile: str) -> List[Dict[str, Any]]:
    """
    Create MCP tools for Oracle Cloud Infrastructure.
    
    Args:
        profile: OCI configuration profile name
        
    Returns:
        List of MCP tool definitions
    """
    clients = create_oci_client(profile)
    
    # Create tool definitions using the clients
    tools = [
        # Compartment tools
        {
            "name": "list_compartments",
            "description": "List all compartments accessible to the user",
            "function": lambda: list_compartments(clients["identity"]),
        },
        
        # Instance tools
        {
            "name": "list_instances",
            "description": "List all instances in a compartment",
            "function": lambda compartment_id: list_instances(clients["compute"], compartment_id),
            "parameters": {
                "compartment_id": {
                    "type": "string",
                    "description": "OCID of the compartment",
                },
            },
        },
        {
            "name": "get_instance",
            "description": "Get details of a specific instance",
            "function": lambda instance_id: get_instance(clients["compute"], instance_id),
            "parameters": {
                "instance_id": {
                    "type": "string",
                    "description": "OCID of the instance",
                },
            },
        },
        {
            "name": "start_instance",
            "description": "Start an instance",
            "function": lambda instance_id: start_instance(clients["compute"], instance_id),
            "parameters": {
                "instance_id": {
                    "type": "string",
                    "description": "OCID of the instance to start",
                },
            },
        },
        {
            "name": "stop_instance",
            "description": "Stop an instance",
            "function": lambda instance_id, force=False: stop_instance(
                clients["compute"], instance_id, force
            ),
            "parameters": {
                "instance_id": {
                    "type": "string",
                    "description": "OCID of the instance to stop",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force stop the instance if true",
                    "default": False,
                },
            },
        },
    ]
    
    return tools
