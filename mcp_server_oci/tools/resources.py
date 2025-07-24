"""
Tools for managing additional OCI resources.
"""

import logging
from typing import Dict, List, Any, Optional

import oci

logger = logging.getLogger(__name__)


def list_availability_domains(identity_client: oci.identity.IdentityClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all availability domains in a compartment.
    
    Args:
        identity_client: OCI Identity client
        compartment_id: OCID of the compartment
        
    Returns:
        List of availability domains with their details
    """
    try:
        ads_response = identity_client.list_availability_domains(compartment_id)
        
        ads = []
        for ad in ads_response.data:
            ads.append({
                "name": ad.name,
                "id": ad.id,
                "compartment_id": ad.compartment_id,
            })
        
        logger.info(f"Found {len(ads)} availability domains in compartment {compartment_id}")
        return ads
        
    except Exception as e:
        logger.exception(f"Error listing availability domains: {e}")
        raise


def list_fault_domains(identity_client: oci.identity.IdentityClient, compartment_id: str, 
                       availability_domain: str) -> List[Dict[str, Any]]:
    """
    List all fault domains in an availability domain.
    
    Args:
        identity_client: OCI Identity client
        compartment_id: OCID of the compartment
        availability_domain: Name of the availability domain
        
    Returns:
        List of fault domains with their details
    """
    try:
        fds_response = identity_client.list_fault_domains(
            compartment_id=compartment_id,
            availability_domain=availability_domain
        )
        
        fds = []
        for fd in fds_response.data:
            fds.append({
                "name": fd.name,
                "id": fd.id,
                "compartment_id": fd.compartment_id,
                "availability_domain": fd.availability_domain,
            })
        
        logger.info(f"Found {len(fds)} fault domains in availability domain {availability_domain}")
        return fds
        
    except Exception as e:
        logger.exception(f"Error listing fault domains: {e}")
        raise


def list_images(compute_client: oci.core.ComputeClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all images in a compartment.
    
    Args:
        compute_client: OCI Compute client
        compartment_id: OCID of the compartment
        
    Returns:
        List of images with their details
    """
    try:
        images_response = oci.pagination.list_call_get_all_results(
            compute_client.list_images,
            compartment_id
        )
        
        images = []
        for image in images_response.data:
            images.append({
                "id": image.id,
                "display_name": image.display_name,
                "compartment_id": image.compartment_id,
                "operating_system": image.operating_system,
                "operating_system_version": image.operating_system_version,
                "lifecycle_state": image.lifecycle_state,
                "time_created": str(image.time_created),
                "size_in_mbs": image.size_in_mbs,
                "base_image_id": image.base_image_id,
                "create_image_allowed": image.create_image_allowed,
                "listing_type": image.listing_type,
            })
        
        logger.info(f"Found {len(images)} images in compartment {compartment_id}")
        return images
        
    except Exception as e:
        logger.exception(f"Error listing images: {e}")
        raise


def get_image(compute_client: oci.core.ComputeClient, image_id: str) -> Dict[str, Any]:
    """
    Get details of a specific image.
    
    Args:
        compute_client: OCI Compute client
        image_id: OCID of the image
        
    Returns:
        Details of the image
    """
    try:
        image = compute_client.get_image(image_id).data
        
        image_details = {
            "id": image.id,
            "display_name": image.display_name,
            "compartment_id": image.compartment_id,
            "operating_system": image.operating_system,
            "operating_system_version": image.operating_system_version,
            "lifecycle_state": image.lifecycle_state,
            "time_created": str(image.time_created),
            "size_in_mbs": image.size_in_mbs,
            "base_image_id": image.base_image_id,
            "create_image_allowed": image.create_image_allowed,
            "listing_type": image.listing_type,
            "launch_mode": image.launch_mode,
            "launch_options": {
                "boot_volume_type": image.launch_options.boot_volume_type if image.launch_options else None,
                "firmware": image.launch_options.firmware if image.launch_options else None,
                "network_type": image.launch_options.network_type if image.launch_options else None,
                "remote_data_volume_type": image.launch_options.remote_data_volume_type if image.launch_options else None,
                "is_pv_encryption_in_transit_enabled": image.launch_options.is_pv_encryption_in_transit_enabled if image.launch_options else None,
                "is_consistent_volume_naming_enabled": image.launch_options.is_consistent_volume_naming_enabled if image.launch_options else None,
            } if image.launch_options else None,
        }
        
        logger.info(f"Retrieved details for image {image_id}")
        return image_details
        
    except Exception as e:
        logger.exception(f"Error getting image details: {e}")
        raise


def list_shapes(compute_client: oci.core.ComputeClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all shapes available in a compartment.
    
    Args:
        compute_client: OCI Compute client
        compartment_id: OCID of the compartment
        
    Returns:
        List of shapes with their details
    """
    try:
        shapes_response = oci.pagination.list_call_get_all_results(
            compute_client.list_shapes,
            compartment_id
        )
        
        shapes = []
        for shape in shapes_response.data:
            shapes.append({
                "shape": shape.shape,
                "processor_description": shape.processor_description,
                "ocpus": shape.ocpus,
                "memory_in_gbs": shape.memory_in_gbs,
                "networking_bandwidth_in_gbps": shape.networking_bandwidth_in_gbps,
                "max_vnic_attachments": shape.max_vnic_attachments,
                "gpus": shape.gpus,
                "gpu_description": shape.gpu_description,
                "local_disks": shape.local_disks,
                "local_disks_total_size_in_gbs": shape.local_disks_total_size_in_gbs,
                "local_disk_description": shape.local_disk_description,
                "rdma_ports": shape.rdma_ports,
                "rdma_bandwidth_in_gbps": shape.rdma_bandwidth_in_gbps,
                "is_live_migration_supported": shape.is_live_migration_supported,
                "ocpu_options": {
                    "min": shape.ocpu_options.min if shape.ocpu_options else None,
                    "max": shape.ocpu_options.max if shape.ocpu_options else None,
                } if shape.ocpu_options else None,
                "memory_options": {
                    "min_in_g_bs": shape.memory_options.min_in_g_bs if shape.memory_options else None,
                    "max_in_g_bs": shape.memory_options.max_in_g_bs if shape.memory_options else None,
                    "default_per_ocpu_in_g_bs": shape.memory_options.default_per_ocpu_in_g_bs if shape.memory_options else None,
                    "min_per_ocpu_in_g_bs": shape.memory_options.min_per_ocpu_in_g_bs if shape.memory_options else None,
                    "max_per_ocpu_in_g_bs": shape.memory_options.max_per_ocpu_in_g_bs if shape.memory_options else None,
                } if shape.memory_options else None,
                "networking_bandwidth_options": {
                    "min_in_gbps": shape.networking_bandwidth_options.min_in_gbps if shape.networking_bandwidth_options else None,
                    "max_in_gbps": shape.networking_bandwidth_options.max_in_gbps if shape.networking_bandwidth_options else None,
                    "default_per_ocpu_in_gbps": shape.networking_bandwidth_options.default_per_ocpu_in_gbps if shape.networking_bandwidth_options else None,
                } if shape.networking_bandwidth_options else None,
            })
        
        logger.info(f"Found {len(shapes)} shapes in compartment {compartment_id}")
        return shapes
        
    except Exception as e:
        logger.exception(f"Error listing shapes: {e}")
        raise


def get_namespace(object_storage_client: oci.object_storage.ObjectStorageClient) -> Dict[str, Any]:
    """
    Get the Object Storage namespace for the tenancy.
    
    Args:
        object_storage_client: OCI ObjectStorage client
        
    Returns:
        Object Storage namespace details
    """
    try:
        namespace = object_storage_client.get_namespace().data
        
        namespace_details = {
            "namespace": namespace,
        }
        
        logger.info(f"Retrieved Object Storage namespace: {namespace}")
        return namespace_details
        
    except Exception as e:
        logger.exception(f"Error getting namespace: {e}")
        raise


def list_regions(identity_client: oci.identity.IdentityClient) -> List[Dict[str, Any]]:
    """
    List all available regions.
    
    Args:
        identity_client: OCI Identity client
        
    Returns:
        List of regions with their details
    """
    try:
        regions_response = identity_client.list_regions()
        
        regions = []
        for region in regions_response.data:
            regions.append({
                "key": region.key,
                "name": region.name,
            })
        
        logger.info(f"Found {len(regions)} regions")
        return regions
        
    except Exception as e:
        logger.exception(f"Error listing regions: {e}")
        raise


def get_tenancy_info(identity_client: oci.identity.IdentityClient, tenancy_id: str) -> Dict[str, Any]:
    """
    Get tenancy information.
    
    Args:
        identity_client: OCI Identity client
        tenancy_id: OCID of the tenancy
        
    Returns:
        Tenancy details
    """
    try:
        tenancy = identity_client.get_tenancy(tenancy_id).data
        
        tenancy_details = {
            "id": tenancy.id,
            "name": tenancy.name,
            "description": tenancy.description,
            "home_region_key": tenancy.home_region_key,
            "upi_idcs_compatibility_layer_endpoint": tenancy.upi_idcs_compatibility_layer_endpoint,
        }
        
        logger.info(f"Retrieved tenancy details for {tenancy_id}")
        return tenancy_details
        
    except Exception as e:
        logger.exception(f"Error getting tenancy details: {e}")
        raise
