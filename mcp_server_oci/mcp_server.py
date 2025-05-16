"""
OCI MCP Server - A simplified MCP server for Oracle Cloud Infrastructure.
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Dict, List, Any, Optional

import oci
from loguru import logger
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP, Context

# Import OCI tools
from mcp_server_oci.tools.compartments import list_compartments
from mcp_server_oci.tools.instances import (
    list_instances,
    get_instance,
    start_instance,
    stop_instance,
    create_instance,
    terminate_instance,
)

# Setup logging
logger.remove()
log_level = os.environ.get("FASTMCP_LOG_LEVEL", "INFO")
logger.add(sys.stderr, level=log_level)

# Create the MCP server
mcp = FastMCP(
    "OCI MCP Server - Interact with Oracle Cloud Infrastructure",
    dependencies=[
        "oci",
        "loguru",
    ],
)

# Store OCI clients
oci_clients = {}


def init_oci_clients(profile: str = "DEFAULT") -> Dict[str, Any]:
    """
    Initialize OCI clients using the specified profile.
    
    Args:
        profile: OCI configuration profile name
        
    Returns:
        Dictionary with various OCI clients
    """
    global oci_clients
    
    logger.info(f"Initializing OCI clients with profile: {profile}")
    
    try:
        # Use OCI config from standard location
        config = oci.config.from_file(profile_name=profile)
        
        # Create clients for various services
        compute_client = oci.core.ComputeClient(config)
        identity_client = oci.identity.IdentityClient(config)
        network_client = oci.core.VirtualNetworkClient(config)
        
        oci_clients = {
            "compute": compute_client,
            "identity": identity_client,
            "network": network_client,
            "config": config,
        }
        
        logger.info("OCI clients initialized successfully")
        return oci_clients
    except Exception as e:
        logger.exception(f"Error initializing OCI clients: {e}")
        raise


@mcp.tool(name="list_compartments")
async def get_compartments(ctx: Context) -> List[Dict[str, Any]]:
    """
    List all compartments accessible to the user.
    
    Returns:
        List of compartments with their details
    """
    try:
        await ctx.info("Listing compartments...")
        result = list_compartments(oci_clients["identity"])
        await ctx.info(f"Found {len(result)} compartments")
        return result
    except Exception as e:
        error_msg = f"Error listing compartments: {str(e)}"
        await ctx.error(error_msg)
        return [{"error": error_msg}]


@mcp.tool(name="list_instances")
async def get_instances(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all instances in a compartment.
    
    Args:
        compartment_id: OCID of the compartment
        
    Returns:
        List of instances with their details
    """
    try:
        await ctx.info(f"Listing instances in compartment {compartment_id}...")
        result = list_instances(oci_clients["compute"], compartment_id)
        await ctx.info(f"Found {len(result)} instances")
        return result
    except Exception as e:
        error_msg = f"Error listing instances: {str(e)}"
        await ctx.error(error_msg)
        return [{"error": error_msg}]


@mcp.tool(name="get_instance")
async def get_instance_details(ctx: Context, instance_id: str) -> Dict[str, Any]:
    """
    Get details of a specific instance.
    
    Args:
        instance_id: OCID of the instance
        
    Returns:
        Details of the instance
    """
    try:
        await ctx.info(f"Getting details for instance {instance_id}...")
        result = get_instance(oci_clients["compute"], instance_id)
        await ctx.info(f"Retrieved instance details successfully")
        return result
    except Exception as e:
        error_msg = f"Error getting instance details: {str(e)}"
        await ctx.error(error_msg)
        return {"error": error_msg}


@mcp.tool(name="start_instance")
async def start_instance_tool(ctx: Context, instance_id: str) -> Dict[str, Any]:
    """
    Start an instance.
    
    Args:
        instance_id: OCID of the instance to start
        
    Returns:
        Result of the operation
    """
    try:
        await ctx.info(f"Starting instance {instance_id}...")
        result = start_instance(oci_clients["compute"], instance_id)
        await ctx.info(f"Instance start operation completed with status: {result['current_state']}")
        return result
    except Exception as e:
        error_msg = f"Error starting instance: {str(e)}"
        await ctx.error(error_msg)
        return {"error": error_msg}


@mcp.tool(name="stop_instance")
async def stop_instance_tool(ctx: Context, instance_id: str, force: bool = False) -> Dict[str, Any]:
    """
    Stop an instance.
    
    Args:
        instance_id: OCID of the instance to stop
        force: If True, perform a force stop
        
    Returns:
        Result of the operation
    """
    try:
        await ctx.info(f"Stopping instance {instance_id}{' (force)' if force else ''}...")
        result = stop_instance(oci_clients["compute"], instance_id, force)
        await ctx.info(f"Instance stop operation completed with status: {result['current_state']}")
        return result
    except Exception as e:
        error_msg = f"Error stopping instance: {str(e)}"
        await ctx.error(error_msg)
        return {"error": error_msg}


@mcp.tool(name="create_instance")
async def create_instance_tool(
    ctx: Context,
    compartment_id: str,
    availability_domain: str,
    subnet_id: str,
    shape: str,
    display_name: str,
    image_id: str,
    metadata: Dict[str, str] = None,
    boot_volume_size_in_gbs: Optional[int] = None,
    shape_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a new compute instance.
    
    Args:
        compartment_id: OCID of the compartment
        availability_domain: Availability domain name
        subnet_id: OCID of the subnet
        shape: Compute shape name
        display_name: Display name for the instance
        image_id: OCID of the image to use
        metadata: Optional metadata to include with the instance
        boot_volume_size_in_gbs: Optional boot volume size in GB
        shape_config: Optional shape configuration (e.g., OCPUs, memory)
        
    Returns:
        Details of the created instance
    """
    try:
        await ctx.info(f"Creating instance {display_name} in compartment {compartment_id}...")
        result = create_instance(
            oci_clients["compute"],
            oci_clients["network"],
            compartment_id,
            availability_domain,
            subnet_id,
            shape,
            display_name,
            image_id,
            metadata,
            boot_volume_size_in_gbs,
            shape_config,
        )
        
        if result.get("success", False):
            await ctx.info(f"Instance creation initiated successfully. Current state: {result.get('lifecycle_state', 'PROVISIONING')}")
        else:
            await ctx.error(f"Instance creation failed: {result.get('message', 'Unknown error')}")
            
        return result
    except Exception as e:
        error_msg = f"Error creating instance: {str(e)}"
        await ctx.error(error_msg)
        return {"error": error_msg}


@mcp.tool(name="terminate_instance")
async def terminate_instance_tool(
    ctx: Context,
    instance_id: str,
    preserve_boot_volume: bool = False,
) -> Dict[str, Any]:
    """
    Terminate (delete) a compute instance.
    
    Args:
        instance_id: OCID of the instance to terminate
        preserve_boot_volume: If True, the boot volume will be preserved after the instance is terminated
        
    Returns:
        Result of the operation
    """
    try:
        await ctx.info(f"Terminating instance {instance_id}...")
        result = terminate_instance(
            oci_clients["compute"],
            instance_id,
            preserve_boot_volume,
        )
        
        if result.get("success", False):
            await ctx.info(f"Instance termination operation completed with status: {result.get('current_state', 'UNKNOWN')}")
        else:
            await ctx.error(f"Instance termination failed: {result.get('message', 'Unknown error')}")
            
        return result
    except Exception as e:
        error_msg = f"Error terminating instance: {str(e)}"
        await ctx.error(error_msg)
        return {"error": error_msg}


def main() -> None:
    """Run the MCP server for OCI."""
    parser = argparse.ArgumentParser(
        description="A Model Context Protocol (MCP) server for Oracle Cloud Infrastructure"
    )
    parser.add_argument("--profile", default=os.environ.get("OCI_CLI_PROFILE", "DEFAULT"),
                        help="OCI profile to use")
    parser.add_argument("--sse", action="store_true", help="Use SSE transport")
    parser.add_argument("--port", type=int, default=45678, help="Port for SSE transport")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Set log level based on debug flag
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    # Initialize OCI clients
    try:
        init_oci_clients(args.profile)
    except Exception as e:
        logger.error(f"Failed to initialize OCI clients: {e}")
        sys.exit(1)
    
    # Run server with appropriate transport
    logger.info("Starting OCI MCP Server")
    
    if args.sse:
        logger.info(f"Using SSE transport on port {args.port}")
        mcp.settings.port = args.port
        mcp.run(transport="sse")
    else:
        logger.info("Using standard stdio transport")
        mcp.run()


if __name__ == "__main__":
    main()
