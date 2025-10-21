"""
Tools for managing OCI Container Engine for Kubernetes (OKE) resources.
"""

import logging
from typing import Dict, List, Any, Optional
import base64

import oci

logger = logging.getLogger(__name__)


def list_clusters(container_engine_client: oci.container_engine.ContainerEngineClient,
                  compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all OKE clusters in a compartment.

    Args:
        container_engine_client: OCI ContainerEngine client
        compartment_id: OCID of the compartment

    Returns:
        List of clusters with their details
    """
    try:
        clusters_response = oci.pagination.list_call_get_all_results(
            container_engine_client.list_clusters,
            compartment_id
        )

        clusters = []
        for cluster in clusters_response.data:
            clusters.append({
                "id": cluster.id,
                "name": cluster.name,
                "compartment_id": cluster.compartment_id,
                "lifecycle_state": cluster.lifecycle_state,
                "lifecycle_details": cluster.lifecycle_details,
                "vcn_id": cluster.vcn_id,
                "kubernetes_version": cluster.kubernetes_version,
                "time_created": str(cluster.time_created) if cluster.time_created else None,
                "time_updated": str(cluster.time_updated) if cluster.time_updated else None,
                "endpoint_config": {
                    "subnet_id": cluster.endpoint_config.subnet_id if cluster.endpoint_config else None,
                    "is_public_ip_enabled": cluster.endpoint_config.is_public_ip_enabled if cluster.endpoint_config else None,
                } if cluster.endpoint_config else None,
                "type": cluster.type if hasattr(cluster, 'type') else None,
            })

        logger.info(f"Found {len(clusters)} OKE clusters in compartment {compartment_id}")
        return clusters

    except Exception as e:
        logger.exception(f"Error listing OKE clusters: {e}")
        raise


def get_cluster(container_engine_client: oci.container_engine.ContainerEngineClient,
                cluster_id: str) -> Dict[str, Any]:
    """
    Get details of a specific OKE cluster.

    Args:
        container_engine_client: OCI ContainerEngine client
        cluster_id: OCID of the cluster

    Returns:
        Details of the cluster
    """
    try:
        cluster = container_engine_client.get_cluster(cluster_id).data

        # Format endpoint config
        endpoint_config = None
        if cluster.endpoint_config:
            endpoint_config = {
                "subnet_id": cluster.endpoint_config.subnet_id,
                "nsg_ids": cluster.endpoint_config.nsg_ids,
                "is_public_ip_enabled": cluster.endpoint_config.is_public_ip_enabled,
            }

        # Format endpoints
        endpoints = None
        if cluster.endpoints:
            endpoints = {
                "kubernetes": cluster.endpoints.kubernetes if hasattr(cluster.endpoints, 'kubernetes') else None,
                "public_endpoint": cluster.endpoints.public_endpoint if hasattr(cluster.endpoints, 'public_endpoint') else None,
                "private_endpoint": cluster.endpoints.private_endpoint if hasattr(cluster.endpoints, 'private_endpoint') else None,
                "vcn_hostname_endpoint": cluster.endpoints.vcn_hostname_endpoint if hasattr(cluster.endpoints, 'vcn_hostname_endpoint') else None,
            }

        # Format cluster metadata
        metadata = None
        if cluster.metadata:
            metadata = {
                "time_created": str(cluster.metadata.time_created) if hasattr(cluster.metadata, 'time_created') and cluster.metadata.time_created else None,
                "created_by_user_id": cluster.metadata.created_by_user_id if hasattr(cluster.metadata, 'created_by_user_id') else None,
                "created_by_work_request_id": cluster.metadata.created_by_work_request_id if hasattr(cluster.metadata, 'created_by_work_request_id') else None,
                "time_updated": str(cluster.metadata.time_updated) if hasattr(cluster.metadata, 'time_updated') and cluster.metadata.time_updated else None,
                "updated_by_user_id": cluster.metadata.updated_by_user_id if hasattr(cluster.metadata, 'updated_by_user_id') else None,
                "updated_by_work_request_id": cluster.metadata.updated_by_work_request_id if hasattr(cluster.metadata, 'updated_by_work_request_id') else None,
            }

        # Format options
        options = None
        if cluster.options:
            options = {
                "service_lb_subnet_ids": cluster.options.service_lb_subnet_ids if hasattr(cluster.options, 'service_lb_subnet_ids') else None,
                "kubernetes_network_config": {
                    "pods_cidr": cluster.options.kubernetes_network_config.pods_cidr if cluster.options.kubernetes_network_config else None,
                    "services_cidr": cluster.options.kubernetes_network_config.services_cidr if cluster.options.kubernetes_network_config else None,
                } if hasattr(cluster.options, 'kubernetes_network_config') and cluster.options.kubernetes_network_config else None,
                "add_ons": {
                    "is_kubernetes_dashboard_enabled": cluster.options.add_ons.is_kubernetes_dashboard_enabled if cluster.options.add_ons and hasattr(cluster.options.add_ons, 'is_kubernetes_dashboard_enabled') else None,
                    "is_tiller_enabled": cluster.options.add_ons.is_tiller_enabled if cluster.options.add_ons and hasattr(cluster.options.add_ons, 'is_tiller_enabled') else None,
                } if hasattr(cluster.options, 'add_ons') and cluster.options.add_ons else None,
                "admission_controller_options": {
                    "is_pod_security_policy_enabled": cluster.options.admission_controller_options.is_pod_security_policy_enabled if cluster.options.admission_controller_options and hasattr(cluster.options.admission_controller_options, 'is_pod_security_policy_enabled') else None,
                } if hasattr(cluster.options, 'admission_controller_options') and cluster.options.admission_controller_options else None,
                "persistent_volume_config": {
                    "defined_tags": cluster.options.persistent_volume_config.defined_tags if cluster.options.persistent_volume_config and hasattr(cluster.options.persistent_volume_config, 'defined_tags') else None,
                    "freeform_tags": cluster.options.persistent_volume_config.freeform_tags if cluster.options.persistent_volume_config and hasattr(cluster.options.persistent_volume_config, 'freeform_tags') else None,
                } if hasattr(cluster.options, 'persistent_volume_config') and cluster.options.persistent_volume_config else None,
                "service_lb_config": {
                    "defined_tags": cluster.options.service_lb_config.defined_tags if cluster.options.service_lb_config and hasattr(cluster.options.service_lb_config, 'defined_tags') else None,
                    "freeform_tags": cluster.options.service_lb_config.freeform_tags if cluster.options.service_lb_config and hasattr(cluster.options.service_lb_config, 'freeform_tags') else None,
                } if hasattr(cluster.options, 'service_lb_config') and cluster.options.service_lb_config else None,
            }

        cluster_details = {
            "id": cluster.id,
            "name": cluster.name,
            "compartment_id": cluster.compartment_id,
            "lifecycle_state": cluster.lifecycle_state,
            "lifecycle_details": cluster.lifecycle_details,
            "vcn_id": cluster.vcn_id,
            "kubernetes_version": cluster.kubernetes_version,
            "time_created": str(cluster.time_created) if cluster.time_created else None,
            "time_updated": str(cluster.time_updated) if cluster.time_updated else None,
            "endpoint_config": endpoint_config,
            "endpoints": endpoints,
            "metadata": metadata,
            "options": options,
            "available_kubernetes_upgrades": cluster.available_kubernetes_upgrades if hasattr(cluster, 'available_kubernetes_upgrades') else None,
            "image_policy_config": {
                "is_policy_enabled": cluster.image_policy_config.is_policy_enabled if cluster.image_policy_config and hasattr(cluster.image_policy_config, 'is_policy_enabled') else None,
            } if hasattr(cluster, 'image_policy_config') and cluster.image_policy_config else None,
            "cluster_pod_network_options": cluster.cluster_pod_network_options if hasattr(cluster, 'cluster_pod_network_options') else None,
            "type": cluster.type if hasattr(cluster, 'type') else None,
            "freeform_tags": cluster.freeform_tags if hasattr(cluster, 'freeform_tags') else None,
            "defined_tags": cluster.defined_tags if hasattr(cluster, 'defined_tags') else None,
        }

        logger.info(f"Retrieved details for OKE cluster {cluster_id}")
        return cluster_details

    except Exception as e:
        logger.exception(f"Error getting OKE cluster details: {e}")
        raise


def list_node_pools(container_engine_client: oci.container_engine.ContainerEngineClient,
                    compartment_id: str,
                    cluster_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all node pools in a compartment, optionally filtered by cluster.

    Args:
        container_engine_client: OCI ContainerEngine client
        compartment_id: OCID of the compartment
        cluster_id: Optional OCID of the cluster to filter by

    Returns:
        List of node pools with their details
    """
    try:
        kwargs = {"compartment_id": compartment_id}
        if cluster_id:
            kwargs["cluster_id"] = cluster_id

        node_pools_response = oci.pagination.list_call_get_all_results(
            container_engine_client.list_node_pools,
            **kwargs
        )

        node_pools = []
        for np in node_pools_response.data:
            node_pools.append({
                "id": np.id,
                "name": np.name,
                "compartment_id": np.compartment_id,
                "cluster_id": np.cluster_id,
                "lifecycle_state": np.lifecycle_state,
                "lifecycle_details": np.lifecycle_details,
                "kubernetes_version": np.kubernetes_version,
                "node_image_name": np.node_image_name if hasattr(np, 'node_image_name') else None,
                "node_shape": np.node_shape,
                "quantity_per_subnet": np.quantity_per_subnet if hasattr(np, 'quantity_per_subnet') else None,
                "subnet_ids": np.subnet_ids if hasattr(np, 'subnet_ids') else None,
                "node_config_details": {
                    "size": np.node_config_details.size if np.node_config_details else None,
                    "placement_configs": [
                        {
                            "availability_domain": pc.availability_domain,
                            "subnet_id": pc.subnet_id,
                            "capacity_reservation_id": pc.capacity_reservation_id if hasattr(pc, 'capacity_reservation_id') else None,
                        }
                        for pc in np.node_config_details.placement_configs
                    ] if np.node_config_details and hasattr(np.node_config_details, 'placement_configs') and np.node_config_details.placement_configs else [],
                } if hasattr(np, 'node_config_details') and np.node_config_details else None,
                "time_created": str(np.time_created) if hasattr(np, 'time_created') and np.time_created else None,
            })

        logger.info(f"Found {len(node_pools)} node pools in compartment {compartment_id}" +
                   (f" for cluster {cluster_id}" if cluster_id else ""))
        return node_pools

    except Exception as e:
        logger.exception(f"Error listing node pools: {e}")
        raise


def get_node_pool(container_engine_client: oci.container_engine.ContainerEngineClient,
                  node_pool_id: str) -> Dict[str, Any]:
    """
    Get details of a specific node pool.

    Args:
        container_engine_client: OCI ContainerEngine client
        node_pool_id: OCID of the node pool

    Returns:
        Details of the node pool
    """
    try:
        np = container_engine_client.get_node_pool(node_pool_id).data

        # Format node config details
        node_config_details = None
        if hasattr(np, 'node_config_details') and np.node_config_details:
            placement_configs = []
            if hasattr(np.node_config_details, 'placement_configs') and np.node_config_details.placement_configs:
                for pc in np.node_config_details.placement_configs:
                    placement_configs.append({
                        "availability_domain": pc.availability_domain,
                        "subnet_id": pc.subnet_id,
                        "capacity_reservation_id": pc.capacity_reservation_id if hasattr(pc, 'capacity_reservation_id') else None,
                        "fault_domains": pc.fault_domains if hasattr(pc, 'fault_domains') else None,
                    })

            node_config_details = {
                "size": np.node_config_details.size,
                "placement_configs": placement_configs,
                "nsg_ids": np.node_config_details.nsg_ids if hasattr(np.node_config_details, 'nsg_ids') else None,
                "kms_key_id": np.node_config_details.kms_key_id if hasattr(np.node_config_details, 'kms_key_id') else None,
                "is_pv_encryption_in_transit_enabled": np.node_config_details.is_pv_encryption_in_transit_enabled if hasattr(np.node_config_details, 'is_pv_encryption_in_transit_enabled') else None,
                "freeform_tags": np.node_config_details.freeform_tags if hasattr(np.node_config_details, 'freeform_tags') else None,
                "defined_tags": np.node_config_details.defined_tags if hasattr(np.node_config_details, 'defined_tags') else None,
            }

        # Format node shape config
        node_shape_config = None
        if hasattr(np, 'node_shape_config') and np.node_shape_config:
            node_shape_config = {
                "ocpus": np.node_shape_config.ocpus if hasattr(np.node_shape_config, 'ocpus') else None,
                "memory_in_gbs": np.node_shape_config.memory_in_gbs if hasattr(np.node_shape_config, 'memory_in_gbs') else None,
            }

        # Format node source details
        node_source_details = None
        if hasattr(np, 'node_source_details') and np.node_source_details:
            node_source_details = {
                "source_type": np.node_source_details.source_type,
                "image_id": np.node_source_details.image_id if hasattr(np.node_source_details, 'image_id') else None,
                "boot_volume_size_in_gbs": np.node_source_details.boot_volume_size_in_gbs if hasattr(np.node_source_details, 'boot_volume_size_in_gbs') else None,
            }

        # Format initial node labels
        initial_node_labels = []
        if hasattr(np, 'initial_node_labels') and np.initial_node_labels:
            for label in np.initial_node_labels:
                initial_node_labels.append({
                    "key": label.key if hasattr(label, 'key') else None,
                    "value": label.value if hasattr(label, 'value') else None,
                })

        # Format node eviction node pool settings
        node_eviction_node_pool_settings = None
        if hasattr(np, 'node_eviction_node_pool_settings') and np.node_eviction_node_pool_settings:
            node_eviction_node_pool_settings = {
                "eviction_grace_duration": np.node_eviction_node_pool_settings.eviction_grace_duration if hasattr(np.node_eviction_node_pool_settings, 'eviction_grace_duration') else None,
                "is_force_delete_after_grace_duration": np.node_eviction_node_pool_settings.is_force_delete_after_grace_duration if hasattr(np.node_eviction_node_pool_settings, 'is_force_delete_after_grace_duration') else None,
            }

        # Format node pool cycling details
        node_pool_cycling_details = None
        if hasattr(np, 'node_pool_cycling_details') and np.node_pool_cycling_details:
            node_pool_cycling_details = {
                "maximum_unavailable": np.node_pool_cycling_details.maximum_unavailable if hasattr(np.node_pool_cycling_details, 'maximum_unavailable') else None,
                "maximum_surge": np.node_pool_cycling_details.maximum_surge if hasattr(np.node_pool_cycling_details, 'maximum_surge') else None,
                "is_node_cycling_enabled": np.node_pool_cycling_details.is_node_cycling_enabled if hasattr(np.node_pool_cycling_details, 'is_node_cycling_enabled') else None,
            }

        node_pool_details = {
            "id": np.id,
            "name": np.name,
            "compartment_id": np.compartment_id,
            "cluster_id": np.cluster_id,
            "lifecycle_state": np.lifecycle_state,
            "lifecycle_details": np.lifecycle_details,
            "kubernetes_version": np.kubernetes_version,
            "node_image_id": np.node_image_id if hasattr(np, 'node_image_id') else None,
            "node_image_name": np.node_image_name if hasattr(np, 'node_image_name') else None,
            "node_shape": np.node_shape,
            "node_shape_config": node_shape_config,
            "node_source_details": node_source_details,
            "node_config_details": node_config_details,
            "initial_node_labels": initial_node_labels,
            "ssh_public_key": np.ssh_public_key if hasattr(np, 'ssh_public_key') else None,
            "quantity_per_subnet": np.quantity_per_subnet if hasattr(np, 'quantity_per_subnet') else None,
            "subnet_ids": np.subnet_ids if hasattr(np, 'subnet_ids') else None,
            "nodes": [
                {
                    "id": node.id if hasattr(node, 'id') else None,
                    "name": node.name if hasattr(node, 'name') else None,
                    "availability_domain": node.availability_domain if hasattr(node, 'availability_domain') else None,
                    "subnet_id": node.subnet_id if hasattr(node, 'subnet_id') else None,
                    "lifecycle_state": node.lifecycle_state if hasattr(node, 'lifecycle_state') else None,
                    "fault_domain": node.fault_domain if hasattr(node, 'fault_domain') else None,
                    "private_ip": node.private_ip if hasattr(node, 'private_ip') else None,
                    "public_ip": node.public_ip if hasattr(node, 'public_ip') else None,
                    "node_error": {
                        "code": node.node_error.code if node.node_error and hasattr(node.node_error, 'code') else None,
                        "message": node.node_error.message if node.node_error and hasattr(node.node_error, 'message') else None,
                    } if hasattr(node, 'node_error') and node.node_error else None,
                }
                for node in np.nodes
            ] if hasattr(np, 'nodes') and np.nodes else [],
            "node_eviction_node_pool_settings": node_eviction_node_pool_settings,
            "node_pool_cycling_details": node_pool_cycling_details,
            "freeform_tags": np.freeform_tags if hasattr(np, 'freeform_tags') else None,
            "defined_tags": np.defined_tags if hasattr(np, 'defined_tags') else None,
            "time_created": str(np.time_created) if hasattr(np, 'time_created') and np.time_created else None,
        }

        logger.info(f"Retrieved details for node pool {node_pool_id}")
        return node_pool_details

    except Exception as e:
        logger.exception(f"Error getting node pool details: {e}")
        raise


def get_cluster_kubeconfig(container_engine_client: oci.container_engine.ContainerEngineClient,
                           cluster_id: str) -> Dict[str, Any]:
    """
    Get the kubeconfig for a specific OKE cluster.

    Args:
        container_engine_client: OCI ContainerEngine client
        cluster_id: OCID of the cluster

    Returns:
        Kubeconfig content and metadata
    """
    try:
        # Create kubeconfig request
        create_kubeconfig_details = oci.container_engine.models.CreateClusterKubeconfigContentDetails()

        # Get the kubeconfig
        kubeconfig_response = container_engine_client.create_kubeconfig(
            cluster_id,
            create_kubeconfig_details
        )

        # Read the kubeconfig content
        kubeconfig_content = kubeconfig_response.data.content.decode('utf-8') if hasattr(kubeconfig_response.data, 'content') else kubeconfig_response.data.text

        result = {
            "cluster_id": cluster_id,
            "kubeconfig": kubeconfig_content,
            "format": "yaml",
            "usage": "Save this content to ~/.kube/config or use with kubectl --kubeconfig flag",
        }

        logger.info(f"Retrieved kubeconfig for cluster {cluster_id}")
        return result

    except Exception as e:
        logger.exception(f"Error getting cluster kubeconfig: {e}")
        raise


def list_work_requests(container_engine_client: oci.container_engine.ContainerEngineClient,
                       compartment_id: str,
                       resource_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List work requests in a compartment, optionally filtered by resource.

    Args:
        container_engine_client: OCI ContainerEngine client
        compartment_id: OCID of the compartment
        resource_id: Optional OCID of the resource to filter by (cluster or node pool)

    Returns:
        List of work requests with their details
    """
    try:
        kwargs = {"compartment_id": compartment_id}
        if resource_id:
            kwargs["resource_id"] = resource_id

        work_requests_response = oci.pagination.list_call_get_all_results(
            container_engine_client.list_work_requests,
            **kwargs
        )

        work_requests = []
        for wr in work_requests_response.data:
            work_requests.append({
                "id": wr.id,
                "operation_type": wr.operation_type,
                "status": wr.status,
                "compartment_id": wr.compartment_id,
                "resources": [
                    {
                        "action_type": res.action_type if hasattr(res, 'action_type') else None,
                        "entity_type": res.entity_type if hasattr(res, 'entity_type') else None,
                        "identifier": res.identifier if hasattr(res, 'identifier') else None,
                        "entity_uri": res.entity_uri if hasattr(res, 'entity_uri') else None,
                    }
                    for res in wr.resources
                ] if hasattr(wr, 'resources') and wr.resources else [],
                "percent_complete": wr.percent_complete if hasattr(wr, 'percent_complete') else None,
                "time_accepted": str(wr.time_accepted) if hasattr(wr, 'time_accepted') and wr.time_accepted else None,
                "time_started": str(wr.time_started) if hasattr(wr, 'time_started') and wr.time_started else None,
                "time_finished": str(wr.time_finished) if hasattr(wr, 'time_finished') and wr.time_finished else None,
            })

        logger.info(f"Found {len(work_requests)} work requests in compartment {compartment_id}" +
                   (f" for resource {resource_id}" if resource_id else ""))
        return work_requests

    except Exception as e:
        logger.exception(f"Error listing work requests: {e}")
        raise


def get_work_request(container_engine_client: oci.container_engine.ContainerEngineClient,
                     work_request_id: str) -> Dict[str, Any]:
    """
    Get details of a specific work request.

    Args:
        container_engine_client: OCI ContainerEngine client
        work_request_id: OCID of the work request

    Returns:
        Details of the work request
    """
    try:
        wr = container_engine_client.get_work_request(work_request_id).data

        work_request_details = {
            "id": wr.id,
            "operation_type": wr.operation_type,
            "status": wr.status,
            "compartment_id": wr.compartment_id,
            "resources": [
                {
                    "action_type": res.action_type if hasattr(res, 'action_type') else None,
                    "entity_type": res.entity_type if hasattr(res, 'entity_type') else None,
                    "identifier": res.identifier if hasattr(res, 'identifier') else None,
                    "entity_uri": res.entity_uri if hasattr(res, 'entity_uri') else None,
                }
                for res in wr.resources
            ] if hasattr(wr, 'resources') and wr.resources else [],
            "percent_complete": wr.percent_complete if hasattr(wr, 'percent_complete') else None,
            "time_accepted": str(wr.time_accepted) if hasattr(wr, 'time_accepted') and wr.time_accepted else None,
            "time_started": str(wr.time_started) if hasattr(wr, 'time_started') and wr.time_started else None,
            "time_finished": str(wr.time_finished) if hasattr(wr, 'time_finished') and wr.time_finished else None,
        }

        logger.info(f"Retrieved details for work request {work_request_id}")
        return work_request_details

    except Exception as e:
        logger.exception(f"Error getting work request details: {e}")
        raise
