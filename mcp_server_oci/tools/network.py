"""
Tools for managing OCI network resources.
"""

import logging
from typing import Dict, List, Any, Optional

import oci

logger = logging.getLogger(__name__)


def list_vcns(network_client: oci.core.VirtualNetworkClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all Virtual Cloud Networks (VCNs) in a compartment.
    
    Args:
        network_client: OCI VirtualNetwork client
        compartment_id: OCID of the compartment
        
    Returns:
        List of VCNs with their details
    """
    try:
        # List all VCNs in the compartment
        vcns_response = oci.pagination.list_call_get_all_results(
            network_client.list_vcns,
            compartment_id,
        )
        
        # Format the VCNs
        vcns = []
        for vcn in vcns_response.data:
            vcns.append({
                "id": vcn.id,
                "name": vcn.display_name,
                "lifecycle_state": vcn.lifecycle_state,
                "cidr_block": vcn.cidr_block,
                "time_created": str(vcn.time_created),
                "compartment_id": vcn.compartment_id,
                "dns_label": vcn.dns_label,
                "default_dhcp_options_id": vcn.default_dhcp_options_id,
                "default_route_table_id": vcn.default_route_table_id,
                "default_security_list_id": vcn.default_security_list_id,
            })
        
        logger.info(f"Found {len(vcns)} VCNs in compartment {compartment_id}")
        return vcns
        
    except Exception as e:
        logger.exception(f"Error listing VCNs: {e}")
        raise


def get_vcn(network_client: oci.core.VirtualNetworkClient, vcn_id: str) -> Dict[str, Any]:
    """
    Get details of a specific VCN.
    
    Args:
        network_client: OCI VirtualNetwork client
        vcn_id: OCID of the VCN
        
    Returns:
        Details of the VCN
    """
    try:
        # Get the VCN details
        vcn = network_client.get_vcn(vcn_id).data
        
        # Format the VCN details
        vcn_details = {
            "id": vcn.id,
            "name": vcn.display_name,
            "lifecycle_state": vcn.lifecycle_state,
            "cidr_block": vcn.cidr_block,
            "time_created": str(vcn.time_created),
            "compartment_id": vcn.compartment_id,
            "dns_label": vcn.dns_label,
            "default_dhcp_options_id": vcn.default_dhcp_options_id,
            "default_route_table_id": vcn.default_route_table_id,
            "default_security_list_id": vcn.default_security_list_id,
        }
        
        # Add IPv6 CIDR blocks if available
        if hasattr(vcn, 'ipv6_cidr_blocks') and vcn.ipv6_cidr_blocks:
            vcn_details["ipv6_cidr_blocks"] = vcn.ipv6_cidr_blocks
        
        logger.info(f"Retrieved details for VCN {vcn_id}")
        return vcn_details
        
    except Exception as e:
        logger.exception(f"Error getting VCN details: {e}")
        raise


def list_subnets(network_client: oci.core.VirtualNetworkClient, compartment_id: str, vcn_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all subnets in a compartment, optionally filtered by VCN.
    
    Args:
        network_client: OCI VirtualNetwork client
        compartment_id: OCID of the compartment
        vcn_id: Optional OCID of the VCN to filter by
        
    Returns:
        List of subnets with their details
    """
    try:
        # List all subnets in the compartment, optionally filtered by VCN
        if vcn_id:
            subnets_response = oci.pagination.list_call_get_all_results(
                network_client.list_subnets,
                compartment_id,
                vcn_id=vcn_id
            )
            logger.info(f"Listing subnets in compartment {compartment_id} and VCN {vcn_id}")
        else:
            # If no VCN ID provided, we need to list all subnets in all VCNs
            vcns = list_vcns(network_client, compartment_id)
            
            subnets_response_data = []
            for vcn in vcns:
                vcn_subnets = oci.pagination.list_call_get_all_results(
                    network_client.list_subnets,
                    compartment_id,
                    vcn_id=vcn["id"]
                ).data
                subnets_response_data.extend(vcn_subnets)
                
            # Create a custom response object to match the structure returned by list_call_get_all_results
            class CustomResponse:
                def __init__(self, data):
                    self.data = data
                    
            subnets_response = CustomResponse(subnets_response_data)
            logger.info(f"Listing all subnets in compartment {compartment_id} across all VCNs")
        
        # Format the subnets
        subnets = []
        for subnet in subnets_response.data:
            subnet_details = {
                "id": subnet.id,
                "name": subnet.display_name,
                "lifecycle_state": subnet.lifecycle_state,
                "cidr_block": subnet.cidr_block,
                "availability_domain": subnet.availability_domain,
                "compartment_id": subnet.compartment_id,
                "vcn_id": subnet.vcn_id,
                "route_table_id": subnet.route_table_id,
                "dhcp_options_id": subnet.dhcp_options_id,
                "security_list_ids": subnet.security_list_ids,
                "time_created": str(subnet.time_created),
                "prohibit_public_ip_on_vnic": subnet.prohibit_public_ip_on_vnic,
            }
            
            # Add IPv6 CIDR block if available
            if hasattr(subnet, 'ipv6_cidr_block') and subnet.ipv6_cidr_block:
                subnet_details["ipv6_cidr_block"] = subnet.ipv6_cidr_block
            
            subnets.append(subnet_details)
        
        logger.info(f"Found {len(subnets)} subnets")
        return subnets
        
    except Exception as e:
        logger.exception(f"Error listing subnets: {e}")
        raise


def get_subnet(network_client: oci.core.VirtualNetworkClient, subnet_id: str) -> Dict[str, Any]:
    """
    Get details of a specific subnet.
    
    Args:
        network_client: OCI VirtualNetwork client
        subnet_id: OCID of the subnet
        
    Returns:
        Details of the subnet
    """
    try:
        # Get the subnet details
        subnet = network_client.get_subnet(subnet_id).data
        
        # Format the subnet details
        subnet_details = {
            "id": subnet.id,
            "name": subnet.display_name,
            "lifecycle_state": subnet.lifecycle_state,
            "cidr_block": subnet.cidr_block,
            "availability_domain": subnet.availability_domain,
            "compartment_id": subnet.compartment_id,
            "vcn_id": subnet.vcn_id,
            "route_table_id": subnet.route_table_id,
            "dhcp_options_id": subnet.dhcp_options_id,
            "security_list_ids": subnet.security_list_ids,
            "time_created": str(subnet.time_created),
            "prohibit_public_ip_on_vnic": subnet.prohibit_public_ip_on_vnic,
        }
        
        # Add IPv6 CIDR block if available
        if hasattr(subnet, 'ipv6_cidr_block') and subnet.ipv6_cidr_block:
            subnet_details["ipv6_cidr_block"] = subnet.ipv6_cidr_block
        
        logger.info(f"Retrieved details for subnet {subnet_id}")
        return subnet_details
        
    except Exception as e:
        logger.exception(f"Error getting subnet details: {e}")
        raise


def list_vnics(compute_client: oci.core.ComputeClient, network_client: oci.core.VirtualNetworkClient, 
               compartment_id: str, instance_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all VNICs in a compartment, optionally filtered by instance.
    
    Args:
        compute_client: OCI Compute client
        network_client: OCI VirtualNetwork client
        compartment_id: OCID of the compartment
        instance_id: Optional OCID of the instance to filter by
        
    Returns:
        List of VNICs with their details
    """
    try:
        # Get VNIC attachments
        if instance_id:
            vnic_attachments = oci.pagination.list_call_get_all_results(
                compute_client.list_vnic_attachments,
                compartment_id,
                instance_id=instance_id
            ).data
            logger.info(f"Listing VNICs for instance {instance_id} in compartment {compartment_id}")
        else:
            vnic_attachments = oci.pagination.list_call_get_all_results(
                compute_client.list_vnic_attachments,
                compartment_id
            ).data
            logger.info(f"Listing all VNICs in compartment {compartment_id}")
        
        # Get VNIC details
        vnics = []
        for attachment in vnic_attachments:
            try:
                vnic = network_client.get_vnic(attachment.vnic_id).data
                
                vnic_details = {
                    "id": vnic.id,
                    "display_name": vnic.display_name,
                    "hostname_label": vnic.hostname_label,
                    "is_primary": vnic.is_primary,
                    "lifecycle_state": vnic.lifecycle_state,
                    "mac_address": vnic.mac_address,
                    "private_ip": vnic.private_ip,
                    "public_ip": vnic.public_ip,
                    "subnet_id": vnic.subnet_id,
                    "time_created": str(vnic.time_created),
                    "compartment_id": vnic.compartment_id,
                    "attachment_id": attachment.id,
                    "instance_id": attachment.instance_id,
                    "attachment_lifecycle_state": attachment.lifecycle_state,
                }
                
                # Add IPv6 addresses if available
                if hasattr(vnic, 'ipv6_addresses') and vnic.ipv6_addresses:
                    vnic_details["ipv6_addresses"] = vnic.ipv6_addresses
                
                vnics.append(vnic_details)
            except Exception as vnic_error:
                logger.warning(f"Error getting VNIC details for attachment {attachment.id}: {vnic_error}")
                # Add basic info from attachment
                vnics.append({
                    "attachment_id": attachment.id,
                    "vnic_id": attachment.vnic_id,
                    "instance_id": attachment.instance_id,
                    "lifecycle_state": attachment.lifecycle_state,
                    "time_created": str(attachment.time_created),
                    "compartment_id": attachment.compartment_id,
                    "error": str(vnic_error)
                })
        
        logger.info(f"Found {len(vnics)} VNICs")
        return vnics
        
    except Exception as e:
        logger.exception(f"Error listing VNICs: {e}")
        raise


def get_vnic(network_client: oci.core.VirtualNetworkClient, vnic_id: str) -> Dict[str, Any]:
    """
    Get details of a specific VNIC.
    
    Args:
        network_client: OCI VirtualNetwork client
        vnic_id: OCID of the VNIC
        
    Returns:
        Details of the VNIC
    """
    try:
        # Get the VNIC details
        vnic = network_client.get_vnic(vnic_id).data
        
        # Format the VNIC details
        vnic_details = {
            "id": vnic.id,
            "display_name": vnic.display_name,
            "hostname_label": vnic.hostname_label,
            "is_primary": vnic.is_primary,
            "lifecycle_state": vnic.lifecycle_state,
            "mac_address": vnic.mac_address,
            "private_ip": vnic.private_ip,
            "public_ip": vnic.public_ip,
            "subnet_id": vnic.subnet_id,
            "time_created": str(vnic.time_created),
            "compartment_id": vnic.compartment_id,
        }
        
        # Add IPv6 addresses if available
        if hasattr(vnic, 'ipv6_addresses') and vnic.ipv6_addresses:
            vnic_details["ipv6_addresses"] = vnic.ipv6_addresses
        
        logger.info(f"Retrieved details for VNIC {vnic_id}")
        return vnic_details
        
    except Exception as e:
        logger.exception(f"Error getting VNIC details: {e}")
        raise
