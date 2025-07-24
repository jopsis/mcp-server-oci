"""
Tools for managing OCI Security resources.
"""

import logging
from typing import Dict, List, Any, Optional

import oci

logger = logging.getLogger(__name__)


def list_security_lists(network_client: oci.core.VirtualNetworkClient, compartment_id: str, 
                        vcn_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all security lists in a compartment, optionally filtered by VCN.
    
    Args:
        network_client: OCI VirtualNetwork client
        compartment_id: OCID of the compartment
        vcn_id: Optional OCID of the VCN to filter by
        
    Returns:
        List of security lists with their details
    """
    try:
        security_lists_response = oci.pagination.list_call_get_all_results(
            network_client.list_security_lists,
            compartment_id,
            vcn_id=vcn_id
        )
        
        security_lists = []
        for security_list in security_lists_response.data:
            security_lists.append({
                "id": security_list.id,
                "display_name": security_list.display_name,
                "compartment_id": security_list.compartment_id,
                "vcn_id": security_list.vcn_id,
                "lifecycle_state": security_list.lifecycle_state,
                "time_created": str(security_list.time_created),
                "ingress_security_rules_count": len(security_list.ingress_security_rules) if security_list.ingress_security_rules else 0,
                "egress_security_rules_count": len(security_list.egress_security_rules) if security_list.egress_security_rules else 0,
            })
        
        logger.info(f"Found {len(security_lists)} security lists in compartment {compartment_id}")
        return security_lists
        
    except Exception as e:
        logger.exception(f"Error listing security lists: {e}")
        raise


def get_security_list(network_client: oci.core.VirtualNetworkClient, security_list_id: str) -> Dict[str, Any]:
    """
    Get details of a specific security list.
    
    Args:
        network_client: OCI VirtualNetwork client
        security_list_id: OCID of the security list
        
    Returns:
        Details of the security list
    """
    try:
        security_list = network_client.get_security_list(security_list_id).data
        
        # Format ingress rules
        ingress_rules = []
        if security_list.ingress_security_rules:
            for rule in security_list.ingress_security_rules:
                ingress_rules.append({
                    "protocol": rule.protocol,
                    "source": rule.source,
                    "source_type": rule.source_type,
                    "is_stateless": rule.is_stateless,
                    "description": rule.description,
                    "tcp_options": {
                        "destination_port_range": {
                            "min": rule.tcp_options.destination_port_range.min if rule.tcp_options and rule.tcp_options.destination_port_range else None,
                            "max": rule.tcp_options.destination_port_range.max if rule.tcp_options and rule.tcp_options.destination_port_range else None,
                        } if rule.tcp_options and rule.tcp_options.destination_port_range else None,
                        "source_port_range": {
                            "min": rule.tcp_options.source_port_range.min if rule.tcp_options and rule.tcp_options.source_port_range else None,
                            "max": rule.tcp_options.source_port_range.max if rule.tcp_options and rule.tcp_options.source_port_range else None,
                        } if rule.tcp_options and rule.tcp_options.source_port_range else None,
                    } if rule.tcp_options else None,
                    "udp_options": {
                        "destination_port_range": {
                            "min": rule.udp_options.destination_port_range.min if rule.udp_options and rule.udp_options.destination_port_range else None,
                            "max": rule.udp_options.destination_port_range.max if rule.udp_options and rule.udp_options.destination_port_range else None,
                        } if rule.udp_options and rule.udp_options.destination_port_range else None,
                        "source_port_range": {
                            "min": rule.udp_options.source_port_range.min if rule.udp_options and rule.udp_options.source_port_range else None,
                            "max": rule.udp_options.source_port_range.max if rule.udp_options and rule.udp_options.source_port_range else None,
                        } if rule.udp_options and rule.udp_options.source_port_range else None,
                    } if rule.udp_options else None,
                    "icmp_options": {
                        "type": rule.icmp_options.type if rule.icmp_options else None,
                        "code": rule.icmp_options.code if rule.icmp_options else None,
                    } if rule.icmp_options else None,
                })
        
        # Format egress rules
        egress_rules = []
        if security_list.egress_security_rules:
            for rule in security_list.egress_security_rules:
                egress_rules.append({
                    "protocol": rule.protocol,
                    "destination": rule.destination,
                    "destination_type": rule.destination_type,
                    "is_stateless": rule.is_stateless,
                    "description": rule.description,
                    "tcp_options": {
                        "destination_port_range": {
                            "min": rule.tcp_options.destination_port_range.min if rule.tcp_options and rule.tcp_options.destination_port_range else None,
                            "max": rule.tcp_options.destination_port_range.max if rule.tcp_options and rule.tcp_options.destination_port_range else None,
                        } if rule.tcp_options and rule.tcp_options.destination_port_range else None,
                        "source_port_range": {
                            "min": rule.tcp_options.source_port_range.min if rule.tcp_options and rule.tcp_options.source_port_range else None,
                            "max": rule.tcp_options.source_port_range.max if rule.tcp_options and rule.tcp_options.source_port_range else None,
                        } if rule.tcp_options and rule.tcp_options.source_port_range else None,
                    } if rule.tcp_options else None,
                    "udp_options": {
                        "destination_port_range": {
                            "min": rule.udp_options.destination_port_range.min if rule.udp_options and rule.udp_options.destination_port_range else None,
                            "max": rule.udp_options.destination_port_range.max if rule.udp_options and rule.udp_options.destination_port_range else None,
                        } if rule.udp_options and rule.udp_options.destination_port_range else None,
                        "source_port_range": {
                            "min": rule.udp_options.source_port_range.min if rule.udp_options and rule.udp_options.source_port_range else None,
                            "max": rule.udp_options.source_port_range.max if rule.udp_options and rule.udp_options.source_port_range else None,
                        } if rule.udp_options and rule.udp_options.source_port_range else None,
                    } if rule.udp_options else None,
                    "icmp_options": {
                        "type": rule.icmp_options.type if rule.icmp_options else None,
                        "code": rule.icmp_options.code if rule.icmp_options else None,
                    } if rule.icmp_options else None,
                })
        
        security_list_details = {
            "id": security_list.id,
            "display_name": security_list.display_name,
            "compartment_id": security_list.compartment_id,
            "vcn_id": security_list.vcn_id,
            "lifecycle_state": security_list.lifecycle_state,
            "time_created": str(security_list.time_created),
            "ingress_security_rules": ingress_rules,
            "egress_security_rules": egress_rules,
        }
        
        logger.info(f"Retrieved details for security list {security_list_id}")
        return security_list_details
        
    except Exception as e:
        logger.exception(f"Error getting security list details: {e}")
        raise


def list_network_security_groups(network_client: oci.core.VirtualNetworkClient, compartment_id: str,
                                  vcn_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all network security groups in a compartment, optionally filtered by VCN.
    
    Args:
        network_client: OCI VirtualNetwork client
        compartment_id: OCID of the compartment
        vcn_id: Optional OCID of the VCN to filter by
        
    Returns:
        List of network security groups with their details
    """
    try:
        nsgs_response = oci.pagination.list_call_get_all_results(
            network_client.list_network_security_groups,
            compartment_id,
            vcn_id=vcn_id
        )
        
        nsgs = []
        for nsg in nsgs_response.data:
            nsgs.append({
                "id": nsg.id,
                "display_name": nsg.display_name,
                "compartment_id": nsg.compartment_id,
                "vcn_id": nsg.vcn_id,
                "lifecycle_state": nsg.lifecycle_state,
                "time_created": str(nsg.time_created),
            })
        
        logger.info(f"Found {len(nsgs)} network security groups in compartment {compartment_id}")
        return nsgs
        
    except Exception as e:
        logger.exception(f"Error listing network security groups: {e}")
        raise


def get_network_security_group(network_client: oci.core.VirtualNetworkClient, nsg_id: str) -> Dict[str, Any]:
    """
    Get details of a specific network security group.
    
    Args:
        network_client: OCI VirtualNetwork client
        nsg_id: OCID of the network security group
        
    Returns:
        Details of the network security group
    """
    try:
        nsg = network_client.get_network_security_group(nsg_id).data
        
        nsg_details = {
            "id": nsg.id,
            "display_name": nsg.display_name,
            "compartment_id": nsg.compartment_id,
            "vcn_id": nsg.vcn_id,
            "lifecycle_state": nsg.lifecycle_state,
            "time_created": str(nsg.time_created),
        }
        
        logger.info(f"Retrieved details for network security group {nsg_id}")
        return nsg_details
        
    except Exception as e:
        logger.exception(f"Error getting network security group details: {e}")
        raise


def list_vaults(kms_vault_client: oci.key_management.KmsVaultClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all vaults in a compartment.
    
    Args:
        kms_vault_client: OCI KmsVault client
        compartment_id: OCID of the compartment
        
    Returns:
        List of vaults with their details
    """
    try:
        vaults_response = oci.pagination.list_call_get_all_results(
            kms_vault_client.list_vaults,
            compartment_id
        )
        
        vaults = []
        for vault in vaults_response.data:
            vaults.append({
                "id": vault.id,
                "display_name": vault.display_name,
                "compartment_id": vault.compartment_id,
                "lifecycle_state": vault.lifecycle_state,
                "time_created": str(vault.time_created),
                "vault_type": vault.vault_type,
                "crypto_endpoint": vault.crypto_endpoint,
                "management_endpoint": vault.management_endpoint,
                "is_primary": vault.is_primary,
            })
        
        logger.info(f"Found {len(vaults)} vaults in compartment {compartment_id}")
        return vaults
        
    except Exception as e:
        logger.exception(f"Error listing vaults: {e}")
        raise


def get_vault(kms_vault_client: oci.key_management.KmsVaultClient, vault_id: str) -> Dict[str, Any]:
    """
    Get details of a specific vault.
    
    Args:
        kms_vault_client: OCI KmsVault client
        vault_id: OCID of the vault
        
    Returns:
        Details of the vault
    """
    try:
        vault = kms_vault_client.get_vault(vault_id).data
        
        vault_details = {
            "id": vault.id,
            "display_name": vault.display_name,
            "compartment_id": vault.compartment_id,
            "lifecycle_state": vault.lifecycle_state,
            "time_created": str(vault.time_created),
            "vault_type": vault.vault_type,
            "crypto_endpoint": vault.crypto_endpoint,
            "management_endpoint": vault.management_endpoint,
            "is_primary": vault.is_primary,
            "replica_details": {
                "replication_id": vault.replica_details.replication_id if vault.replica_details else None,
            } if vault.replica_details else None,
        }
        
        logger.info(f"Retrieved details for vault {vault_id}")
        return vault_details
        
    except Exception as e:
        logger.exception(f"Error getting vault details: {e}")
        raise
