"""
Tools for managing OCI compute instances.
"""

import logging
from typing import Dict, List, Any, Optional

import oci

logger = logging.getLogger(__name__)


def list_instances(compute_client: oci.core.ComputeClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all instances in a compartment.
    
    Args:
        compute_client: OCI Compute client
        compartment_id: OCID of the compartment
        
    Returns:
        List of instances with their details
    """
    try:
        # List all instances in the compartment
        instances_response = oci.pagination.list_call_get_all_results(
            compute_client.list_instances,
            compartment_id,
        )
        
        # Format the instances
        instances = []
        for instance in instances_response.data:
            instances.append({
                "id": instance.id,
                "name": instance.display_name,
                "lifecycle_state": instance.lifecycle_state,
                "shape": instance.shape,
                "time_created": str(instance.time_created),
                "availability_domain": instance.availability_domain,
                "compartment_id": instance.compartment_id,
                "fault_domain": instance.fault_domain,
                "is_running": instance.lifecycle_state == "RUNNING",
                "ocpu_count": getattr(instance.shape_config, "ocpus", None) if instance.shape_config else None,
                "memory_in_gbs": getattr(instance.shape_config, "memory_in_gbs", None) if instance.shape_config else None,
            })
        
        logger.info(f"Found {len(instances)} instances in compartment {compartment_id}")
        return instances
        
    except Exception as e:
        logger.exception(f"Error listing instances: {e}")
        raise


def get_instance(compute_client: oci.core.ComputeClient, instance_id: str) -> Dict[str, Any]:
    """
    Get details of a specific instance.
    
    Args:
        compute_client: OCI Compute client
        instance_id: OCID of the instance
        
    Returns:
        Details of the instance
    """
    try:
        # Get the instance details
        instance = compute_client.get_instance(instance_id).data
        
        # Get VNIC attachments for the instance
        vnic_attachments = oci.pagination.list_call_get_all_results(
            compute_client.list_vnic_attachments,
            instance.compartment_id,
            instance_id=instance_id
        ).data
        
        # Format the instance details
        instance_details = {
            "id": instance.id,
            "name": instance.display_name,
            "lifecycle_state": instance.lifecycle_state,
            "shape": instance.shape,
            "time_created": str(instance.time_created),
            "availability_domain": instance.availability_domain,
            "compartment_id": instance.compartment_id,
            "fault_domain": instance.fault_domain,
            "is_running": instance.lifecycle_state == "RUNNING",
            "metadata": instance.metadata,
            "vnic_attachments": [
                {
                    "id": vnic.id,
                    "display_name": vnic.display_name,
                    "lifecycle_state": vnic.lifecycle_state,
                    "vnic_id": vnic.vnic_id,
                }
                for vnic in vnic_attachments
            ],
        }
        
        # Include shape config if available
        if instance.shape_config:
            instance_details.update({
                "ocpu_count": instance.shape_config.ocpus if hasattr(instance.shape_config, "ocpus") else None,
                "memory_in_gbs": instance.shape_config.memory_in_gbs if hasattr(instance.shape_config, "memory_in_gbs") else None,
                "processors": instance.shape_config.processors if hasattr(instance.shape_config, "processors") else None,
            })
        
        logger.info(f"Retrieved details for instance {instance_id}")
        return instance_details
        
    except Exception as e:
        logger.exception(f"Error getting instance details: {e}")
        raise


def start_instance(compute_client: oci.core.ComputeClient, instance_id: str) -> Dict[str, Any]:
    """
    Start an instance.
    
    Args:
        compute_client: OCI Compute client
        instance_id: OCID of the instance to start
        
    Returns:
        Result of the operation
    """
    try:
        # Check if instance is already running
        instance = compute_client.get_instance(instance_id).data
        if instance.lifecycle_state == "RUNNING":
            return {
                "success": True,
                "message": f"Instance {instance.display_name} ({instance_id}) is already running",
                "current_state": instance.lifecycle_state,
            }
        
        if instance.lifecycle_state != "STOPPED":
            return {
                "success": False,
                "message": f"Cannot start instance {instance.display_name} ({instance_id}). Current state: {instance.lifecycle_state}",
                "current_state": instance.lifecycle_state,
            }
        
        # Start the instance
        compute_client.instance_action(instance_id, "START")

        # Return immediately - instance is starting
        return {
            "success": True,
            "message": f"Instance {instance.display_name} ({instance_id}) is starting. Check status later.",
            "current_state": compute_client.get_instance(instance_id).data.lifecycle_state,
        }
        
    except Exception as e:
        logger.exception(f"Error starting instance: {e}")
        raise


def stop_instance(compute_client: oci.core.ComputeClient, instance_id: str, force: bool = False) -> Dict[str, Any]:
    """
    Stop an instance.
    
    Args:
        compute_client: OCI Compute client
        instance_id: OCID of the instance to stop
        force: If True, perform a force stop
        
    Returns:
        Result of the operation
    """
    try:
        # Check if instance is already stopped
        instance = compute_client.get_instance(instance_id).data
        if instance.lifecycle_state == "STOPPED":
            return {
                "success": True,
                "message": f"Instance {instance.display_name} ({instance_id}) is already stopped",
                "current_state": instance.lifecycle_state,
            }
        
        if instance.lifecycle_state != "RUNNING":
            return {
                "success": False,
                "message": f"Cannot stop instance {instance.display_name} ({instance_id}). Current state: {instance.lifecycle_state}",
                "current_state": instance.lifecycle_state,
            }
        
        # Stop the instance
        action = "SOFTSTOP"
        if force:
            action = "STOP"

        compute_client.instance_action(instance_id, action)

        # Return immediately - operation is asynchronous
        logger.info(f"Initiated {action} for instance {instance_id}")
        return {
            "success": True,
            "message": f"Instance stop operation initiated. Check status with get_instance to monitor progress.",
            "current_state": "STOPPING",
            "instance_id": instance_id,
            "stop_type": "soft" if action == "SOFTSTOP" else "force"
        }
        
    except Exception as e:
        logger.exception(f"Error stopping instance: {e}")
        raise
