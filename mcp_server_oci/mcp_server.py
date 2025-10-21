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
from mcp_server_oci.profile_manager import (
    list_available_profiles,
    validate_profile_exists,
    get_profile_info,
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
    list_keys,
    get_key,
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
from mcp_server_oci.tools.cost import (
    get_cost_usage_summary,
    get_cost_by_service,
    get_cost_by_compartment,
    list_budgets,
    get_budget,
)
from mcp_server_oci.tools.monitoring import (
    list_alarms,
    get_alarm,
    get_alarm_history,
    list_metrics,
    query_metric_data,
    search_logs,
    list_log_groups,
    list_logs,
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
from mcp_server_oci.tools.oke import (
    list_clusters,
    get_cluster,
    list_node_pools,
    get_node_pool,
    get_cluster_kubeconfig,
    list_work_requests,
    get_work_request,
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

# Store OCI clients and current profile
oci_clients: Dict[str, Any] = {}
current_profile: Optional[str] = None

# Type variable for generic function returns
T = TypeVar('T', bound=Union[Dict[str, Any], List[Dict[str, Any]]])


def mcp_tool_wrapper(start_msg: str = None, success_msg: str = None, error_prefix: str = "Error", require_profile: bool = True):
    """
    Decorator to wrap MCP tool functions with common error handling and logging.

    Implements Hybrid Error Handling Pattern (Option A):
    - Technical errors (network, permissions, etc.) → raise Exception → converted to {"error": ...}
    - Business states (already running, invalid state) → return {"success": bool, ...} → passed through

    Args:
        start_msg: Optional custom start message (supports {args} placeholders)
        success_msg: Optional custom success message (supports {result} placeholder)
        error_prefix: Prefix for error messages (default: "Error")
        require_profile: Whether this tool requires an active OCI profile (default: True)

    Returns:
        Decorated async function with error handling and logging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(ctx: Context, *args, **kwargs) -> T:
            # Check if profile is required and active
            if require_profile and current_profile is None:
                error_msg = "No OCI profile selected. Use 'list_oci_profiles' to see available profiles, then 'set_oci_profile' to activate one."
                await ctx.error(error_msg)

                # Return error dict for consistency - check function return type annotation
                return_annotation = func.__annotations__.get('return', '')
                if 'List' in str(return_annotation):
                    return [{"error": error_msg, "requires_profile": True}]
                return {"error": error_msg, "requires_profile": True}

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
        usage_api_client = oci.usage_api.UsageapiClient(config)
        budget_client = oci.budget.BudgetClient(config)
        monitoring_client = oci.monitoring.MonitoringClient(config)
        logging_search_client = oci.loggingsearch.LogSearchClient(config)
        logging_client = oci.logging.LoggingManagementClient(config)
        container_engine_client = oci.container_engine.ContainerEngineClient(config)

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
            "usage_api": usage_api_client,
            "budget": budget_client,
            "monitoring": monitoring_client,
            "logging_search": logging_search_client,
            "logging": logging_client,
            "container_engine": container_engine_client,
            "config": config,
        }

        logger.info("OCI clients initialized successfully")
        return oci_clients
    except Exception as e:
        logger.exception(f"Error initializing OCI clients: {e}")
        raise


# Profile Management Tools
@mcp.tool(name="list_oci_profiles")
async def list_profiles_tool(ctx: Context) -> List[Dict[str, str]]:
    """
    List all available OCI profiles from ~/.oci/config file.

    Returns a list of profiles with their configuration details.
    Use this when you need to select a profile before making OCI API calls.
    """
    try:
        await ctx.info("Reading available OCI profiles from config file...")
        profiles = list_available_profiles()

        if not profiles:
            await ctx.info("No profiles found in OCI config file")
            return [{
                "error": "No profiles found in OCI config file. Please configure OCI CLI first."
            }]

        await ctx.info(f"Found {len(profiles)} available profiles")
        return profiles
    except FileNotFoundError as e:
        error_msg = str(e)
        await ctx.error(error_msg)
        return [{"error": error_msg}]
    except Exception as e:
        error_msg = f"Error listing profiles: {str(e)}"
        await ctx.error(error_msg)
        logger.exception("Error listing OCI profiles")
        return [{"error": error_msg}]


@mcp.tool(name="set_oci_profile")
async def set_profile_tool(ctx: Context, profile_name: str) -> Dict[str, Any]:
    """
    Set the active OCI profile to use for API calls.

    Args:
        profile_name: Name of the profile to activate (e.g., "DEFAULT", "production")

    This will initialize or reinitialize OCI clients with the selected profile.
    """
    global oci_clients, current_profile

    try:
        await ctx.info(f"Setting active profile to: {profile_name}")

        # Validate profile exists
        if not validate_profile_exists(profile_name):
            error_msg = f"Profile '{profile_name}' not found in OCI config. Use list_oci_profiles to see available profiles."
            await ctx.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "current_profile": current_profile
            }

        # Get profile info
        profile_info = get_profile_info(profile_name)

        # Initialize OCI clients with the selected profile
        await ctx.info(f"Initializing OCI clients with profile '{profile_name}'...")
        oci_clients = init_oci_clients(profile_name)
        current_profile = profile_name

        await ctx.info(f"Successfully activated profile: {profile_name}")
        return {
            "success": True,
            "message": f"Profile '{profile_name}' activated successfully",
            "current_profile": current_profile,
            "profile_details": profile_info
        }

    except Exception as e:
        error_msg = f"Error setting profile: {str(e)}"
        await ctx.error(error_msg)
        logger.exception(f"Error setting profile to {profile_name}")
        return {
            "success": False,
            "message": error_msg,
            "current_profile": current_profile
        }


@mcp.tool(name="get_current_oci_profile")
async def get_current_profile_tool(ctx: Context) -> Dict[str, Any]:
    """
    Get the currently active OCI profile.

    Returns information about which profile is currently being used for API calls.
    """
    try:
        if current_profile is None:
            await ctx.info("No profile currently active")
            return {
                "active": False,
                "message": "No profile selected. Use list_oci_profiles to see available profiles, then set_oci_profile to activate one."
            }

        profile_info = get_profile_info(current_profile)
        await ctx.info(f"Current active profile: {current_profile}")

        return {
            "active": True,
            "current_profile": current_profile,
            "profile_details": profile_info
        }

    except Exception as e:
        error_msg = f"Error getting current profile: {str(e)}"
        await ctx.error(error_msg)
        logger.exception("Error getting current profile")
        return {
            "error": error_msg
        }


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


# Network tools - VCNs
@mcp.tool(name="list_vcns")
@mcp_tool_wrapper(
    start_msg="Listing VCNs in compartment {compartment_id}...",
    error_prefix="Error listing VCNs"
)
async def mcp_list_vcns(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all Virtual Cloud Networks (VCNs) in a compartment.

    Args:
        compartment_id: OCID of the compartment to list VCNs from

    Returns:
        List of VCNs with their CIDR blocks, DNS labels, and default resources
    """
    return list_vcns(oci_clients["network"], compartment_id)


@mcp.tool(name="get_vcn")
@mcp_tool_wrapper(
    start_msg="Getting VCN details for {vcn_id}...",
    success_msg="Retrieved VCN details successfully",
    error_prefix="Error getting VCN details"
)
async def mcp_get_vcn(ctx: Context, vcn_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific VCN.

    Args:
        vcn_id: OCID of the VCN to retrieve

    Returns:
        Detailed VCN information including CIDR blocks, DNS configuration, and default resources
    """
    return get_vcn(oci_clients["network"], vcn_id)


# Network tools - Subnets
@mcp.tool(name="list_subnets")
@mcp_tool_wrapper(
    start_msg="Listing subnets in compartment {compartment_id}...",
    error_prefix="Error listing subnets"
)
async def mcp_list_subnets(ctx: Context, compartment_id: str, vcn_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all subnets in a compartment, optionally filtered by VCN.

    Args:
        compartment_id: OCID of the compartment to list subnets from
        vcn_id: Optional OCID of the VCN to filter subnets

    Returns:
        List of subnets with CIDR blocks, security lists, and routing information
    """
    return list_subnets(oci_clients["network"], compartment_id, vcn_id)


@mcp.tool(name="get_subnet")
@mcp_tool_wrapper(
    start_msg="Getting subnet details for {subnet_id}...",
    success_msg="Retrieved subnet details successfully",
    error_prefix="Error getting subnet details"
)
async def mcp_get_subnet(ctx: Context, subnet_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific subnet.

    Args:
        subnet_id: OCID of the subnet to retrieve

    Returns:
        Detailed subnet information including CIDR, security lists, and routing
    """
    return get_subnet(oci_clients["network"], subnet_id)


# Network tools - VNICs
@mcp.tool(name="list_vnics")
@mcp_tool_wrapper(
    start_msg="Listing VNICs in compartment {compartment_id}...",
    error_prefix="Error listing VNICs"
)
async def mcp_list_vnics(ctx: Context, compartment_id: str, instance_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all Virtual Network Interface Cards (VNICs) in a compartment.

    Args:
        compartment_id: OCID of the compartment to list VNICs from
        instance_id: Optional OCID of the instance to filter VNICs

    Returns:
        List of VNICs with their IP addresses, subnet information, and security groups
    """
    return list_vnics(oci_clients["compute"], oci_clients["network"], compartment_id, instance_id)


@mcp.tool(name="get_vnic")
@mcp_tool_wrapper(
    start_msg="Getting VNIC details for {vnic_id}...",
    success_msg="Retrieved VNIC details successfully",
    error_prefix="Error getting VNIC details"
)
async def mcp_get_vnic(ctx: Context, vnic_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific VNIC.

    Args:
        vnic_id: OCID of the VNIC to retrieve

    Returns:
        Detailed VNIC information including IP addresses, subnet, and NSG associations
    """
    return get_vnic(oci_clients["network"], vnic_id)


# Network tools - Security Lists
@mcp.tool(name="list_security_lists")
@mcp_tool_wrapper(
    start_msg="Listing security lists in compartment {compartment_id}...",
    error_prefix="Error listing security lists"
)
async def mcp_list_security_lists(ctx: Context, compartment_id: str, vcn_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all security lists in a compartment, optionally filtered by VCN.

    Args:
        compartment_id: OCID of the compartment to list security lists from
        vcn_id: Optional OCID of the VCN to filter security lists

    Returns:
        List of security lists with their ingress and egress rules
    """
    return list_security_lists(oci_clients["network"], compartment_id, vcn_id)


@mcp.tool(name="get_security_list")
@mcp_tool_wrapper(
    start_msg="Getting security list details for {security_list_id}...",
    success_msg="Retrieved security list details successfully",
    error_prefix="Error getting security list details"
)
async def mcp_get_security_list(ctx: Context, security_list_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific security list.

    Args:
        security_list_id: OCID of the security list to retrieve

    Returns:
        Detailed security list with all ingress and egress rules
    """
    return get_security_list(oci_clients["network"], security_list_id)


# Network tools - Network Security Groups
@mcp.tool(name="list_network_security_groups")
@mcp_tool_wrapper(
    start_msg="Listing network security groups in compartment {compartment_id}...",
    error_prefix="Error listing network security groups"
)
async def mcp_list_network_security_groups(ctx: Context, compartment_id: str, vcn_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all Network Security Groups (NSGs) in a compartment.

    Args:
        compartment_id: OCID of the compartment to list NSGs from
        vcn_id: Optional OCID of the VCN to filter NSGs

    Returns:
        List of NSGs with their security rules
    """
    return list_network_security_groups(oci_clients["network"], compartment_id, vcn_id)


@mcp.tool(name="get_network_security_group")
@mcp_tool_wrapper(
    start_msg="Getting network security group details for {nsg_id}...",
    success_msg="Retrieved network security group details successfully",
    error_prefix="Error getting network security group details"
)
async def mcp_get_network_security_group(ctx: Context, nsg_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific Network Security Group.

    Args:
        nsg_id: OCID of the NSG to retrieve

    Returns:
        Detailed NSG information with all security rules
    """
    return get_network_security_group(oci_clients["network"], nsg_id)


# Storage tools - Object Storage
@mcp.tool(name="get_namespace")
@mcp_tool_wrapper(
    start_msg="Getting Object Storage namespace...",
    success_msg="Retrieved namespace successfully",
    error_prefix="Error getting namespace"
)
async def mcp_get_namespace(ctx: Context) -> Dict[str, Any]:
    """
    Get the Object Storage namespace for the tenancy.

    The namespace is a unique identifier for the tenancy in Object Storage.
    It's required for all Object Storage operations.

    Returns:
        Dictionary with namespace information
    """
    return get_namespace(oci_clients["object_storage"])


@mcp.tool(name="list_buckets")
@mcp_tool_wrapper(
    start_msg="Listing Object Storage buckets in compartment {compartment_id}...",
    error_prefix="Error listing buckets"
)
async def mcp_list_buckets(ctx: Context, compartment_id: str, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all Object Storage buckets in a compartment.

    Args:
        compartment_id: OCID of the compartment to list buckets from
        namespace: Optional namespace (if not provided, will be fetched automatically)

    Returns:
        List of buckets with their configurations and metadata
    """
    # Get namespace if not provided
    if not namespace:
        namespace_info = get_namespace(oci_clients["object_storage"])
        namespace = namespace_info.get("namespace")

    return list_buckets(oci_clients["object_storage"], namespace, compartment_id)


@mcp.tool(name="get_bucket")
@mcp_tool_wrapper(
    start_msg="Getting bucket details for {bucket_name}...",
    success_msg="Retrieved bucket details successfully",
    error_prefix="Error getting bucket details"
)
async def mcp_get_bucket(ctx: Context, bucket_name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Get detailed information about a specific Object Storage bucket.

    Args:
        bucket_name: Name of the bucket
        namespace: Optional namespace (if not provided, will be fetched automatically)

    Returns:
        Detailed bucket information including public access settings and versioning
    """
    # Get namespace if not provided
    if not namespace:
        namespace_info = get_namespace(oci_clients["object_storage"])
        namespace = namespace_info.get("namespace")

    return get_bucket(oci_clients["object_storage"], namespace, bucket_name)


# Storage tools - Block Storage (Volumes)
@mcp.tool(name="list_volumes")
@mcp_tool_wrapper(
    start_msg="Listing Block volumes in compartment {compartment_id}...",
    error_prefix="Error listing volumes"
)
async def mcp_list_volumes(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all Block Storage volumes in a compartment.

    Args:
        compartment_id: OCID of the compartment to list volumes from

    Returns:
        List of volumes with their size, state, and attachment information
    """
    return list_volumes(oci_clients["block_storage"], compartment_id)


@mcp.tool(name="get_volume")
@mcp_tool_wrapper(
    start_msg="Getting volume details for {volume_id}...",
    success_msg="Retrieved volume details successfully",
    error_prefix="Error getting volume details"
)
async def mcp_get_volume(ctx: Context, volume_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific Block Storage volume.

    Args:
        volume_id: OCID of the volume to retrieve

    Returns:
        Detailed volume information including size, performance tier, and backup policy
    """
    return get_volume(oci_clients["block_storage"], volume_id)


@mcp.tool(name="list_boot_volumes")
@mcp_tool_wrapper(
    start_msg="Listing boot volumes in compartment {compartment_id}...",
    error_prefix="Error listing boot volumes"
)
async def mcp_list_boot_volumes(ctx: Context, compartment_id: str, availability_domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all boot volumes in a compartment.

    Args:
        compartment_id: OCID of the compartment to list boot volumes from
        availability_domain: Optional AD to filter boot volumes

    Returns:
        List of boot volumes with their size, state, and source image information
    """
    return list_boot_volumes(oci_clients["block_storage"], compartment_id, availability_domain)


@mcp.tool(name="get_boot_volume")
@mcp_tool_wrapper(
    start_msg="Getting boot volume details for {boot_volume_id}...",
    success_msg="Retrieved boot volume details successfully",
    error_prefix="Error getting boot volume details"
)
async def mcp_get_boot_volume(ctx: Context, boot_volume_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific boot volume.

    Args:
        boot_volume_id: OCID of the boot volume to retrieve

    Returns:
        Detailed boot volume information including size, performance, and source image
    """
    return get_boot_volume(oci_clients["block_storage"], boot_volume_id)


# Storage tools - File Storage
@mcp.tool(name="list_file_systems")
@mcp_tool_wrapper(
    start_msg="Listing file systems in compartment {compartment_id}...",
    error_prefix="Error listing file systems"
)
async def mcp_list_file_systems(ctx: Context, compartment_id: str, availability_domain: str) -> List[Dict[str, Any]]:
    """
    List all File Storage file systems in a compartment and availability domain.

    Args:
        compartment_id: OCID of the compartment to list file systems from
        availability_domain: Name of the availability domain

    Returns:
        List of file systems with their state and metadata
    """
    return list_file_systems(oci_clients["file_storage"], compartment_id, availability_domain)


@mcp.tool(name="get_file_system")
@mcp_tool_wrapper(
    start_msg="Getting file system details for {file_system_id}...",
    success_msg="Retrieved file system details successfully",
    error_prefix="Error getting file system details"
)
async def mcp_get_file_system(ctx: Context, file_system_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific File Storage file system.

    Args:
        file_system_id: OCID of the file system to retrieve

    Returns:
        Detailed file system information including metered bytes and snapshots
    """
    return get_file_system(oci_clients["file_storage"], file_system_id)


# Database tools - Regular Databases
@mcp.tool(name="list_databases")
@mcp_tool_wrapper(
    start_msg="Listing databases in compartment {compartment_id}...",
    error_prefix="Error listing databases"
)
async def mcp_list_databases(ctx: Context, compartment_id: str, db_system_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all databases in a compartment, optionally filtered by DB System.

    Args:
        compartment_id: OCID of the compartment to list databases from
        db_system_id: Optional OCID of the DB System to filter databases

    Returns:
        List of databases with their state, version, and connection information
    """
    return list_databases(oci_clients["database"], compartment_id, db_system_id)


@mcp.tool(name="get_database")
@mcp_tool_wrapper(
    start_msg="Getting database details for {database_id}...",
    success_msg="Retrieved database details successfully",
    error_prefix="Error getting database details"
)
async def mcp_get_database(ctx: Context, database_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific database.

    Args:
        database_id: OCID of the database to retrieve

    Returns:
        Detailed database information including connection strings, character set, and PDB name
    """
    return get_database(oci_clients["database"], database_id)


# Database tools - Autonomous Databases
@mcp.tool(name="list_autonomous_databases")
@mcp_tool_wrapper(
    start_msg="Listing Autonomous Databases in compartment {compartment_id}...",
    error_prefix="Error listing Autonomous Databases"
)
async def mcp_list_autonomous_databases(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all Autonomous Databases in a compartment.

    Args:
        compartment_id: OCID of the compartment to list Autonomous Databases from

    Returns:
        List of Autonomous Databases with their configuration, workload type, and connection info
    """
    return list_autonomous_databases(oci_clients["database"], compartment_id)


@mcp.tool(name="get_autonomous_database")
@mcp_tool_wrapper(
    start_msg="Getting Autonomous Database details for {autonomous_database_id}...",
    success_msg="Retrieved Autonomous Database details successfully",
    error_prefix="Error getting Autonomous Database details"
)
async def mcp_get_autonomous_database(ctx: Context, autonomous_database_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific Autonomous Database.

    Args:
        autonomous_database_id: OCID of the Autonomous Database to retrieve

    Returns:
        Detailed Autonomous Database information including connection strings, wallet info, and auto-scaling settings
    """
    return get_autonomous_database(oci_clients["database"], autonomous_database_id)


# Identity & Access Management tools - Users
@mcp.tool(name="list_users")
@mcp_tool_wrapper(
    start_msg="Listing IAM users in compartment {compartment_id}...",
    error_prefix="Error listing users"
)
async def mcp_list_users(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all IAM users in a compartment.

    Args:
        compartment_id: OCID of the compartment to list users from

    Returns:
        List of users with their state, capabilities, and MFA status
    """
    return list_users(oci_clients["identity"], compartment_id)


@mcp.tool(name="get_user")
@mcp_tool_wrapper(
    start_msg="Getting user details for {user_id}...",
    success_msg="Retrieved user details successfully",
    error_prefix="Error getting user details"
)
async def mcp_get_user(ctx: Context, user_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific IAM user.

    Args:
        user_id: OCID of the user to retrieve

    Returns:
        Detailed user information including capabilities, MFA status, and group memberships
    """
    return get_user(oci_clients["identity"], user_id)


# Identity & Access Management tools - Groups
@mcp.tool(name="list_groups")
@mcp_tool_wrapper(
    start_msg="Listing IAM groups in compartment {compartment_id}...",
    error_prefix="Error listing groups"
)
async def mcp_list_groups(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all IAM groups in a compartment.

    Args:
        compartment_id: OCID of the compartment to list groups from

    Returns:
        List of groups with their members count and state
    """
    return list_groups(oci_clients["identity"], compartment_id)


@mcp.tool(name="get_group")
@mcp_tool_wrapper(
    start_msg="Getting group details for {group_id}...",
    success_msg="Retrieved group details successfully",
    error_prefix="Error getting group details"
)
async def mcp_get_group(ctx: Context, group_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific IAM group.

    Args:
        group_id: OCID of the group to retrieve

    Returns:
        Detailed group information including members and description
    """
    return get_group(oci_clients["identity"], group_id)


# Identity & Access Management tools - Policies
@mcp.tool(name="list_policies")
@mcp_tool_wrapper(
    start_msg="Listing IAM policies in compartment {compartment_id}...",
    error_prefix="Error listing policies"
)
async def mcp_list_policies(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all IAM policies in a compartment.

    Args:
        compartment_id: OCID of the compartment to list policies from

    Returns:
        List of policies with their statements and state
    """
    return list_policies(oci_clients["identity"], compartment_id)


@mcp.tool(name="get_policy")
@mcp_tool_wrapper(
    start_msg="Getting policy details for {policy_id}...",
    success_msg="Retrieved policy details successfully",
    error_prefix="Error getting policy details"
)
async def mcp_get_policy(ctx: Context, policy_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific IAM policy.

    Args:
        policy_id: OCID of the policy to retrieve

    Returns:
        Detailed policy information including all policy statements
    """
    return get_policy(oci_clients["identity"], policy_id)


# Identity & Access Management tools - Dynamic Groups
@mcp.tool(name="list_dynamic_groups")
@mcp_tool_wrapper(
    start_msg="Listing dynamic groups in compartment {compartment_id}...",
    error_prefix="Error listing dynamic groups"
)
async def mcp_list_dynamic_groups(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all dynamic groups in a compartment.

    Args:
        compartment_id: OCID of the compartment to list dynamic groups from

    Returns:
        List of dynamic groups with their matching rules and state
    """
    return list_dynamic_groups(oci_clients["identity"], compartment_id)


@mcp.tool(name="get_dynamic_group")
@mcp_tool_wrapper(
    start_msg="Getting dynamic group details for {dynamic_group_id}...",
    success_msg="Retrieved dynamic group details successfully",
    error_prefix="Error getting dynamic group details"
)
async def mcp_get_dynamic_group(ctx: Context, dynamic_group_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific dynamic group.

    Args:
        dynamic_group_id: OCID of the dynamic group to retrieve

    Returns:
        Detailed dynamic group information including matching rules for instance principals
    """
    return get_dynamic_group(oci_clients["identity"], dynamic_group_id)


# Load Balancer tools - Load Balancers
@mcp.tool(name="list_load_balancers")
@mcp_tool_wrapper(
    start_msg="Listing load balancers in compartment {compartment_id}...",
    error_prefix="Error listing load balancers"
)
async def mcp_list_load_balancers(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all classic load balancers in a compartment.

    Args:
        compartment_id: OCID of the compartment to list load balancers from

    Returns:
        List of load balancers with their IP addresses, shape, and state
    """
    return list_load_balancers(oci_clients["load_balancer"], compartment_id)


@mcp.tool(name="get_load_balancer")
@mcp_tool_wrapper(
    start_msg="Getting load balancer details for {load_balancer_id}...",
    success_msg="Retrieved load balancer details successfully",
    error_prefix="Error getting load balancer details"
)
async def mcp_get_load_balancer(ctx: Context, load_balancer_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific classic load balancer.

    Args:
        load_balancer_id: OCID of the load balancer to retrieve

    Returns:
        Detailed load balancer information including backend sets, listeners, and certificates
    """
    return get_load_balancer(oci_clients["load_balancer"], load_balancer_id)


# Load Balancer tools - Network Load Balancers
@mcp.tool(name="list_network_load_balancers")
@mcp_tool_wrapper(
    start_msg="Listing network load balancers in compartment {compartment_id}...",
    error_prefix="Error listing network load balancers"
)
async def mcp_list_network_load_balancers(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all network load balancers in a compartment.

    Args:
        compartment_id: OCID of the compartment to list network load balancers from

    Returns:
        List of network load balancers with their IP addresses and state
    """
    return list_network_load_balancers(oci_clients["network_load_balancer"], compartment_id)


@mcp.tool(name="get_network_load_balancer")
@mcp_tool_wrapper(
    start_msg="Getting network load balancer details for {network_load_balancer_id}...",
    success_msg="Retrieved network load balancer details successfully",
    error_prefix="Error getting network load balancer details"
)
async def mcp_get_network_load_balancer(ctx: Context, network_load_balancer_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific network load balancer.

    Args:
        network_load_balancer_id: OCID of the network load balancer to retrieve

    Returns:
        Detailed network load balancer information including backend sets and listeners
    """
    return get_network_load_balancer(oci_clients["network_load_balancer"], network_load_balancer_id)


# Infrastructure Utilities - Availability and Fault Domains
@mcp.tool(name="list_availability_domains")
@mcp_tool_wrapper(
    start_msg="Listing availability domains in compartment {compartment_id}...",
    error_prefix="Error listing availability domains"
)
async def mcp_list_availability_domains(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all availability domains in a compartment.

    Args:
        compartment_id: OCID of the compartment (typically use tenancy OCID for root)

    Returns:
        List of availability domains with their names and IDs
    """
    return list_availability_domains(oci_clients["identity"], compartment_id)


@mcp.tool(name="list_fault_domains")
@mcp_tool_wrapper(
    start_msg="Listing fault domains in availability domain {availability_domain}...",
    error_prefix="Error listing fault domains"
)
async def mcp_list_fault_domains(ctx: Context, compartment_id: str, availability_domain: str) -> List[Dict[str, Any]]:
    """
    List all fault domains in an availability domain.

    Args:
        compartment_id: OCID of the compartment
        availability_domain: Name of the availability domain

    Returns:
        List of fault domains with their names and IDs
    """
    return list_fault_domains(oci_clients["identity"], compartment_id, availability_domain)


# Infrastructure Utilities - Compute Images
@mcp.tool(name="list_images")
@mcp_tool_wrapper(
    start_msg="Listing compute images in compartment {compartment_id}...",
    error_prefix="Error listing images"
)
async def mcp_list_images(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all compute images in a compartment.

    Args:
        compartment_id: OCID of the compartment to list images from

    Returns:
        List of images with OS, version, size, and lifecycle state
    """
    return list_images(oci_clients["compute"], compartment_id)


@mcp.tool(name="get_image")
@mcp_tool_wrapper(
    start_msg="Getting image details for {image_id}...",
    success_msg="Retrieved image details successfully",
    error_prefix="Error getting image details"
)
async def mcp_get_image(ctx: Context, image_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific compute image.

    Args:
        image_id: OCID of the image to retrieve

    Returns:
        Detailed image information including launch options and OS details
    """
    return get_image(oci_clients["compute"], image_id)


# Infrastructure Utilities - Compute Shapes
@mcp.tool(name="list_shapes")
@mcp_tool_wrapper(
    start_msg="Listing compute shapes in compartment {compartment_id}...",
    error_prefix="Error listing shapes"
)
async def mcp_list_shapes(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all compute shapes available in a compartment.

    Args:
        compartment_id: OCID of the compartment

    Returns:
        List of shapes with CPU, memory, network, and GPU specifications
    """
    return list_shapes(oci_clients["compute"], compartment_id)


# Infrastructure Utilities - Regions and Tenancy
@mcp.tool(name="list_regions")
@mcp_tool_wrapper(
    start_msg="Listing all available OCI regions...",
    error_prefix="Error listing regions"
)
async def mcp_list_regions(ctx: Context) -> List[Dict[str, Any]]:
    """
    List all available OCI regions.

    Returns:
        List of regions with their keys and names
    """
    return list_regions(oci_clients["identity"])


@mcp.tool(name="get_tenancy_info")
@mcp_tool_wrapper(
    start_msg="Getting tenancy information for {tenancy_id}...",
    success_msg="Retrieved tenancy information successfully",
    error_prefix="Error getting tenancy information"
)
async def mcp_get_tenancy_info(ctx: Context, tenancy_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a tenancy.

    Args:
        tenancy_id: OCID of the tenancy

    Returns:
        Tenancy details including name, home region, and description
    """
    return get_tenancy_info(oci_clients["identity"], tenancy_id)


# Security & Encryption - Vaults
@mcp.tool(name="list_vaults")
@mcp_tool_wrapper(
    start_msg="Listing vaults in compartment {compartment_id}...",
    error_prefix="Error listing vaults"
)
async def mcp_list_vaults(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all KMS vaults in a compartment.

    Args:
        compartment_id: OCID of the compartment to list vaults from

    Returns:
        List of vaults with their type, endpoints, and state
    """
    return list_vaults(oci_clients["kms_vault"], compartment_id)


@mcp.tool(name="get_vault")
@mcp_tool_wrapper(
    start_msg="Getting vault details for {vault_id}...",
    success_msg="Retrieved vault details successfully",
    error_prefix="Error getting vault details"
)
async def mcp_get_vault(ctx: Context, vault_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific KMS vault.

    Args:
        vault_id: OCID of the vault to retrieve

    Returns:
        Detailed vault information including crypto and management endpoints
    """
    return get_vault(oci_clients["kms_vault"], vault_id)


# Security & Encryption - Keys
@mcp.tool(name="list_keys")
@mcp_tool_wrapper(
    start_msg="Listing encryption keys in vault...",
    error_prefix="Error listing keys"
)
async def mcp_list_keys(ctx: Context, compartment_id: str, management_endpoint: str) -> List[Dict[str, Any]]:
    """
    List all encryption keys in a vault's compartment.

    Note: You must first get a vault to obtain its management_endpoint.

    Args:
        compartment_id: OCID of the compartment
        management_endpoint: Management endpoint from the vault (get from vault details)

    Returns:
        List of keys with their algorithm, protection mode, and state
    """
    return list_keys(oci_clients["config"], management_endpoint, compartment_id)


@mcp.tool(name="get_key")
@mcp_tool_wrapper(
    start_msg="Getting encryption key details for {key_id}...",
    success_msg="Retrieved key details successfully",
    error_prefix="Error getting key details"
)
async def mcp_get_key(ctx: Context, key_id: str, management_endpoint: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific encryption key.

    Note: You must first get a vault to obtain its management_endpoint.

    Args:
        key_id: OCID of the key to retrieve
        management_endpoint: Management endpoint from the vault (get from vault details)

    Returns:
        Detailed key information including algorithm, shape, and versions
    """
    return get_key(oci_clients["config"], management_endpoint, key_id)


# Cost Management - Usage and Cost Analysis
@mcp.tool(name="get_cost_usage_summary")
@mcp_tool_wrapper(
    start_msg="Getting cost and usage summary...",
    error_prefix="Error getting cost usage summary"
)
async def mcp_get_cost_usage_summary(ctx: Context, tenant_id: str, time_usage_started: str,
                                    time_usage_ended: str, granularity: str = "DAILY") -> List[Dict[str, Any]]:
    """
    Get cost and usage summary for a tenancy.

    Args:
        tenant_id: OCID of the tenancy
        time_usage_started: Start time in ISO format (YYYY-MM-DD)
        time_usage_ended: End time in ISO format (YYYY-MM-DD)
        granularity: Granularity of the data (DAILY or MONTHLY), defaults to DAILY

    Returns:
        List of cost and usage summaries with amounts, services, and compartments
    """
    return get_cost_usage_summary(oci_clients["usage_api"], tenant_id, time_usage_started,
                                 time_usage_ended, granularity)


@mcp.tool(name="get_cost_by_service")
@mcp_tool_wrapper(
    start_msg="Getting cost breakdown by service...",
    error_prefix="Error getting cost by service"
)
async def mcp_get_cost_by_service(ctx: Context, tenant_id: str, time_usage_started: str,
                                  time_usage_ended: str) -> List[Dict[str, Any]]:
    """
    Get cost breakdown by service for a tenancy.

    Args:
        tenant_id: OCID of the tenancy
        time_usage_started: Start time in ISO format (YYYY-MM-DD)
        time_usage_ended: End time in ISO format (YYYY-MM-DD)

    Returns:
        List of costs grouped by service with total cost per service
    """
    return get_cost_by_service(oci_clients["usage_api"], tenant_id, time_usage_started, time_usage_ended)


@mcp.tool(name="get_cost_by_compartment")
@mcp_tool_wrapper(
    start_msg="Getting cost breakdown by compartment...",
    error_prefix="Error getting cost by compartment"
)
async def mcp_get_cost_by_compartment(ctx: Context, tenant_id: str, time_usage_started: str,
                                      time_usage_ended: str) -> List[Dict[str, Any]]:
    """
    Get cost breakdown by compartment for a tenancy.

    Args:
        tenant_id: OCID of the tenancy
        time_usage_started: Start time in ISO format (YYYY-MM-DD)
        time_usage_ended: End time in ISO format (YYYY-MM-DD)

    Returns:
        List of costs grouped by compartment with total cost per compartment
    """
    return get_cost_by_compartment(oci_clients["usage_api"], tenant_id, time_usage_started, time_usage_ended)


# Cost Management - Budgets
@mcp.tool(name="list_budgets")
@mcp_tool_wrapper(
    start_msg="Listing budgets in compartment {compartment_id}...",
    error_prefix="Error listing budgets"
)
async def mcp_list_budgets(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all budgets in a compartment.

    Args:
        compartment_id: OCID of the compartment to list budgets from

    Returns:
        List of budgets with amount, reset period, actual spend, and forecasted spend
    """
    return list_budgets(oci_clients["budget"], compartment_id)


@mcp.tool(name="get_budget")
@mcp_tool_wrapper(
    start_msg="Getting budget details for {budget_id}...",
    success_msg="Retrieved budget details successfully",
    error_prefix="Error getting budget details"
)
async def mcp_get_budget(ctx: Context, budget_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific budget.

    Args:
        budget_id: OCID of the budget to retrieve

    Returns:
        Detailed budget information including targets, alert rules, and spend tracking
    """
    return get_budget(oci_clients["budget"], budget_id)


# Monitoring & Observability - Alarms
@mcp.tool(name="list_alarms")
@mcp_tool_wrapper(
    start_msg="Listing alarms in compartment {compartment_id}...",
    error_prefix="Error listing alarms"
)
async def mcp_list_alarms(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all alarms in a compartment.

    Args:
        compartment_id: OCID of the compartment to list alarms from

    Returns:
        List of alarms with their query, severity, state, and destinations
    """
    return list_alarms(oci_clients["monitoring"], compartment_id)


@mcp.tool(name="get_alarm")
@mcp_tool_wrapper(
    start_msg="Getting alarm details for {alarm_id}...",
    success_msg="Retrieved alarm details successfully",
    error_prefix="Error getting alarm details"
)
async def mcp_get_alarm(ctx: Context, alarm_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific alarm.

    Args:
        alarm_id: OCID of the alarm to retrieve

    Returns:
        Detailed alarm information including query, thresholds, and notification settings
    """
    return get_alarm(oci_clients["monitoring"], alarm_id)


@mcp.tool(name="get_alarm_history")
@mcp_tool_wrapper(
    start_msg="Getting alarm history for {alarm_id}...",
    error_prefix="Error getting alarm history"
)
async def mcp_get_alarm_history(ctx: Context, alarm_id: str,
                                alarm_historytype: str = "STATE_TRANSITION_HISTORY") -> List[Dict[str, Any]]:
    """
    Get alarm state history.

    Args:
        alarm_id: OCID of the alarm
        alarm_historytype: Type of history (STATE_TRANSITION_HISTORY, STATE_HISTORY, RULE_HISTORY)

    Returns:
        List of alarm history entries with timestamps and state changes
    """
    return get_alarm_history(oci_clients["monitoring"], alarm_id, alarm_historytype)


# Monitoring & Observability - Metrics
@mcp.tool(name="list_metrics")
@mcp_tool_wrapper(
    start_msg="Listing metrics in compartment {compartment_id}...",
    error_prefix="Error listing metrics"
)
async def mcp_list_metrics(ctx: Context, compartment_id: str,
                           namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List available metrics in a compartment.

    Args:
        compartment_id: OCID of the compartment
        namespace: Optional namespace to filter metrics (e.g., oci_computeagent, oci_blockstore)

    Returns:
        List of available metrics with their namespaces and dimensions
    """
    return list_metrics(oci_clients["monitoring"], compartment_id, namespace)


@mcp.tool(name="query_metric_data")
@mcp_tool_wrapper(
    start_msg="Querying metric data...",
    error_prefix="Error querying metric data"
)
async def mcp_query_metric_data(ctx: Context, compartment_id: str, query: str,
                                start_time: str, end_time: str,
                                resolution: str = "1m") -> List[Dict[str, Any]]:
    """
    Query metric data for a time range using MQL.

    Args:
        compartment_id: OCID of the compartment
        query: Metric query in MQL format (e.g., "CpuUtilization[1m].mean()")
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SSZ)
        end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SSZ)
        resolution: Data resolution (1m, 5m, 1h)

    Returns:
        List of metric data points with timestamps and values
    """
    return query_metric_data(oci_clients["monitoring"], compartment_id, query,
                           start_time, end_time, resolution)


# Monitoring & Observability - Logs
@mcp.tool(name="search_logs")
@mcp_tool_wrapper(
    start_msg="Searching logs...",
    error_prefix="Error searching logs"
)
async def mcp_search_logs(ctx: Context, time_start: str, time_end: str,
                         search_query: str) -> List[Dict[str, Any]]:
    """
    Search logs using the Logging Search API.

    Args:
        time_start: Start time in ISO format (YYYY-MM-DDTHH:MM:SSZ)
        time_end: End time in ISO format (YYYY-MM-DDTHH:MM:SSZ)
        search_query: Search query string

    Returns:
        List of log entries matching the search criteria
    """
    search_details = {
        'time_start': time_start,
        'time_end': time_end,
        'search_query': search_query,
    }
    return search_logs(oci_clients["logging_search"], search_details)


@mcp.tool(name="list_log_groups")
@mcp_tool_wrapper(
    start_msg="Listing log groups in compartment {compartment_id}...",
    error_prefix="Error listing log groups"
)
async def mcp_list_log_groups(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all log groups in a compartment.

    Args:
        compartment_id: OCID of the compartment to list log groups from

    Returns:
        List of log groups with their display names and lifecycle states
    """
    return list_log_groups(oci_clients["logging"], compartment_id)


@mcp.tool(name="list_logs")
@mcp_tool_wrapper(
    start_msg="Listing logs in log group {log_group_id}...",
    error_prefix="Error listing logs"
)
async def mcp_list_logs(ctx: Context, log_group_id: str) -> List[Dict[str, Any]]:
    """
    List all logs in a log group.

    Args:
        log_group_id: OCID of the log group

    Returns:
        List of logs with their types, retention, and enabled state
    """
    return list_logs(oci_clients["logging"], log_group_id)


# ============================================================================
# Container Engine for Kubernetes (OKE) Tools
# ============================================================================

@mcp.tool(name="list_oke_clusters")
@mcp_tool_wrapper(
    start_msg="Listing OKE clusters in compartment {compartment_id}...",
    error_prefix="Error listing OKE clusters"
)
async def mcp_list_oke_clusters(ctx: Context, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all OKE (Container Engine for Kubernetes) clusters in a compartment.

    Args:
        compartment_id: OCID of the compartment

    Returns:
        List of OKE clusters with their details including Kubernetes version, endpoints, and lifecycle state
    """
    return list_clusters(oci_clients["container_engine"], compartment_id)


@mcp.tool(name="get_oke_cluster")
@mcp_tool_wrapper(
    start_msg="Getting details for OKE cluster {cluster_id}...",
    error_prefix="Error getting OKE cluster details"
)
async def mcp_get_oke_cluster(ctx: Context, cluster_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific OKE cluster.

    Args:
        cluster_id: OCID of the cluster

    Returns:
        Detailed cluster information including:
        - Kubernetes version and available upgrades
        - Cluster endpoints (public/private)
        - Network configuration (VCN, subnets, CIDR blocks)
        - Add-ons configuration (dashboard, tiller)
        - Image policy settings
        - Cluster metadata and options
    """
    return get_cluster(oci_clients["container_engine"], cluster_id)


@mcp.tool(name="list_oke_node_pools")
@mcp_tool_wrapper(
    start_msg="Listing node pools in compartment {compartment_id}...",
    error_prefix="Error listing node pools"
)
async def mcp_list_oke_node_pools(
    ctx: Context,
    compartment_id: str,
    cluster_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List all node pools in a compartment, optionally filtered by cluster.

    Args:
        compartment_id: OCID of the compartment
        cluster_id: Optional OCID of the cluster to filter by

    Returns:
        List of node pools with their details including:
        - Node shape and image information
        - Kubernetes version
        - Placement configuration (ADs, subnets)
        - Node count per subnet
        - Lifecycle state
    """
    return list_node_pools(oci_clients["container_engine"], compartment_id, cluster_id)


@mcp.tool(name="get_oke_node_pool")
@mcp_tool_wrapper(
    start_msg="Getting details for node pool {node_pool_id}...",
    error_prefix="Error getting node pool details"
)
async def mcp_get_oke_node_pool(ctx: Context, node_pool_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific node pool.

    Args:
        node_pool_id: OCID of the node pool

    Returns:
        Detailed node pool information including:
        - Node configuration (shape, image, SSH keys)
        - Individual node details (IPs, state, fault domains)
        - Placement configuration across ADs
        - Node eviction settings
        - Node pool cycling details
        - Initial node labels
        - Security settings (NSGs, encryption)
    """
    return get_node_pool(oci_clients["container_engine"], node_pool_id)


@mcp.tool(name="get_oke_cluster_kubeconfig")
@mcp_tool_wrapper(
    start_msg="Getting kubeconfig for cluster {cluster_id}...",
    error_prefix="Error getting cluster kubeconfig"
)
async def mcp_get_oke_cluster_kubeconfig(ctx: Context, cluster_id: str) -> Dict[str, Any]:
    """
    Get the kubeconfig file content for accessing an OKE cluster.

    Args:
        cluster_id: OCID of the cluster

    Returns:
        Kubeconfig content in YAML format that can be saved to ~/.kube/config
        or used with kubectl --kubeconfig flag
    """
    return get_cluster_kubeconfig(oci_clients["container_engine"], cluster_id)


@mcp.tool(name="list_oke_work_requests")
@mcp_tool_wrapper(
    start_msg="Listing OKE work requests in compartment {compartment_id}...",
    error_prefix="Error listing OKE work requests"
)
async def mcp_list_oke_work_requests(
    ctx: Context,
    compartment_id: str,
    resource_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List work requests (async operations) for OKE resources in a compartment.

    Args:
        compartment_id: OCID of the compartment
        resource_id: Optional OCID of a specific resource (cluster or node pool) to filter by

    Returns:
        List of work requests with their details including:
        - Operation type (create, update, delete, etc.)
        - Status and completion percentage
        - Associated resources
        - Timestamps (accepted, started, finished)
    """
    return list_work_requests(oci_clients["container_engine"], compartment_id, resource_id)


@mcp.tool(name="get_oke_work_request")
@mcp_tool_wrapper(
    start_msg="Getting details for work request {work_request_id}...",
    error_prefix="Error getting work request details"
)
async def mcp_get_oke_work_request(ctx: Context, work_request_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific OKE work request.

    Args:
        work_request_id: OCID of the work request

    Returns:
        Detailed work request information including:
        - Operation type and status
        - Completion percentage
        - Associated resources and actions
        - Timing information
    """
    return get_work_request(oci_clients["container_engine"], work_request_id)


def main() -> None:
    """Run the MCP server for OCI."""
    global oci_clients, current_profile

    parser = argparse.ArgumentParser(
        description="A Model Context Protocol (MCP) server for Oracle Cloud Infrastructure"
    )

    parser.add_argument("--profile", default=None,
                        help="OCI profile to use (optional - can be set dynamically using set_oci_profile tool)")
    parser.add_argument("--sse", action="store_true", help="Use SSE transport")
    parser.add_argument("--port", type=int, default=DEFAULT_SSE_PORT, help="Port for SSE transport")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Set log level based on debug flag
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    # Initialize OCI clients if profile provided
    if args.profile:
        try:
            logger.info(f"Initializing OCI clients with profile: {args.profile}")
            oci_clients = init_oci_clients(args.profile)
            current_profile = args.profile
            logger.info(f"OCI clients initialized successfully with profile: {args.profile}")
        except Exception as e:
            logger.error(f"Failed to initialize OCI clients with profile '{args.profile}': {e}")
            logger.info("Server will start without an active profile. Use 'set_oci_profile' tool to activate one.")
    else:
        logger.info("Starting OCI MCP Server without a default profile")
        logger.info("Use 'list_oci_profiles' to see available profiles and 'set_oci_profile' to activate one")

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
