"""
OCI MCP Server - A simplified MCP server for Oracle Cloud Infrastructure.
"""

import argparse
import os
import sys
from typing import Dict, List, Any, Optional, Callable, TypeVar, Union
from functools import wraps

import oci
from loguru import logger

from mcp.server.fastmcp import FastMCP, Context
from mcp_server_oci.config import (
    DEFAULT_SSE_PORT,
    DEFAULT_LOG_LEVEL,
    DEFAULT_OCI_PROFILE,
)

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
from mcp_server_oci.tools.identity import (
    list_users,
    get_user,
    list_groups,
    get_group,
    list_policies,
    get_policy,
    list_dynamic_groups,
    get_dynamic_group,
)
from mcp_server_oci.tools.storage import (
    list_buckets,
    get_bucket,
    list_volumes,
    get_volume,
    list_boot_volumes,
    get_boot_volume,
    list_file_systems,
    get_file_system,
)
# Database resources (Autonomous, etc.) if needed
from mcp_server_oci.tools.database import (
    list_db_systems as list_db_systems_dbpkg,  # alias to avoid name clash
    get_db_system as get_db_system_dbpkg,
    list_databases,
    get_database,
    list_autonomous_databases,
    get_autonomous_database,
)
from mcp_server_oci.tools.security import (
    list_security_lists,
    get_security_list,
    list_network_security_groups,
    get_network_security_group,
    list_vaults,
    get_vault,
)
from mcp_server_oci.tools.load_balancer import (
    list_load_balancers,
    get_load_balancer,
    list_network_load_balancers,
    get_network_load_balancer,
)
from mcp_server_oci.tools.resources import (
    list_availability_domains,
    list_fault_domains,
    list_images,
    get_image,
    list_shapes,
    get_namespace,
    list_regions,
    get_tenancy_info,
)
# DB Systems tools (our corrected module)
from mcp_server_oci.tools.dbsystems import (
    list_db_systems,
    get_db_system,
    list_db_nodes,
    get_db_node,
    start_db_node,
    stop_db_node,
    reboot_db_node,
    reset_db_node,
    softreset_db_node,
    start_db_system_all_nodes,
    stop_db_system_all_nodes,
)

# Setup logging
logger.remove()
log_level = os.environ.get("FASTMCP_LOG_LEVEL", DEFAULT_LOG_LEVEL)
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
oci_clients: Dict[str, Any] = {}

# Type variable for generic function returns
T = TypeVar('T', bound=Union[Dict[str, Any], List[Dict[str, Any]]])


def mcp_tool_wrapper(start_msg: str = None, success_msg: str = None, error_prefix: str = "Error"):
    """
    Decorator to wrap MCP tool functions with common error handling and logging.

    Implements Hybrid Error Handling Pattern (Option A):
    - Technical errors (network, permissions, etc.) → raise Exception → converted to {"error": ...}
    - Business states (already running, invalid state) → return {"success": bool, ...} → passed through

    Args:
        start_msg: Optional custom start message (supports {args} placeholders)
        success_msg: Optional custom success message (supports {result} placeholder)
        error_prefix: Prefix for error messages (default: "Error")

    Returns:
        Decorated async function with error handling and logging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(ctx: Context, *args, **kwargs) -> T:
            # Log start message
            if start_msg:
                try:
                    msg = start_msg.format(**kwargs) if kwargs else start_msg
                    await ctx.info(msg)
                except (KeyError, IndexError):
                    await ctx.info(start_msg)

            try:
                # Call the decorated function (which calls the underlying OCI function)
                result = await func(ctx, *args, **kwargs)

                # Check if result is a business state response
                if isinstance(result, dict) and "success" in result:
                    # Business state response - log based on success field
                    if result.get("success"):
                        msg = result.get("message", "Operation completed successfully")
                        await ctx.info(msg)
                    else:
                        # Business failure (not technical error)
                        msg = result.get("message", "Operation could not be completed")
                        await ctx.info(f"Business state: {msg}")
                    return result

                # Normal data response - log success message if provided
                if success_msg:
                    try:
                        msg = success_msg.format(result=result, **kwargs)
                        await ctx.info(msg)
                    except (KeyError, AttributeError):
                        await ctx.info(success_msg)

                return result

            except Exception as e:
                # Technical error - convert to error dict
                error_msg = f"{error_prefix}: {str(e)}"
                await ctx.error(error_msg)
                logger.exception(f"{error_prefix} in {func.__name__}")

                # Return error dict for consistency - check function return type annotation
                return_annotation = func.__annotations__.get('return', '')
                if 'List' in str(return_annotation):
                    return [{"error": error_msg}]
                return {"error": error_msg}

        return wrapper
    return decorator


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
        object_storage_client = oci.object_storage.ObjectStorageClient(config)
        block_storage_client = oci.core.BlockstorageClient(config)
        file_storage_client = oci.file_storage.FileStorageClient(config)
        database_client = oci.database.DatabaseClient(config)
        load_balancer_client = oci.load_balancer.LoadBalancerClient(config)
        network_load_balancer_client = oci.network_load_balancer.NetworkLoadBalancerClient(config)
        kms_vault_client = oci.key_management.KmsVaultClient(config)

        oci_clients = {
            "compute": compute_client,
            "identity": identity_client,
            "network": network_client,
            "object_storage": object_storage_client,
            "block_storage": block_storage_client,
            "file_storage": file_storage_client,
            "database": database_client,
            "load_balancer": load_balancer_client,
            "network_load_balancer": network_load_balancer_client,
            "kms_vault": kms_vault_client,
            "config": config,
        }

        logger.info("OCI clients initialized successfully")
        return oci_clients
    except Exception as e:
        logger.exception(f"Error initializing OCI clients: {e}")
        raise


# Compartment tools
@mcp.tool(name="list_compartments")
@mcp_tool_wrapper(
    start_msg="Listing compartments...",
    success_msg="Found {result} compartments" if isinstance(list_compartments, list) else None,
    error_prefix="Error listing compartments"
)
async def get_compartments(ctx: Context) -> List[Dict[str, Any]]:
    """List all compartments accessible to the user."""
    return list_compartments(oci_clients["identity"])


# Instance tools
@mcp.tool(name="list_instances")
@mcp_tool_wrapper(
    start_msg="Listing instances in compartment {compartment_id}...",
    error_prefix="Error listing instances"
)
async def get_instances(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """List all instances in a compartment."""
    return list_instances(oci_clients["compute"], compartment_id)


@mcp.tool(name="get_instance")
@mcp_tool_wrapper(
    start_msg="Getting details for instance {instance_id}...",
    success_msg="Retrieved instance details successfully",
    error_prefix="Error getting instance details"
)
async def get_instance_details(ctx: Context, instance_id: str) -> Dict[str, Any]:
    """Get details of a specific instance."""
    return get_instance(oci_clients["compute"], instance_id)


@mcp.tool(name="start_instance")
@mcp_tool_wrapper(
    start_msg="Starting instance {instance_id}...",
    error_prefix="Error starting instance"
)
async def start_instance_tool(ctx: Context, instance_id: str) -> Dict[str, Any]:
    """Start an instance."""
    return start_instance(oci_clients["compute"], instance_id)


@mcp.tool(name="stop_instance")
@mcp_tool_wrapper(
    start_msg="Stopping instance {instance_id}...",
    error_prefix="Error stopping instance"
)
async def stop_instance_tool(ctx: Context, instance_id: str, force: bool = False) -> Dict[str, Any]:
    """Stop an instance."""
    return stop_instance(oci_clients["compute"], instance_id, force)


# Network, Identity, Storage, etc. tools omitted for brevity in this snippet


# DB Systems tools
@mcp.tool(name="list_db_systems")
@mcp_tool_wrapper(
    start_msg="Listing DB Systems in compartment {compartment_id}...",
    error_prefix="Error listing DB Systems"
)
async def mcp_list_db_systems(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """List DB Systems in a compartment."""
    return list_db_systems(oci_clients["database"], compartment_id)


@mcp.tool(name="get_db_system")
@mcp_tool_wrapper(
    start_msg="Getting DB System {db_system_id}...",
    success_msg="Retrieved DB System successfully",
    error_prefix="Error getting DB System"
)
async def mcp_get_db_system(ctx: Context, db_system_id: str) -> Dict[str, Any]:
    """Get DB System details."""
    return get_db_system(oci_clients["database"], db_system_id)


@mcp.tool(name="list_db_nodes")
@mcp_tool_wrapper(
    start_msg="Listing DB Nodes in compartment {compartment_id}...",
    error_prefix="Error listing DB Nodes"
)
async def mcp_list_db_nodes(ctx: Context, compartment_id: str, db_system_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List DB Nodes in a compartment, optionally filtered by DB System.
    Note: compartment_id is always required by the SDK.
    """
    return list_db_nodes(
        oci_clients["database"],
        db_system_id=db_system_id,
        compartment_id=compartment_id,
    )


@mcp.tool(name="get_db_node")
@mcp_tool_wrapper(
    start_msg="Getting DB Node {db_node_id}...",
    success_msg="Retrieved DB Node successfully",
    error_prefix="Error getting DB Node"
)
async def mcp_get_db_node(ctx: Context, db_node_id: str) -> Dict[str, Any]:
    """Get DB Node details."""
    return get_db_node(oci_clients["database"], db_node_id)


@mcp.tool(name="start_db_node")
@mcp_tool_wrapper(
    start_msg="Starting DB Node {db_node_id}...",
    error_prefix="Error starting DB Node"
)
async def mcp_start_db_node(ctx: Context, db_node_id: str) -> Dict[str, Any]:
    """Start a DB Node."""
    return start_db_node(oci_clients["database"], db_node_id)


@mcp.tool(name="stop_db_node")
@mcp_tool_wrapper(
    start_msg="Stopping DB Node {db_node_id}...",
    error_prefix="Error stopping DB Node"
)
async def mcp_stop_db_node(ctx: Context, db_node_id: str, soft: bool = True) -> Dict[str, Any]:
    """Stop a DB Node."""
    return stop_db_node(oci_clients["database"], db_node_id, soft=soft)


@mcp.tool(name="reboot_db_node")
@mcp_tool_wrapper(
    start_msg="Rebooting DB Node {db_node_id}...",
    error_prefix="Error rebooting DB Node"
)
async def mcp_reboot_db_node(ctx: Context, db_node_id: str) -> Dict[str, Any]:
    """Reboot a DB Node."""
    return reboot_db_node(oci_clients["database"], db_node_id)


@mcp.tool(name="reset_db_node")
@mcp_tool_wrapper(
    start_msg="Resetting DB Node {db_node_id}...",
    error_prefix="Error resetting DB Node"
)
async def mcp_reset_db_node(ctx: Context, db_node_id: str) -> Dict[str, Any]:
    """Reset (force reboot) a DB Node."""
    return reset_db_node(oci_clients["database"], db_node_id)


@mcp.tool(name="softreset_db_node")
@mcp_tool_wrapper(
    start_msg="Soft resetting DB Node {db_node_id}...",
    error_prefix="Error soft resetting DB Node"
)
async def mcp_softreset_db_node(ctx: Context, db_node_id: str) -> Dict[str, Any]:
    """Soft reset (graceful reboot) a DB Node."""
    return softreset_db_node(oci_clients["database"], db_node_id)


@mcp.tool(name="start_db_system")
@mcp_tool_wrapper(
    start_msg="Starting all DB Nodes for DB System {db_system_id} in compartment {compartment_id}...",
    error_prefix="Error starting DB System nodes"
)
async def mcp_start_db_system(ctx: Context, db_system_id: str, compartment_id: str) -> Dict[str, Any]:
    """
    Start all nodes of a DB System.
    Note: compartment_id required to enumerate nodes correctly.
    """
    return start_db_system_all_nodes(oci_clients["database"], db_system_id, compartment_id)


@mcp.tool(name="stop_db_system")
@mcp_tool_wrapper(
    start_msg="Stopping all DB Nodes for DB System {db_system_id} in compartment {compartment_id}...",
    error_prefix="Error stopping DB System nodes"
)
async def mcp_stop_db_system(ctx: Context, db_system_id: str, compartment_id: str, soft: bool = True) -> Dict[str, Any]:
    """
    Stop all nodes of a DB System.
    Note: compartment_id required to enumerate nodes correctly.
    """
    return stop_db_system_all_nodes(oci_clients["database"], db_system_id, compartment_id, soft=soft)


def main() -> None:
    """Run the MCP server for OCI."""
    parser = argparse.ArgumentParser(
        description="A Model Context Protocol (MCP) server for Oracle Cloud Infrastructure"
    )

    parser.add_argument("--profile", default=os.environ.get("OCI_CLI_PROFILE", DEFAULT_OCI_PROFILE),
                        help="OCI profile to use")
    parser.add_argument("--sse", action="store_true", help="Use SSE transport")
    parser.add_argument("--port", type=int, default=DEFAULT_SSE_PORT, help="Port for SSE transport")
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
