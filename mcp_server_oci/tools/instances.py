"""
Tools for managing OCI compute instances.
"""

import logging
import time
import json
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
    create_vnic_details: Optional[Dict[str, Any]] = None,
    fault_domain: Optional[str] = None,
    assign_public_ip: Optional[bool] = True,
    defined_tags: Optional[Dict[str, Any]] = None,
    freeform_tags: Optional[Dict[str, Any]] = None,
    extended_metadata: Optional[Dict[str, Any]] = None,
    capacity_reservation_id: Optional[str] = None,
    dedicated_vm_host_id: Optional[str] = None,
    hostname_label: Optional[str] = None,
    ipxe_script: Optional[str] = None,
    launch_options: Optional[Dict[str, Any]] = None,
    instance_options: Optional[Dict[str, Any]] = None,
    availability_config: Optional[Dict[str, Any]] = None,
    agent_config: Optional[Dict[str, Any]] = None,
    is_pv_encryption_in_transit_enabled: Optional[bool] = None,
    platform_config: Optional[Dict[str, Any]] = None,
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
        shape_config: Optional shape configuration (OCPUs, memory)
        create_vnic_details: Optional VNIC configuration
        fault_domain: Optional fault domain
        assign_public_ip: Whether to assign a public IP (defaults to True)
        defined_tags: Optional defined tags
        freeform_tags: Optional freeform tags
        extended_metadata: Optional extended metadata
        capacity_reservation_id: Optional capacity reservation ID
        dedicated_vm_host_id: Optional dedicated VM host ID
        hostname_label: Optional hostname label
        ipxe_script: Optional iPXE script
        launch_options: Optional launch options
        instance_options: Optional instance options
        availability_config: Optional availability configuration
        agent_config: Optional agent configuration
        is_pv_encryption_in_transit_enabled: Optional PV encryption in transit
        platform_config: Optional platform configuration
        
    Returns:
        Details of the created instance
    """
    try:
        # Default values
        if metadata is None:
            metadata = {}
            
        # Create the VNIC details
        vnic_details = oci.core.models.CreateVnicDetails(
            subnet_id=subnet_id,
            assign_public_ip=assign_public_ip
        )
        
        # Add additional VNIC configs if provided
        if create_vnic_details:
            if 'display_name' in create_vnic_details:
                vnic_details.display_name = create_vnic_details['display_name']
            if 'hostname_label' in create_vnic_details:
                vnic_details.hostname_label = create_vnic_details['hostname_label']
            if 'private_ip' in create_vnic_details:
                vnic_details.private_ip = create_vnic_details['private_ip']
            if 'nsg_ids' in create_vnic_details:
                vnic_details.nsg_ids = create_vnic_details['nsg_ids']
            if 'skip_source_dest_check' in create_vnic_details:
                vnic_details.skip_source_dest_check = create_vnic_details['skip_source_dest_check']
        
        # Create the source details
        source_details = oci.core.models.InstanceSourceViaImageDetails(
            image_id=image_id
        )
        
        # Add boot volume size if provided
        if boot_volume_size_in_gbs:
            source_details.boot_volume_size_in_gbs = boot_volume_size_in_gbs
            
        # Create the instance details
        instance_details = oci.core.models.LaunchInstanceDetails(
            compartment_id=compartment_id,
            availability_domain=availability_domain,
            display_name=display_name,
            shape=shape,
            source_details=source_details,
            create_vnic_details=vnic_details,
            metadata=metadata,
        )
        
        # Add optional configs if provided
        if shape_config:
            shape_config_obj = oci.core.models.LaunchInstanceShapeConfigDetails()
            if 'ocpus' in shape_config:
                shape_config_obj.ocpus = float(shape_config['ocpus'])
            if 'memory_in_gbs' in shape_config:
                shape_config_obj.memory_in_gbs = float(shape_config['memory_in_gbs'])
            if 'baseline_ocpu_utilization' in shape_config:
                shape_config_obj.baseline_ocpu_utilization = shape_config['baseline_ocpu_utilization']
            instance_details.shape_config = shape_config_obj
            
        if fault_domain:
            instance_details.fault_domain = fault_domain
            
        if defined_tags:
            instance_details.defined_tags = defined_tags
            
        if freeform_tags:
            instance_details.freeform_tags = freeform_tags
            
        if extended_metadata:
            instance_details.extended_metadata = extended_metadata
            
        if capacity_reservation_id:
            instance_details.capacity_reservation_id = capacity_reservation_id
            
        if dedicated_vm_host_id:
            instance_details.dedicated_vm_host_id = dedicated_vm_host_id
            
        if hostname_label:
            instance_details.hostname_label = hostname_label
            
        if ipxe_script:
            instance_details.ipxe_script = ipxe_script
            
        if launch_options:
            launch_options_obj = oci.core.models.LaunchOptions()
            if 'boot_volume_type' in launch_options:
                launch_options_obj.boot_volume_type = launch_options['boot_volume_type']
            if 'firmware' in launch_options:
                launch_options_obj.firmware = launch_options['firmware']
            if 'network_type' in launch_options:
                launch_options_obj.network_type = launch_options['network_type']
            if 'remote_data_volume_type' in launch_options:
                launch_options_obj.remote_data_volume_type = launch_options['remote_data_volume_type']
            if 'is_pv_encryption_in_transit_enabled' in launch_options:
                launch_options_obj.is_pv_encryption_in_transit_enabled = launch_options['is_pv_encryption_in_transit_enabled']
            if 'is_consistent_volume_naming_enabled' in launch_options:
                launch_options_obj.is_consistent_volume_naming_enabled = launch_options['is_consistent_volume_naming_enabled']
            instance_details.launch_options = launch_options_obj
            
        if instance_options:
            instance_options_obj = oci.core.models.InstanceOptions()
            if 'are_legacy_imds_endpoints_disabled' in instance_options:
                instance_options_obj.are_legacy_imds_endpoints_disabled = instance_options['are_legacy_imds_endpoints_disabled']
            instance_details.instance_options = instance_options_obj
            
        if availability_config:
            availability_config_obj = oci.core.models.LaunchInstanceAvailabilityConfigDetails()
            if 'is_live_migration_preferred' in availability_config:
                availability_config_obj.is_live_migration_preferred = availability_config['is_live_migration_preferred']
            if 'recovery_action' in availability_config:
                availability_config_obj.recovery_action = availability_config['recovery_action']
            instance_details.availability_config = availability_config_obj
            
        if agent_config:
            agent_config_obj = oci.core.models.LaunchInstanceAgentConfigDetails()
            if 'is_monitoring_disabled' in agent_config:
                agent_config_obj.is_monitoring_disabled = agent_config['is_monitoring_disabled']
            if 'is_management_disabled' in agent_config:
                agent_config_obj.is_management_disabled = agent_config['is_management_disabled']
            if 'are_all_plugins_disabled' in agent_config:
                agent_config_obj.are_all_plugins_disabled = agent_config['are_all_plugins_disabled']
            if 'plugins_config' in agent_config:
                agent_config_obj.plugins_config = [
                    oci.core.models.InstanceAgentPluginConfigDetails(
                        name=plugin['name'],
                        desired_state=plugin['desired_state']
                    )
                    for plugin in agent_config['plugins_config']
                ]
            instance_details.agent_config = agent_config_obj
            
        if is_pv_encryption_in_transit_enabled is not None:
            instance_details.is_pv_encryption_in_transit_enabled = is_pv_encryption_in_transit_enabled
            
        if platform_config:
            # OCI has different platform config classes based on the type
            platform_type = platform_config.get('type')
            if platform_type == 'AMD_ROME_BM_GPU':
                platform_config_obj = oci.core.models.AmdRomeBmGpuLaunchInstancePlatformConfig(
                    type=platform_type
                )
            elif platform_type == 'AMD_VM':
                platform_config_obj = oci.core.models.AmdVmLaunchInstancePlatformConfig(
                    type=platform_type
                )
            elif platform_type == 'INTEL_VM':
                platform_config_obj = oci.core.models.IntelVmLaunchInstancePlatformConfig(
                    type=platform_type
                )
            elif platform_type == 'AMD_MILAN_BM':
                platform_config_obj = oci.core.models.AmdMilanBmLaunchInstancePlatformConfig(
                    type=platform_type
                )
            else:
                logger.warning(f"Unknown platform type: {platform_type}")
                platform_config_obj = None
                
            if platform_config_obj:
                # Add common properties
                for key in platform_config:
                    if key != 'type' and hasattr(platform_config_obj, key):
                        setattr(platform_config_obj, key, platform_config[key])
                        
                instance_details.platform_config = platform_config_obj
        
        # Log the instance details
        logger.info(f"Creating instance {display_name} in compartment {compartment_id}")
        
        # Launch the instance
        launch_instance_response = compute_client.launch_instance(instance_details)
        instance_id = launch_instance_response.data.id
        logger.info(f"Instance creation initiated with ID: {instance_id}")
        
        # Wait for the instance to become available (max 60 seconds for response)
        max_wait_time = 60
        wait_interval = 10
        total_waited = 0
        
        while total_waited < max_wait_time:
            time.sleep(wait_interval)
            total_waited += wait_interval
            
            try:
                # Get instance details
                instance = compute_client.get_instance(instance_id).data
                logger.info(f"Instance state: {instance.lifecycle_state}")
                
                # If instance is no longer provisioning, get network details
                if instance.lifecycle_state not in ["PROVISIONING", "CREATING"]:
                    public_ip = None
                    private_ip = None
                    
                    # Get VNIC attachments to find IP addresses
                    vnic_attachments = oci.pagination.list_call_get_all_results(
                        compute_client.list_vnic_attachments,
                        compartment_id,
                        instance_id=instance_id
                    ).data
                    
                    # Get IP addresses if VNIC attachments exist
                    if vnic_attachments:
                        # There might be a delay until VNIC attachment is fully created
                        time.sleep(5)
                        
                        for vnic_attachment in vnic_attachments:
                            if vnic_attachment.lifecycle_state == "ATTACHED":
                                try:
                                    vnic = network_client.get_vnic(vnic_attachment.vnic_id).data
                                    if hasattr(vnic, 'public_ip') and vnic.public_ip:
                                        public_ip = vnic.public_ip
                                    if hasattr(vnic, 'private_ip') and vnic.private_ip:
                                        private_ip = vnic.private_ip
                                    
                                    # Break once we find valid IPs
                                    if public_ip or private_ip:
                                        break
                                except Exception as vnic_error:
                                    logger.warning(f"Error getting VNIC details: {vnic_error}")
                    
                    # Return instance details
                    return {
                        "success": True,
                        "message": f"Instance {display_name} created with ID: {instance_id}",
                        "instance_id": instance_id,
                        "name": instance.display_name,
                        "lifecycle_state": instance.lifecycle_state,
                        "compartment_id": instance.compartment_id,
                        "availability_domain": instance.availability_domain,
                        "shape": instance.shape,
                        "fault_domain": instance.fault_domain if hasattr(instance, 'fault_domain') else None,
                        "public_ip": public_ip,
                        "private_ip": private_ip,
                    }
            except oci.exceptions.ServiceError as se:
                if se.status == 404:
                    # Instance not found yet, keep waiting
                    logger.info(f"Instance {instance_id} not found yet, waiting...")
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
        return {
            "success": False,
            "message": f"Failed to create instance: {str(e)}",
            "error": str(e)
        }


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
