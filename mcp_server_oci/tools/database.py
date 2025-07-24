"""
Tools for managing OCI Database resources.
"""

import logging
from typing import Dict, List, Any, Optional

import oci

logger = logging.getLogger(__name__)


def list_db_systems(database_client: oci.database.DatabaseClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all DB systems in a compartment.
    
    Args:
        database_client: OCI Database client
        compartment_id: OCID of the compartment
        
    Returns:
        List of DB systems with their details
    """
    try:
        db_systems_response = oci.pagination.list_call_get_all_results(
            database_client.list_db_systems,
            compartment_id
        )
        
        db_systems = []
        for db_system in db_systems_response.data:
            db_systems.append({
                "id": db_system.id,
                "display_name": db_system.display_name,
                "compartment_id": db_system.compartment_id,
                "availability_domain": db_system.availability_domain,
                "shape": db_system.shape,
                "cpu_core_count": db_system.cpu_core_count,
                "node_count": db_system.node_count,
                "database_edition": db_system.database_edition,
                "lifecycle_state": db_system.lifecycle_state,
                "time_created": str(db_system.time_created),
                "data_storage_size_in_gbs": db_system.data_storage_size_in_gbs,
                "data_storage_percentage": db_system.data_storage_percentage,
                "license_model": db_system.license_model,
                "version": db_system.version,
                "hostname": db_system.hostname,
                "domain": db_system.domain,
                "backup_subnet_id": db_system.backup_subnet_id,
                "subnet_id": db_system.subnet_id,
            })
        
        logger.info(f"Found {len(db_systems)} DB systems in compartment {compartment_id}")
        return db_systems
        
    except Exception as e:
        logger.exception(f"Error listing DB systems: {e}")
        raise


def get_db_system(database_client: oci.database.DatabaseClient, db_system_id: str) -> Dict[str, Any]:
    """
    Get details of a specific DB system.
    
    Args:
        database_client: OCI Database client
        db_system_id: OCID of the DB system
        
    Returns:
        Details of the DB system
    """
    try:
        db_system = database_client.get_db_system(db_system_id).data
        
        db_system_details = {
            "id": db_system.id,
            "display_name": db_system.display_name,
            "compartment_id": db_system.compartment_id,
            "availability_domain": db_system.availability_domain,
            "shape": db_system.shape,
            "cpu_core_count": db_system.cpu_core_count,
            "node_count": db_system.node_count,
            "database_edition": db_system.database_edition,
            "lifecycle_state": db_system.lifecycle_state,
            "time_created": str(db_system.time_created),
            "data_storage_size_in_gbs": db_system.data_storage_size_in_gbs,
            "data_storage_percentage": db_system.data_storage_percentage,
            "license_model": db_system.license_model,
            "version": db_system.version,
            "hostname": db_system.hostname,
            "domain": db_system.domain,
            "backup_subnet_id": db_system.backup_subnet_id,
            "subnet_id": db_system.subnet_id,
            "cluster_name": db_system.cluster_name,
            "maintenance_window": {
                "preference": db_system.maintenance_window.preference if db_system.maintenance_window else None,
                "days_of_week": [day.name for day in db_system.maintenance_window.days_of_week] if db_system.maintenance_window and db_system.maintenance_window.days_of_week else None,
            } if db_system.maintenance_window else None,
        }
        
        logger.info(f"Retrieved details for DB system {db_system_id}")
        return db_system_details
        
    except Exception as e:
        logger.exception(f"Error getting DB system details: {e}")
        raise


def list_databases(database_client: oci.database.DatabaseClient, compartment_id: str, 
                   db_system_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List all databases in a compartment, optionally filtered by DB system.
    
    Args:
        database_client: OCI Database client
        compartment_id: OCID of the compartment
        db_system_id: Optional OCID of the DB system to filter by
        
    Returns:
        List of databases with their details
    """
    try:
        databases_response = oci.pagination.list_call_get_all_results(
            database_client.list_databases,
            compartment_id,
            db_system_id=db_system_id
        )
        
        databases = []
        for database in databases_response.data:
            databases.append({
                "id": database.id,
                "db_name": database.db_name,
                "compartment_id": database.compartment_id,
                "character_set": database.character_set,
                "ncharacter_set": database.ncharacter_set,
                "db_workload": database.db_workload,
                "pdb_name": database.pdb_name,
                "lifecycle_state": database.lifecycle_state,
                "time_created": str(database.time_created),
                "db_unique_name": database.db_unique_name,
                "db_system_id": database.db_system_id,
                "vm_cluster_id": database.vm_cluster_id,
                "kms_key_id": database.kms_key_id,
                "vault_id": database.vault_id,
            })
        
        logger.info(f"Found {len(databases)} databases in compartment {compartment_id}")
        return databases
        
    except Exception as e:
        logger.exception(f"Error listing databases: {e}")
        raise


def get_database(database_client: oci.database.DatabaseClient, database_id: str) -> Dict[str, Any]:
    """
    Get details of a specific database.
    
    Args:
        database_client: OCI Database client
        database_id: OCID of the database
        
    Returns:
        Details of the database
    """
    try:
        database = database_client.get_database(database_id).data
        
        database_details = {
            "id": database.id,
            "db_name": database.db_name,
            "compartment_id": database.compartment_id,
            "character_set": database.character_set,
            "ncharacter_set": database.ncharacter_set,
            "db_workload": database.db_workload,
            "pdb_name": database.pdb_name,
            "lifecycle_state": database.lifecycle_state,
            "time_created": str(database.time_created),
            "db_unique_name": database.db_unique_name,
            "db_system_id": database.db_system_id,
            "vm_cluster_id": database.vm_cluster_id,
            "kms_key_id": database.kms_key_id,
            "vault_id": database.vault_id,
            "source_database_point_in_time_recovery_timestamp": str(database.source_database_point_in_time_recovery_timestamp) if database.source_database_point_in_time_recovery_timestamp else None,
        }
        
        logger.info(f"Retrieved details for database {database_id}")
        return database_details
        
    except Exception as e:
        logger.exception(f"Error getting database details: {e}")
        raise


def list_autonomous_databases(database_client: oci.database.DatabaseClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all autonomous databases in a compartment.
    
    Args:
        database_client: OCI Database client
        compartment_id: OCID of the compartment
        
    Returns:
        List of autonomous databases with their details
    """
    try:
        autonomous_databases_response = oci.pagination.list_call_get_all_results(
            database_client.list_autonomous_databases,
            compartment_id
        )
        
        autonomous_databases = []
        for adb in autonomous_databases_response.data:
            autonomous_databases.append({
                "id": adb.id,
                "db_name": adb.db_name,
                "display_name": adb.display_name,
                "compartment_id": adb.compartment_id,
                "lifecycle_state": adb.lifecycle_state,
                "time_created": str(adb.time_created),
                "cpu_core_count": adb.cpu_core_count,
                "data_storage_size_in_tbs": adb.data_storage_size_in_tbs,
                "is_free_tier": adb.is_free_tier,
                "is_auto_scaling_enabled": adb.is_auto_scaling_enabled,
                "db_workload": adb.db_workload,
                "db_version": adb.db_version,
                "license_model": adb.license_model,
                "is_dedicated": adb.is_dedicated,
                "autonomous_container_database_id": adb.autonomous_container_database_id,
                "is_access_control_enabled": adb.is_access_control_enabled,
                "whitelisted_ips": adb.whitelisted_ips,
                "are_primary_whitelisted_ips_used": adb.are_primary_whitelisted_ips_used,
                "standby_whitelisted_ips": adb.standby_whitelisted_ips,
                "is_data_guard_enabled": adb.is_data_guard_enabled,
                "is_local_data_guard_enabled": adb.is_local_data_guard_enabled,
                "subnet_id": adb.subnet_id,
                "nsg_ids": adb.nsg_ids,
                "private_endpoint": adb.private_endpoint,
                "private_endpoint_label": adb.private_endpoint_label,
            })
        
        logger.info(f"Found {len(autonomous_databases)} autonomous databases in compartment {compartment_id}")
        return autonomous_databases
        
    except Exception as e:
        logger.exception(f"Error listing autonomous databases: {e}")
        raise


def get_autonomous_database(database_client: oci.database.DatabaseClient, autonomous_database_id: str) -> Dict[str, Any]:
    """
    Get details of a specific autonomous database.
    
    Args:
        database_client: OCI Database client
        autonomous_database_id: OCID of the autonomous database
        
    Returns:
        Details of the autonomous database
    """
    try:
        adb = database_client.get_autonomous_database(autonomous_database_id).data
        
        adb_details = {
            "id": adb.id,
            "db_name": adb.db_name,
            "display_name": adb.display_name,
            "compartment_id": adb.compartment_id,
            "lifecycle_state": adb.lifecycle_state,
            "time_created": str(adb.time_created),
            "cpu_core_count": adb.cpu_core_count,
            "data_storage_size_in_tbs": adb.data_storage_size_in_tbs,
            "is_free_tier": adb.is_free_tier,
            "is_auto_scaling_enabled": adb.is_auto_scaling_enabled,
            "db_workload": adb.db_workload,
            "db_version": adb.db_version,
            "license_model": adb.license_model,
            "is_dedicated": adb.is_dedicated,
            "autonomous_container_database_id": adb.autonomous_container_database_id,
            "is_access_control_enabled": adb.is_access_control_enabled,
            "whitelisted_ips": adb.whitelisted_ips,
            "are_primary_whitelisted_ips_used": adb.are_primary_whitelisted_ips_used,
            "standby_whitelisted_ips": adb.standby_whitelisted_ips,
            "is_data_guard_enabled": adb.is_data_guard_enabled,
            "is_local_data_guard_enabled": adb.is_local_data_guard_enabled,
            "subnet_id": adb.subnet_id,
            "nsg_ids": adb.nsg_ids,
            "private_endpoint": adb.private_endpoint,
            "private_endpoint_label": adb.private_endpoint_label,
            "connection_strings": {
                "high": adb.connection_strings.high if adb.connection_strings else None,
                "medium": adb.connection_strings.medium if adb.connection_strings else None,
                "low": adb.connection_strings.low if adb.connection_strings else None,
                "dedicated": adb.connection_strings.dedicated if adb.connection_strings else None,
            } if adb.connection_strings else None,
            "connection_urls": {
                "sql_dev_web_url": adb.connection_urls.sql_dev_web_url if adb.connection_urls else None,
                "apex_url": adb.connection_urls.apex_url if adb.connection_urls else None,
                "machine_learning_user_management_url": adb.connection_urls.machine_learning_user_management_url if adb.connection_urls else None,
                "graph_studio_url": adb.connection_urls.graph_studio_url if adb.connection_urls else None,
                "mongo_db_url": adb.connection_urls.mongo_db_url if adb.connection_urls else None,
            } if adb.connection_urls else None,
        }
        
        logger.info(f"Retrieved details for autonomous database {autonomous_database_id}")
        return adb_details
        
    except Exception as e:
        logger.exception(f"Error getting autonomous database details: {e}")
        raise
