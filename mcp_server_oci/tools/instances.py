"""
Tools for managing OCI compute instances.
"""

import logging
import time
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
        
        # Wait for the instance to start (max 30 seconds for response)
        max_wait_time = 30
        wait_interval = 5
        total_waited = 0
        
        while total_waited < max_wait_time:
            time.sleep(wait_interval)
            total_waited += wait_interval
            
            current_state = compute_client.get_instance(instance_id).data.lifecycle_state
            if current_state == "RUNNING":
                return {
                    "success": True,
                    "message": f"Successfully started instance {instance.display_name} ({instance_id})",
                    "current_state": current_state,
                }
        
        # If we get here, the instance is still starting
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
        
        # Wait for the instance to stop (max 30 seconds for response)
        max_wait_time = 30
        wait_interval = 5
        total_waited = 0
        
        while total_waited < max_wait_time:
            time.sleep(wait_interval)
            total_waited += wait_interval
            
            current_state = compute_client.get_instance(instance_id).data.lifecycle_state
            if current_state == "STOPPED":
                return {
                    "success": True,
                    "message": f"Successfully stopped instance {instance.display_name} ({instance_id})",
                    "current_state": current_state,
                }
        
        # If we get here, the instance is still stopping
        return {
            "success": True,
            "message": f"Instance {instance.display_name} ({instance_id}) is stopping. Check status later.",
            "current_state": compute_client.get_instance(instance_id).data.lifecycle_state,
        }
        
    except Exception as e:
        logger.exception(f"Error stopping instance: {e}")
        raise


def create_instance(
    compute_client: oci.core.ComputeClient,
    network_client: oci.core.VirtualNetworkClient,
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
        compute_client: OCI Compute client
        network_client: OCI VirtualNetwork client
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
        # Create instance details
        create_instance_details = oci.core.models.LaunchInstanceDetails(
            compartment_id=compartment_id,
            availability_domain=availability_domain,
            display_name=display_name,
            shape=shape,
            metadata=metadata or {},
            source_details=oci.core.models.InstanceSourceViaImageDetails(
                source_type="image",
                image_id=image_id,
                boot_volume_size_in_gbs=boot_volume_size_in_gbs,
            ),
            create_vnic_details=oci.core.models.CreateVnicDetails(
                subnet_id=subnet_id,
                assign_public_ip=True,
            ),
        )
        
        # Add shape config if provided
        if shape_config:
            shape_config_obj = oci.core.models.LaunchInstanceShapeConfigDetails()
            if "ocpus" in shape_config:
                shape_config_obj.ocpus = float(shape_config["ocpus"])
            if "memory_in_gbs" in shape_config:
                shape_config_obj.memory_in_gbs = float(shape_config["memory_in_gbs"])
            create_instance_details.shape_config = shape_config_obj
        
        # Launch the instance
        logger.info(f"Creating instance {display_name} in compartment {compartment_id}")
        launch_instance_response = compute_client.launch_instance(create_instance_details)
        instance_id = launch_instance_response.data.id
        
        # Wait for the instance to become available (max 60 seconds for response)
        max_wait_time = 60
        wait_interval = 10
        total_waited = 0
        
        while total_waited < max_wait_time:
            time.sleep(wait_interval)
            total_waited += wait_interval
            
            try:
                instance = compute_client.get_instance(instance_id).data
                if instance.lifecycle_state not in ["PROVISIONING", "CREATING"]:
                    # Instance is no longer in a provisioning state
                    
                    # Get VNIC attachment to retrieve public IP
                    vnic_attachments = oci.pagination.list_call_get_all_results(
                        compute_client.list_vnic_attachments,
                        compartment_id,
                        instance_id=instance_id
                    ).data
                    
                    public_ip = None
                    private_ip = None
                    
                    if vnic_attachments:
                        vnic_id = vnic_attachments[0].vnic_id
                        vnic = network_client.get_vnic(vnic_id).data
                        public_ip = vnic.public_ip
                        private_ip = vnic.private_ip
                    
                    return {
                        "success": instance.lifecycle_state == "RUNNING",
                        "message": f"Instance {display_name} created with ID: {instance_id}",
                        "instance_id": instance_id,
                        "name": instance.display_name,
                        "lifecycle_state": instance.lifecycle_state,
                        "compartment_id": instance.compartment_id,
                        "availability_domain": instance.availability_domain,
                        "shape": instance.shape,
                        "public_ip": public_ip,
                        "private_ip": private_ip,
                    }
            except oci.exceptions.ServiceError as se:
                if se.status == 404:
                    # Instance not found yet, keep waiting
                    continue
                raise
        
        # If we get here, the instance is still provisioning
        return {
            "success": True,
            "message": f"Instance {display_name} is being provisioned with ID: {instance_id}. Check status later.",
            "instance_id": instance_id,
            "lifecycle_state": "PROVISIONING",
        }
        
    except Exception as e:
        logger.exception(f"Error creating instance: {e}")
        raise


def terminate_instance(
    compute_client: oci.core.ComputeClient,
    instance_id: str,
    preserve_boot_volume: bool = False
) -> Dict[str, Any]:
    """
    Terminate (delete) a compute instance.
    
    Args:
        compute_client: OCI Compute client
        instance_id: OCID of the instance to terminate
        preserve_boot_volume: If True, the boot volume will be preserved after the instance is terminated
        
    Returns:
        Result of the operation
    """
    try:
        # Check if instance exists and get its details
        instance = compute_client.get_instance(instance_id).data
        instance_name = instance.display_name
        
        # Terminate the instance
        logger.info(f"Terminating instance {instance_name} ({instance_id})")
        compute_client.terminate_instance(instance_id, preserve_boot_volume=preserve_boot_volume)
        
        # Wait for the instance to be terminated (max 30 seconds for response)
        max_wait_time = 30
        wait_interval = 5
        total_waited = 0
        
        while total_waited < max_wait_time:
            time.sleep(wait_interval)
            total_waited += wait_interval
            
            try:
                current_instance = compute_client.get_instance(instance_id).data
                if current_instance.lifecycle_state == "TERMINATED":
                    return {
                        "success": True,
                        "message": f"Successfully terminated instance {instance_name} ({instance_id})",
                        "current_state": current_instance.lifecycle_state,
                    }
            except oci.exceptions.ServiceError as se:
                if se.status == 404:
                    # Instance not found, means it's been fully terminated
                    return {
                        "success": True,
                        "message": f"Successfully terminated instance {instance_name} ({instance_id})",
                        "current_state": "TERMINATED",
                    }
                raise
        
        # If we get here, the instance is still terminating
        return {
            "success": True,
            "message": f"Instance {instance_name} ({instance_id}) is being terminated. Check status later.",
            "current_state": "TERMINATING",
        }
        
    except oci.exceptions.ServiceError as se:
        if se.status == 404:
            return {
                "success": False,
                "message": f"Instance {instance_id} not found",
                "current_state": "NOT_FOUND",
            }
        logger.exception(f"Service error terminating instance: {se}")
        raise
    except Exception as e:
        logger.exception(f"Error terminating instance: {e}")
        raise
