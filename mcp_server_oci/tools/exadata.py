"""
Tools for OCI Exadata Cloud Service resources.

Covers:
  * Cloud Exadata Infrastructures (fleet-level Exadata hardware)
  * Cloud VM Clusters (Exadata Cloud Service RAC clusters)
  * Cloud Autonomous VM Clusters (Exadata for Autonomous Database)
  * Data Guard associations
  * Database backups
  * Maintenance runs

All functions are read-only and accept the standard
`oci.database.DatabaseClient` plus resource identifiers.
"""

import logging
from typing import Dict, List, Any, Optional

import oci

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cloud Exadata Infrastructures
# ---------------------------------------------------------------------------

def _exadata_infra_to_dict(d) -> Dict[str, Any]:
    return {
        "id": d.id,
        "display_name": d.display_name,
        "shape": d.shape,
        "lifecycle_state": d.lifecycle_state,
        "availability_domain": getattr(d, "availability_domain", None),
        "compartment_id": d.compartment_id,
        "compute_count": getattr(d, "compute_count", None),
        "storage_count": getattr(d, "storage_count", None),
        "total_storage_size_in_gbs": getattr(d, "total_storage_size_in_gbs", None),
        "available_storage_size_in_gbs": getattr(d, "available_storage_size_in_gbs", None),
        "cpu_count": getattr(d, "cpu_count", None),
        "max_cpu_count": getattr(d, "max_cpu_count", None),
        "memory_size_in_gbs": getattr(d, "memory_size_in_gbs", None),
        "max_memory_in_gbs": getattr(d, "max_memory_in_gbs", None),
        "db_node_storage_size_in_gbs": getattr(d, "db_node_storage_size_in_gbs", None),
        "max_db_node_storage_in_gbs": getattr(d, "max_db_node_storage_in_gbs", None),
        "data_storage_size_in_tbs": getattr(d, "data_storage_size_in_tbs", None),
        "max_data_storage_in_tbs": getattr(d, "max_data_storage_in_tbs", None),
        "activated_storage_count": getattr(d, "activated_storage_count", None),
        "additional_storage_count": getattr(d, "additional_storage_count", None),
        "time_created": str(getattr(d, "time_created", "")),
        "last_maintenance_run_id": getattr(d, "last_maintenance_run_id", None),
        "next_maintenance_run_id": getattr(d, "next_maintenance_run_id", None),
    }


def list_cloud_exadata_infrastructures(
    database_client: oci.database.DatabaseClient, compartment_id: str
) -> List[Dict[str, Any]]:
    """List Cloud Exadata Infrastructures in a compartment."""
    try:
        resp = oci.pagination.list_call_get_all_results(
            database_client.list_cloud_exadata_infrastructures, compartment_id
        )
        items = [_exadata_infra_to_dict(d) for d in resp.data]
        logger.info(f"Found {len(items)} Cloud Exadata Infrastructures in {compartment_id}")
        return items
    except Exception as e:
        logger.exception(f"Error listing Cloud Exadata Infrastructures: {e}")
        raise


def get_cloud_exadata_infrastructure(
    database_client: oci.database.DatabaseClient, cloud_exadata_infrastructure_id: str
) -> Dict[str, Any]:
    """Get a Cloud Exadata Infrastructure by OCID."""
    try:
        d = database_client.get_cloud_exadata_infrastructure(cloud_exadata_infrastructure_id).data
        return _exadata_infra_to_dict(d)
    except Exception as e:
        logger.exception(f"Error getting Cloud Exadata Infrastructure: {e}")
        raise


# ---------------------------------------------------------------------------
# Cloud VM Clusters (Exadata Cloud Service RAC)
# ---------------------------------------------------------------------------

def _vm_cluster_to_dict(d) -> Dict[str, Any]:
    return {
        "id": d.id,
        "display_name": d.display_name,
        "shape": d.shape,
        "lifecycle_state": d.lifecycle_state,
        "availability_domain": getattr(d, "availability_domain", None),
        "compartment_id": d.compartment_id,
        "cloud_exadata_infrastructure_id": getattr(d, "cloud_exadata_infrastructure_id", None),
        "cpu_core_count": getattr(d, "cpu_core_count", None),
        "ocpu_count": getattr(d, "ocpu_count", None),
        "memory_size_in_gbs": getattr(d, "memory_size_in_gbs", None),
        "db_node_storage_size_in_gbs": getattr(d, "db_node_storage_size_in_gbs", None),
        "data_storage_size_in_tbs": getattr(d, "data_storage_size_in_tbs", None),
        "node_count": getattr(d, "node_count", None),
        "gi_version": getattr(d, "gi_version", None),
        "system_version": getattr(d, "system_version", None),
        "license_model": getattr(d, "license_model", None),
        "is_local_backup_enabled": getattr(d, "is_local_backup_enabled", None),
        "is_sparse_diskgroup_enabled": getattr(d, "is_sparse_diskgroup_enabled", None),
        "subnet_id": getattr(d, "subnet_id", None),
        "backup_subnet_id": getattr(d, "backup_subnet_id", None),
        "nsg_ids": getattr(d, "nsg_ids", None),
        "hostname": getattr(d, "hostname", None),
        "domain": getattr(d, "domain", None),
        "cluster_name": getattr(d, "cluster_name", None),
        "scan_dns_name": getattr(d, "scan_dns_name", None),
        "scan_ip_ids": getattr(d, "scan_ip_ids", None),
        "vip_ids": getattr(d, "vip_ids", None),
        "time_created": str(getattr(d, "time_created", "")),
    }


def list_cloud_vm_clusters(
    database_client: oci.database.DatabaseClient, compartment_id: str
) -> List[Dict[str, Any]]:
    """List Cloud VM Clusters (Exadata Cloud Service) in a compartment."""
    try:
        resp = oci.pagination.list_call_get_all_results(
            database_client.list_cloud_vm_clusters, compartment_id
        )
        items = [_vm_cluster_to_dict(d) for d in resp.data]
        logger.info(f"Found {len(items)} Cloud VM Clusters in {compartment_id}")
        return items
    except Exception as e:
        logger.exception(f"Error listing Cloud VM Clusters: {e}")
        raise


def get_cloud_vm_cluster(
    database_client: oci.database.DatabaseClient, cloud_vm_cluster_id: str
) -> Dict[str, Any]:
    """Get a Cloud VM Cluster by OCID."""
    try:
        d = database_client.get_cloud_vm_cluster(cloud_vm_cluster_id).data
        return _vm_cluster_to_dict(d)
    except Exception as e:
        logger.exception(f"Error getting Cloud VM Cluster: {e}")
        raise


# ---------------------------------------------------------------------------
# Cloud Autonomous VM Clusters (Exadata for Autonomous Database)
# ---------------------------------------------------------------------------

def list_cloud_autonomous_vm_clusters(
    database_client: oci.database.DatabaseClient, compartment_id: str
) -> List[Dict[str, Any]]:
    """List Cloud Autonomous VM Clusters in a compartment."""
    try:
        resp = oci.pagination.list_call_get_all_results(
            database_client.list_cloud_autonomous_vm_clusters, compartment_id
        )
        items = []
        for d in resp.data:
            items.append({
                "id": d.id,
                "display_name": d.display_name,
                "lifecycle_state": d.lifecycle_state,
                "compartment_id": d.compartment_id,
                "cloud_exadata_infrastructure_id": getattr(d, "cloud_exadata_infrastructure_id", None),
                "cpu_core_count_per_node": getattr(d, "cpu_core_count_per_node", None),
                "memory_per_oracle_compute_unit_in_gbs": getattr(d, "memory_per_oracle_compute_unit_in_gbs", None),
                "total_container_databases": getattr(d, "total_container_databases", None),
                "node_count": getattr(d, "node_count", None),
                "time_created": str(getattr(d, "time_created", "")),
            })
        logger.info(f"Found {len(items)} Cloud Autonomous VM Clusters in {compartment_id}")
        return items
    except Exception as e:
        logger.exception(f"Error listing Cloud Autonomous VM Clusters: {e}")
        raise


# ---------------------------------------------------------------------------
# Data Guard associations
# ---------------------------------------------------------------------------

def list_data_guard_associations(
    database_client: oci.database.DatabaseClient, database_id: str
) -> List[Dict[str, Any]]:
    """List Data Guard associations for a Database (call on the primary DB OCID)."""
    try:
        resp = oci.pagination.list_call_get_all_results(
            database_client.list_data_guard_associations, database_id
        )
        items = []
        for d in resp.data:
            items.append({
                "id": d.id,
                "database_id": d.database_id,
                "role": getattr(d, "role", None),
                "lifecycle_state": d.lifecycle_state,
                "peer_database_id": getattr(d, "peer_database_id", None),
                "peer_role": getattr(d, "peer_role", None),
                "peer_data_guard_association_id": getattr(d, "peer_data_guard_association_id", None),
                "apply_lag": getattr(d, "apply_lag", None),
                "apply_rate": getattr(d, "apply_rate", None),
                "protection_mode": getattr(d, "protection_mode", None),
                "transport_type": getattr(d, "transport_type", None),
                "time_created": str(getattr(d, "time_created", "")),
            })
        logger.info(f"Found {len(items)} Data Guard associations for database {database_id}")
        return items
    except Exception as e:
        logger.exception(f"Error listing Data Guard associations: {e}")
        raise


def get_data_guard_association(
    database_client: oci.database.DatabaseClient,
    database_id: str,
    data_guard_association_id: str,
) -> Dict[str, Any]:
    """Get a specific Data Guard association by ID."""
    try:
        d = database_client.get_data_guard_association(database_id, data_guard_association_id).data
        return {
            "id": d.id,
            "database_id": d.database_id,
            "role": getattr(d, "role", None),
            "lifecycle_state": d.lifecycle_state,
            "peer_database_id": getattr(d, "peer_database_id", None),
            "peer_role": getattr(d, "peer_role", None),
            "peer_data_guard_association_id": getattr(d, "peer_data_guard_association_id", None),
            "apply_lag": getattr(d, "apply_lag", None),
            "apply_rate": getattr(d, "apply_rate", None),
            "protection_mode": getattr(d, "protection_mode", None),
            "transport_type": getattr(d, "transport_type", None),
            "time_created": str(getattr(d, "time_created", "")),
        }
    except Exception as e:
        logger.exception(f"Error getting Data Guard association: {e}")
        raise


# ---------------------------------------------------------------------------
# Backups
# ---------------------------------------------------------------------------

def list_backups(
    database_client: oci.database.DatabaseClient,
    compartment_id: Optional[str] = None,
    database_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List database backups.

    Provide either ``compartment_id`` (all backups in a compartment) or
    ``database_id`` (backups of a specific database). Passing both is fine
    — the SDK accepts them together.
    """
    try:
        if not compartment_id and not database_id:
            raise ValueError("compartment_id or database_id is required")

        kwargs: Dict[str, Any] = {}
        if compartment_id:
            kwargs["compartment_id"] = compartment_id
        if database_id:
            kwargs["database_id"] = database_id

        resp = oci.pagination.list_call_get_all_results(
            database_client.list_backups, **kwargs
        )
        items = []
        for d in resp.data:
            items.append({
                "id": d.id,
                "display_name": getattr(d, "display_name", None),
                "database_id": getattr(d, "database_id", None),
                "compartment_id": getattr(d, "compartment_id", None),
                "type": getattr(d, "type", None),
                "lifecycle_state": d.lifecycle_state,
                "availability_domain": getattr(d, "availability_domain", None),
                "database_edition": getattr(d, "database_edition", None),
                "database_size_in_gbs": getattr(d, "database_size_in_gbs", None),
                "shape": getattr(d, "shape", None),
                "version": getattr(d, "version", None),
                "time_started": str(getattr(d, "time_started", "")),
                "time_ended": str(getattr(d, "time_ended", "")),
            })
        logger.info(f"Found {len(items)} backups")
        return items
    except Exception as e:
        logger.exception(f"Error listing backups: {e}")
        raise


# ---------------------------------------------------------------------------
# Maintenance runs
# ---------------------------------------------------------------------------

def list_maintenance_runs(
    database_client: oci.database.DatabaseClient,
    compartment_id: str,
    target_resource_id: Optional[str] = None,
    target_resource_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List maintenance runs in a compartment, optionally filtered by target
    resource (e.g. a specific Cloud Exadata Infrastructure OCID) and type.
    """
    try:
        kwargs: Dict[str, Any] = {"compartment_id": compartment_id}
        if target_resource_id:
            kwargs["target_resource_id"] = target_resource_id
        if target_resource_type:
            kwargs["target_resource_type"] = target_resource_type

        resp = oci.pagination.list_call_get_all_results(
            database_client.list_maintenance_runs, **kwargs
        )
        items = []
        for d in resp.data:
            items.append({
                "id": d.id,
                "display_name": getattr(d, "display_name", None),
                "description": getattr(d, "description", None),
                "lifecycle_state": d.lifecycle_state,
                "target_resource_id": getattr(d, "target_resource_id", None),
                "target_resource_type": getattr(d, "target_resource_type", None),
                "maintenance_type": getattr(d, "maintenance_type", None),
                "maintenance_subtype": getattr(d, "maintenance_subtype", None),
                "patch_type": getattr(d, "patch_type", None),
                "time_scheduled": str(getattr(d, "time_scheduled", "")),
                "time_started": str(getattr(d, "time_started", "")),
                "time_ended": str(getattr(d, "time_ended", "")),
                "patch_id": getattr(d, "patch_id", None),
            })
        logger.info(f"Found {len(items)} maintenance runs")
        return items
    except Exception as e:
        logger.exception(f"Error listing maintenance runs: {e}")
        raise


def get_maintenance_run(
    database_client: oci.database.DatabaseClient, maintenance_run_id: str
) -> Dict[str, Any]:
    """Get details of a single maintenance run."""
    try:
        d = database_client.get_maintenance_run(maintenance_run_id).data
        return {
            "id": d.id,
            "display_name": getattr(d, "display_name", None),
            "description": getattr(d, "description", None),
            "lifecycle_state": d.lifecycle_state,
            "target_resource_id": getattr(d, "target_resource_id", None),
            "target_resource_type": getattr(d, "target_resource_type", None),
            "maintenance_type": getattr(d, "maintenance_type", None),
            "maintenance_subtype": getattr(d, "maintenance_subtype", None),
            "patch_type": getattr(d, "patch_type", None),
            "time_scheduled": str(getattr(d, "time_scheduled", "")),
            "time_started": str(getattr(d, "time_started", "")),
            "time_ended": str(getattr(d, "time_ended", "")),
            "patch_id": getattr(d, "patch_id", None),
        }
    except Exception as e:
        logger.exception(f"Error getting maintenance run: {e}")
        raise
