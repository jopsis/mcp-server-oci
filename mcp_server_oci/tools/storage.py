"""
Tools for managing OCI Storage resources.
"""

import logging
from typing import Dict, List, Any, Optional

import oci

logger = logging.getLogger(__name__)


def list_buckets(object_storage_client: oci.object_storage.ObjectStorageClient, 
                 compartment_id: str, namespace_name: str) -> List[Dict[str, Any]]:
    """
    List all buckets in a compartment.
    
    Args:
        object_storage_client: OCI ObjectStorage client
        compartment_id: OCID of the compartment
        namespace_name: Object Storage namespace name
        
    Returns:
        List of buckets with their details
    """
    try:
        buckets_response = oci.pagination.list_call_get_all_results(
            object_storage_client.list_buckets,
            namespace_name,
            compartment_id
        )
        
        buckets = []
        for bucket in buckets_response.data:
            buckets.append({
                "name": bucket.name,
                "namespace": bucket.namespace,
                "compartment_id": bucket.compartment_id,
                "created_by": bucket.created_by,
                "time_created": str(bucket.time_created),
                "etag": bucket.etag,
            })
        
        logger.info(f"Found {len(buckets)} buckets in compartment {compartment_id}")
        return buckets
        
    except Exception as e:
        logger.exception(f"Error listing buckets: {e}")
        raise


def get_bucket(object_storage_client: oci.object_storage.ObjectStorageClient, 
               namespace_name: str, bucket_name: str) -> Dict[str, Any]:
    """
    Get details of a specific bucket.
    
    Args:
        object_storage_client: OCI ObjectStorage client
        namespace_name: Object Storage namespace name
        bucket_name: Name of the bucket
        
    Returns:
        Details of the bucket
    """
    try:
        bucket = object_storage_client.get_bucket(namespace_name, bucket_name).data
        
        bucket_details = {
            "name": bucket.name,
            "namespace": bucket.namespace,
            "compartment_id": bucket.compartment_id,
            "created_by": bucket.created_by,
            "time_created": str(bucket.time_created),
            "etag": bucket.etag,
            "public_access_type": bucket.public_access_type,
            "storage_tier": bucket.storage_tier,
            "object_events_enabled": bucket.object_events_enabled,
            "versioning": bucket.versioning,
            "replication_enabled": bucket.replication_enabled,
            "is_read_only": bucket.is_read_only,
            "object_lifecycle_policy_etag": bucket.object_lifecycle_policy_etag,
        }
        
        logger.info(f"Retrieved details for bucket {bucket_name}")
        return bucket_details
        
    except Exception as e:
        logger.exception(f"Error getting bucket details: {e}")
        raise


def list_volumes(block_storage_client: oci.core.BlockstorageClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all block volumes in a compartment.
    
    Args:
        block_storage_client: OCI BlockStorage client
        compartment_id: OCID of the compartment
        
    Returns:
        List of volumes with their details
    """
    try:
        volumes_response = oci.pagination.list_call_get_all_results(
            block_storage_client.list_volumes,
            compartment_id
        )
        
        volumes = []
        for volume in volumes_response.data:
            volumes.append({
                "id": volume.id,
                "display_name": volume.display_name,
                "compartment_id": volume.compartment_id,
                "availability_domain": volume.availability_domain,
                "size_in_mbs": volume.size_in_mbs,
                "size_in_gbs": volume.size_in_gbs,
                "lifecycle_state": volume.lifecycle_state,
                "time_created": str(volume.time_created),
                "volume_group_id": volume.volume_group_id,
                "is_hydrated": volume.is_hydrated,
                "vpus_per_gb": volume.vpus_per_gb,
                "is_auto_tune_enabled": volume.is_auto_tune_enabled,
                "auto_tuned_vpus_per_gb": volume.auto_tuned_vpus_per_gb,
            })
        
        logger.info(f"Found {len(volumes)} volumes in compartment {compartment_id}")
        return volumes
        
    except Exception as e:
        logger.exception(f"Error listing volumes: {e}")
        raise


def get_volume(block_storage_client: oci.core.BlockstorageClient, volume_id: str) -> Dict[str, Any]:
    """
    Get details of a specific volume.
    
    Args:
        block_storage_client: OCI BlockStorage client
        volume_id: OCID of the volume
        
    Returns:
        Details of the volume
    """
    try:
        volume = block_storage_client.get_volume(volume_id).data
        
        volume_details = {
            "id": volume.id,
            "display_name": volume.display_name,
            "compartment_id": volume.compartment_id,
            "availability_domain": volume.availability_domain,
            "size_in_mbs": volume.size_in_mbs,
            "size_in_gbs": volume.size_in_gbs,
            "lifecycle_state": volume.lifecycle_state,
            "time_created": str(volume.time_created),
            "volume_group_id": volume.volume_group_id,
            "is_hydrated": volume.is_hydrated,
            "vpus_per_gb": volume.vpus_per_gb,
            "is_auto_tune_enabled": volume.is_auto_tune_enabled,
            "auto_tuned_vpus_per_gb": volume.auto_tuned_vpus_per_gb,
            "kms_key_id": volume.kms_key_id,
            "source_details": {
                "type": volume.source_details.type if volume.source_details else None,
                "id": volume.source_details.id if volume.source_details else None,
            } if volume.source_details else None,
        }
        
        logger.info(f"Retrieved details for volume {volume_id}")
        return volume_details
        
    except Exception as e:
        logger.exception(f"Error getting volume details: {e}")
        raise


def list_boot_volumes(block_storage_client: oci.core.BlockstorageClient, 
                      availability_domain: str, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all boot volumes in a compartment and availability domain.
    
    Args:
        block_storage_client: OCI BlockStorage client
        availability_domain: Availability domain name
        compartment_id: OCID of the compartment
        
    Returns:
        List of boot volumes with their details
    """
    try:
        boot_volumes_response = oci.pagination.list_call_get_all_results(
            block_storage_client.list_boot_volumes,
            availability_domain,
            compartment_id
        )
        
        boot_volumes = []
        for boot_volume in boot_volumes_response.data:
            boot_volumes.append({
                "id": boot_volume.id,
                "display_name": boot_volume.display_name,
                "compartment_id": boot_volume.compartment_id,
                "availability_domain": boot_volume.availability_domain,
                "size_in_mbs": boot_volume.size_in_mbs,
                "size_in_gbs": boot_volume.size_in_gbs,
                "lifecycle_state": boot_volume.lifecycle_state,
                "time_created": str(boot_volume.time_created),
                "is_hydrated": boot_volume.is_hydrated,
                "vpus_per_gb": boot_volume.vpus_per_gb,
                "is_auto_tune_enabled": boot_volume.is_auto_tune_enabled,
                "auto_tuned_vpus_per_gb": boot_volume.auto_tuned_vpus_per_gb,
            })
        
        logger.info(f"Found {len(boot_volumes)} boot volumes in compartment {compartment_id}")
        return boot_volumes
        
    except Exception as e:
        logger.exception(f"Error listing boot volumes: {e}")
        raise


def get_boot_volume(block_storage_client: oci.core.BlockstorageClient, boot_volume_id: str) -> Dict[str, Any]:
    """
    Get details of a specific boot volume.
    
    Args:
        block_storage_client: OCI BlockStorage client
        boot_volume_id: OCID of the boot volume
        
    Returns:
        Details of the boot volume
    """
    try:
        boot_volume = block_storage_client.get_boot_volume(boot_volume_id).data
        
        boot_volume_details = {
            "id": boot_volume.id,
            "display_name": boot_volume.display_name,
            "compartment_id": boot_volume.compartment_id,
            "availability_domain": boot_volume.availability_domain,
            "size_in_mbs": boot_volume.size_in_mbs,
            "size_in_gbs": boot_volume.size_in_gbs,
            "lifecycle_state": boot_volume.lifecycle_state,
            "time_created": str(boot_volume.time_created),
            "is_hydrated": boot_volume.is_hydrated,
            "vpus_per_gb": boot_volume.vpus_per_gb,
            "is_auto_tune_enabled": boot_volume.is_auto_tune_enabled,
            "auto_tuned_vpus_per_gb": boot_volume.auto_tuned_vpus_per_gb,
            "kms_key_id": boot_volume.kms_key_id,
            "source_details": {
                "type": boot_volume.source_details.type if boot_volume.source_details else None,
                "id": boot_volume.source_details.id if boot_volume.source_details else None,
            } if boot_volume.source_details else None,
        }
        
        logger.info(f"Retrieved details for boot volume {boot_volume_id}")
        return boot_volume_details
        
    except Exception as e:
        logger.exception(f"Error getting boot volume details: {e}")
        raise


def list_file_systems(file_storage_client: oci.file_storage.FileStorageClient, 
                      compartment_id: str, availability_domain: str) -> List[Dict[str, Any]]:
    """
    List all file systems in a compartment and availability domain.
    
    Args:
        file_storage_client: OCI FileStorage client
        compartment_id: OCID of the compartment
        availability_domain: Availability domain name
        
    Returns:
        List of file systems with their details
    """
    try:
        file_systems_response = oci.pagination.list_call_get_all_results(
            file_storage_client.list_file_systems,
            compartment_id,
            availability_domain
        )
        
        file_systems = []
        for file_system in file_systems_response.data:
            file_systems.append({
                "id": file_system.id,
                "display_name": file_system.display_name,
                "compartment_id": file_system.compartment_id,
                "availability_domain": file_system.availability_domain,
                "lifecycle_state": file_system.lifecycle_state,
                "time_created": str(file_system.time_created),
                "metered_bytes": file_system.metered_bytes,
                "is_clone_parent": file_system.is_clone_parent,
                "is_hydrated": file_system.is_hydrated,
                "lifecycle_details": file_system.lifecycle_details,
                "kms_key_id": file_system.kms_key_id,
            })
        
        logger.info(f"Found {len(file_systems)} file systems in compartment {compartment_id}")
        return file_systems
        
    except Exception as e:
        logger.exception(f"Error listing file systems: {e}")
        raise


def get_file_system(file_storage_client: oci.file_storage.FileStorageClient, file_system_id: str) -> Dict[str, Any]:
    """
    Get details of a specific file system.
    
    Args:
        file_storage_client: OCI FileStorage client
        file_system_id: OCID of the file system
        
    Returns:
        Details of the file system
    """
    try:
        file_system = file_storage_client.get_file_system(file_system_id).data
        
        file_system_details = {
            "id": file_system.id,
            "display_name": file_system.display_name,
            "compartment_id": file_system.compartment_id,
            "availability_domain": file_system.availability_domain,
            "lifecycle_state": file_system.lifecycle_state,
            "time_created": str(file_system.time_created),
            "metered_bytes": file_system.metered_bytes,
            "is_clone_parent": file_system.is_clone_parent,
            "is_hydrated": file_system.is_hydrated,
            "lifecycle_details": file_system.lifecycle_details,
            "kms_key_id": file_system.kms_key_id,
            "source_details": {
                "parent_file_system_id": file_system.source_details.parent_file_system_id if file_system.source_details else None,
                "source_snapshot_id": file_system.source_details.source_snapshot_id if file_system.source_details else None,
            } if file_system.source_details else None,
        }
        
        logger.info(f"Retrieved details for file system {file_system_id}")
        return file_system_details
        
    except Exception as e:
        logger.exception(f"Error getting file system details: {e}")
        raise
