"""
OCI MCP Server - A simplified MCP server for Oracle Cloud Infrastructure.
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Dict, List, Any, Optional, Union, Tuple

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
)
from mcp_server_oci.tools.network import (
    list_vcns,
    get_vcn,
    list_subnets,
    get_subnet,
    list_vnics,
    get_vnic,
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
        "cryptography",
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


#
# Compartment tools
#

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


#
# Instance tools
#

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








#
# Network tools
#

@mcp.tool(name="list_vcns")
async def get_vcns(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all Virtual Cloud Networks (VCNs) in a compartment.
    
    Args:
        compartment_id: OCID of the compartment
        
    Returns:
        List of VCNs with their details
    """
    try:
        await ctx.info(f"Listing VCNs in compartment {compartment_id}...")
        result = list_vcns(oci_clients["network"], compartment_id)
        await ctx.info(f"Found {len(result)} VCNs")
        return result
    except Exception as e:
        error_msg = f"Error listing VCNs: {str(e)}"
        await ctx.error(error_msg)
        return [{"error": error_msg}]


@mcp.tool(name="get_vcn")
async def get_vcn_details(ctx: Context, vcn_id: str) -> Dict[str, Any]:
    """
    Get details of a specific VCN.
    
    Args:
        vcn_id: OCID of the VCN
        
    Returns:
        Details of the VCN
    """
    try:
        await ctx.info(f"Getting details for VCN {vcn_id}...")
        result = get_vcn(oci_clients["network"], vcn_id)
        await ctx.info(f"Retrieved VCN details successfully")
        return result
    except Exception as e:
        error_msg = f"Error getting VCN details: {str(e)}"
        await ctx.error(error_msg)
        return {"error": error_msg}


@mcp.tool(name="list_subnets")
async def get_subnets(ctx: Context, compartment_id: str, vcn_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all subnets in a compartment, optionally filtered by VCN.
    
    Args:
        compartment_id: OCID of the compartment
        vcn_id: Optional OCID of the VCN to filter by
        
    Returns:
        List of subnets with their details
    """
    try:
        if vcn_id:
            await ctx.info(f"Listing subnets in compartment {compartment_id} and VCN {vcn_id}...")
        else:
            await ctx.info(f"Listing all subnets in compartment {compartment_id} across all VCNs...")
            
        result = list_subnets(oci_clients["network"], compartment_id, vcn_id)
        await ctx.info(f"Found {len(result)} subnets")
        return result
    except Exception as e:
        error_msg = f"Error listing subnets: {str(e)}"
        await ctx.error(error_msg)
        return [{"error": error_msg}]


@mcp.tool(name="get_subnet")
async def get_subnet_details(ctx: Context, subnet_id: str) -> Dict[str, Any]:
    """
    Get details of a specific subnet.
    
    Args:
        subnet_id: OCID of the subnet
        
    Returns:
        Details of the subnet
    """
    try:
        await ctx.info(f"Getting details for subnet {subnet_id}...")
        result = get_subnet(oci_clients["network"], subnet_id)
        await ctx.info(f"Retrieved subnet details successfully")
        return result
    except Exception as e:
        error_msg = f"Error getting subnet details: {str(e)}"
        await ctx.error(error_msg)
        return {"error": error_msg}


@mcp.tool(name="list_vnics")
async def get_vnics(ctx: Context, compartment_id: str, instance_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all VNICs in a compartment, optionally filtered by instance.
    
    Args:
        compartment_id: OCID of the compartment
        instance_id: Optional OCID of the instance to filter by
        
    Returns:
        List of VNICs with their details
    """
    try:
        if instance_id:
            await ctx.info(f"Listing VNICs for instance {instance_id} in compartment {compartment_id}...")
        else:
            await ctx.info(f"Listing all VNICs in compartment {compartment_id}...")
            
        result = list_vnics(oci_clients["compute"], oci_clients["network"], compartment_id, instance_id)
        await ctx.info(f"Found {len(result)} VNICs")
        return result
    except Exception as e:
        error_msg = f"Error listing VNICs: {str(e)}"
        await ctx.error(error_msg)
        return [{"error": error_msg}]


@mcp.tool(name="get_vnic")
async def get_vnic_details(ctx: Context, vnic_id: str) -> Dict[str, Any]:
    """
    Get details of a specific VNIC.
    
    Args:
        vnic_id: OCID of the VNIC
        
    Returns:
        Details of the VNIC
    """
    try:
        await ctx.info(f"Getting details for VNIC {vnic_id}...")
        result = get_vnic(oci_clients["network"], vnic_id)
        await ctx.info(f"Retrieved VNIC details successfully")
        return result
    except Exception as e:
        error_msg = f"Error getting VNIC details: {str(e)}"
        await ctx.error(error_msg)
        return {"error": error_msg}


#
# Utility tools
#







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
