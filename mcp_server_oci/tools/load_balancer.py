"""
Tools for managing OCI Load Balancer resources.
"""

import logging
from typing import Dict, List, Any, Optional

import oci

logger = logging.getLogger(__name__)


def list_load_balancers(load_balancer_client: oci.load_balancer.LoadBalancerClient, 
                        compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all load balancers in a compartment.
    
    Args:
        load_balancer_client: OCI LoadBalancer client
        compartment_id: OCID of the compartment
        
    Returns:
        List of load balancers with their details
    """
    try:
        load_balancers_response = oci.pagination.list_call_get_all_results(
            load_balancer_client.list_load_balancers,
            compartment_id
        )
        
        load_balancers = []
        for lb in load_balancers_response.data:
            load_balancers.append({
                "id": lb.id,
                "display_name": lb.display_name,
                "compartment_id": lb.compartment_id,
                "lifecycle_state": lb.lifecycle_state,
                "time_created": str(lb.time_created),
                "shape_name": lb.shape_name,
                "is_private": lb.is_private,
                "ip_addresses": [
                    {
                        "ip_address": ip.ip_address,
                        "is_public": ip.is_public,
                    }
                    for ip in lb.ip_addresses
                ] if lb.ip_addresses else [],
                "subnet_ids": lb.subnet_ids,
                "network_security_group_ids": lb.network_security_group_ids,
            })
        
        logger.info(f"Found {len(load_balancers)} load balancers in compartment {compartment_id}")
        return load_balancers
        
    except Exception as e:
        logger.exception(f"Error listing load balancers: {e}")
        raise


def get_load_balancer(load_balancer_client: oci.load_balancer.LoadBalancerClient, 
                      load_balancer_id: str) -> Dict[str, Any]:
    """
    Get details of a specific load balancer.
    
    Args:
        load_balancer_client: OCI LoadBalancer client
        load_balancer_id: OCID of the load balancer
        
    Returns:
        Details of the load balancer
    """
    try:
        lb = load_balancer_client.get_load_balancer(load_balancer_id).data
        
        # Format backend sets
        backend_sets = {}
        if lb.backend_sets:
            for name, backend_set in lb.backend_sets.items():
                backend_sets[name] = {
                    "name": name,
                    "policy": backend_set.policy,
                    "backends": [
                        {
                            "ip_address": backend.ip_address,
                            "port": backend.port,
                            "weight": backend.weight,
                            "drain": backend.drain,
                            "backup": backend.backup,
                            "offline": backend.offline,
                        }
                        for backend in backend_set.backends
                    ] if backend_set.backends else [],
                    "health_checker": {
                        "protocol": backend_set.health_checker.protocol,
                        "url_path": backend_set.health_checker.url_path,
                        "port": backend_set.health_checker.port,
                        "return_code": backend_set.health_checker.return_code,
                        "retries": backend_set.health_checker.retries,
                        "timeout_in_millis": backend_set.health_checker.timeout_in_millis,
                        "interval_in_millis": backend_set.health_checker.interval_in_millis,
                        "response_body_regex": backend_set.health_checker.response_body_regex,
                    } if backend_set.health_checker else None,
                }
        
        # Format listeners
        listeners = {}
        if lb.listeners:
            for name, listener in lb.listeners.items():
                listeners[name] = {
                    "name": name,
                    "default_backend_set_name": listener.default_backend_set_name,
                    "port": listener.port,
                    "protocol": listener.protocol,
                    "hostname_names": listener.hostname_names,
                    "path_route_set_name": listener.path_route_set_name,
                    "ssl_configuration": {
                        "certificate_name": listener.ssl_configuration.certificate_name if listener.ssl_configuration else None,
                        "verify_peer_certificate": listener.ssl_configuration.verify_peer_certificate if listener.ssl_configuration else None,
                        "verify_depth": listener.ssl_configuration.verify_depth if listener.ssl_configuration else None,
                    } if listener.ssl_configuration else None,
                    "connection_configuration": {
                        "idle_timeout": listener.connection_configuration.idle_timeout if listener.connection_configuration else None,
                        "backend_tcp_proxy_protocol_version": listener.connection_configuration.backend_tcp_proxy_protocol_version if listener.connection_configuration else None,
                    } if listener.connection_configuration else None,
                }
        
        lb_details = {
            "id": lb.id,
            "display_name": lb.display_name,
            "compartment_id": lb.compartment_id,
            "lifecycle_state": lb.lifecycle_state,
            "time_created": str(lb.time_created),
            "shape_name": lb.shape_name,
            "is_private": lb.is_private,
            "ip_addresses": [
                {
                    "ip_address": ip.ip_address,
                    "is_public": ip.is_public,
                }
                for ip in lb.ip_addresses
            ] if lb.ip_addresses else [],
            "subnet_ids": lb.subnet_ids,
            "network_security_group_ids": lb.network_security_group_ids,
            "backend_sets": backend_sets,
            "listeners": listeners,
            "certificates": dict(lb.certificates) if lb.certificates else {},
            "path_route_sets": dict(lb.path_route_sets) if lb.path_route_sets else {},
            "hostnames": dict(lb.hostnames) if lb.hostnames else {},
        }
        
        logger.info(f"Retrieved details for load balancer {load_balancer_id}")
        return lb_details
        
    except Exception as e:
        logger.exception(f"Error getting load balancer details: {e}")
        raise


def list_network_load_balancers(network_load_balancer_client: oci.network_load_balancer.NetworkLoadBalancerClient, 
                                compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all network load balancers in a compartment.
    
    Args:
        network_load_balancer_client: OCI NetworkLoadBalancer client
        compartment_id: OCID of the compartment
        
    Returns:
        List of network load balancers with their details
    """
    try:
        nlbs_response = oci.pagination.list_call_get_all_results(
            network_load_balancer_client.list_network_load_balancers,
            compartment_id
        )
        
        nlbs = []
        for nlb in nlbs_response.data:
            nlbs.append({
                "id": nlb.id,
                "display_name": nlb.display_name,
                "compartment_id": nlb.compartment_id,
                "lifecycle_state": nlb.lifecycle_state,
                "time_created": str(nlb.time_created),
                "is_private": nlb.is_private,
                "ip_addresses": [
                    {
                        "ip_address": ip.ip_address,
                        "is_public": ip.is_public,
                        "ip_version": ip.ip_version,
                    }
                    for ip in nlb.ip_addresses
                ] if nlb.ip_addresses else [],
                "subnet_id": nlb.subnet_id,
                "network_security_group_ids": nlb.network_security_group_ids,
                "is_preserve_source_destination": nlb.is_preserve_source_destination,
            })
        
        logger.info(f"Found {len(nlbs)} network load balancers in compartment {compartment_id}")
        return nlbs
        
    except Exception as e:
        logger.exception(f"Error listing network load balancers: {e}")
        raise


def get_network_load_balancer(network_load_balancer_client: oci.network_load_balancer.NetworkLoadBalancerClient, 
                               network_load_balancer_id: str) -> Dict[str, Any]:
    """
    Get details of a specific network load balancer.
    
    Args:
        network_load_balancer_client: OCI NetworkLoadBalancer client
        network_load_balancer_id: OCID of the network load balancer
        
    Returns:
        Details of the network load balancer
    """
    try:
        nlb = network_load_balancer_client.get_network_load_balancer(network_load_balancer_id).data
        
        # Format backend sets
        backend_sets = {}
        if nlb.backend_sets:
            for name, backend_set in nlb.backend_sets.items():
                backend_sets[name] = {
                    "name": name,
                    "policy": backend_set.policy,
                    "is_preserve_source": backend_set.is_preserve_source,
                    "backends": [
                        {
                            "ip_address": backend.ip_address,
                            "port": backend.port,
                            "weight": backend.weight,
                            "target_id": backend.target_id,
                            "is_drain": backend.is_drain,
                            "is_backup": backend.is_backup,
                            "is_offline": backend.is_offline,
                        }
                        for backend in backend_set.backends
                    ] if backend_set.backends else [],
                    "health_checker": {
                        "protocol": backend_set.health_checker.protocol,
                        "port": backend_set.health_checker.port,
                        "url_path": backend_set.health_checker.url_path,
                        "return_code": backend_set.health_checker.return_code,
                        "retries": backend_set.health_checker.retries,
                        "timeout_in_millis": backend_set.health_checker.timeout_in_millis,
                        "interval_in_millis": backend_set.health_checker.interval_in_millis,
                        "request_data": backend_set.health_checker.request_data,
                        "response_data": backend_set.health_checker.response_data,
                    } if backend_set.health_checker else None,
                }
        
        # Format listeners
        listeners = {}
        if nlb.listeners:
            for name, listener in nlb.listeners.items():
                listeners[name] = {
                    "name": name,
                    "default_backend_set_name": listener.default_backend_set_name,
                    "port": listener.port,
                    "protocol": listener.protocol,
                    "ip_version": listener.ip_version,
                }
        
        nlb_details = {
            "id": nlb.id,
            "display_name": nlb.display_name,
            "compartment_id": nlb.compartment_id,
            "lifecycle_state": nlb.lifecycle_state,
            "time_created": str(nlb.time_created),
            "is_private": nlb.is_private,
            "ip_addresses": [
                {
                    "ip_address": ip.ip_address,
                    "is_public": ip.is_public,
                    "ip_version": ip.ip_version,
                }
                for ip in nlb.ip_addresses
            ] if nlb.ip_addresses else [],
            "subnet_id": nlb.subnet_id,
            "network_security_group_ids": nlb.network_security_group_ids,
            "is_preserve_source_destination": nlb.is_preserve_source_destination,
            "backend_sets": backend_sets,
            "listeners": listeners,
        }
        
        logger.info(f"Retrieved details for network load balancer {network_load_balancer_id}")
        return nlb_details
        
    except Exception as e:
        logger.exception(f"Error getting network load balancer details: {e}")
        raise
