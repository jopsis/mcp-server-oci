"""
Tools for managing OCI Database Systems (DB Systems) and their DB Nodes.
"""

import logging
import time
from typing import Dict, List, Any, Optional

import oci

logger = logging.getLogger(__name__)


def list_db_systems(database_client: oci.database.DatabaseClient, compartment_id: str) -> List[Dict[str, Any]]:
    """List DB Systems in a compartment."""
    try:
        resp = oci.pagination.list_call_get_all_results(
            database_client.list_db_systems,
            compartment_id=compartment_id,
        )

        items = []
        for d in resp.data:
            items.append({
                "id": d.id,
                "display_name": d.display_name,
                "lifecycle_state": d.lifecycle_state,
                "shape": d.shape,
                "database_edition": getattr(d, "database_edition", None),
                "availability_domain": getattr(d, "availability_domain", None),
                "time_created": str(getattr(d, "time_created", "")),
                "subnet_id": getattr(d, "subnet_id", None),
                "compartment_id": d.compartment_id,
                "node_count": getattr(d, "node_count", None),
                "version": getattr(d, "version", None),
                "cpu_core_count": getattr(d, "cpu_core_count", None),
                "data_storage_size_in_gb": getattr(d, "data_storage_size_in_gb", None),
            })
        logger.info(f"Found {len(items)} DB Systems in compartment {compartment_id}")
        return items
    except Exception as e:
        logger.exception(f"Error listing DB Systems: {e}")
        raise


def get_db_system(database_client: oci.database.DatabaseClient, db_system_id: str) -> Dict[str, Any]:
    """Get DB System details."""
    try:
        d = database_client.get_db_system(db_system_id).data
        return {
            "id": d.id,
            "display_name": d.display_name,
            "lifecycle_state": d.lifecycle_state,
            "shape": d.shape,
            "database_edition": getattr(d, "database_edition", None),
            "availability_domain": getattr(d, "availability_domain", None),
            "time_created": str(getattr(d, "time_created", "")),
            "subnet_id": getattr(d, "subnet_id", None),
            "compartment_id": d.compartment_id,
            "node_count": getattr(d, "node_count", None),
            "version": getattr(d, "version", None),
            "cpu_core_count": getattr(d, "cpu_core_count", None),
            "data_storage_size_in_gb": getattr(d, "data_storage_size_in_gb", None),
            "listener_port": getattr(d, "listener_port", None),
            "scan_dns_record_id": getattr(d, "scan_dns_record_id", None),
            "ssh_public_keys": getattr(d, "ssh_public_keys", None),
        }
    except Exception as e:
        logger.exception(f"Error getting DB System: {e}")
        raise


def list_db_nodes(
    database_client: oci.database.DatabaseClient,
    db_system_id: Optional[str] = None,
    compartment_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List DB Nodes for a DB System, or for all DB Systems in a compartment.
    Always requires compartment_id for the SDK call.
    """
    try:
        if not compartment_id:
            raise ValueError("compartment_id is required")

        nodes: List[Dict[str, Any]] = []

        if db_system_id:
            # Correct usage: positional compartment_id + snake_case db_system_id
            resp = oci.pagination.list_call_get_all_results(
                database_client.list_db_nodes,
                compartment_id,
                db_system_id=db_system_id,
            )
            for n in resp.data:
                nodes.append({
                    "id": n.id,
                    "db_system_id": n.db_system_id,
                    "hostname": getattr(n, "hostname", None),
                    "vnic_id": getattr(n, "vnic_id", None),
                    "lifecycle_state": n.lifecycle_state,
                    "software_storage_size_in_gb": getattr(n, "software_storage_size_in_gb", None),
                    "time_created": str(getattr(n, "time_created", "")),
                })
        else:
            systems = list_db_systems(database_client, compartment_id)
            for sys in systems:
                resp = oci.pagination.list_call_get_all_results(
                    database_client.list_db_nodes,
                    compartment_id,
                    db_system_id=sys["id"],
                )
                for n in resp.data:
                    nodes.append({
                        "id": n.id,
                        "db_system_id": n.db_system_id,
                        "hostname": getattr(n, "hostname", None),
                        "vnic_id": getattr(n, "vnic_id", None),
                        "lifecycle_state": n.lifecycle_state,
                        "software_storage_size_in_gb": getattr(n, "software_storage_size_in_gb", None),
                        "time_created": str(getattr(n, "time_created", "")),
                    })

        logger.info(f"Found {len(nodes)} DB Nodes")
        return nodes
    except Exception as e:
        logger.exception(f"Error listing DB Nodes: {e}")
        raise


def get_db_node(database_client: oci.database.DatabaseClient, db_node_id: str) -> Dict[str, Any]:
    """Get DB Node details."""
    try:
        n = database_client.get_db_node(db_node_id).data
        return {
            "id": n.id,
            "db_system_id": n.db_system_id,
            "hostname": getattr(n, "hostname", None),
            "vnic_id": getattr(n, "vnic_id", None),
            "lifecycle_state": n.lifecycle_state,
            "software_storage_size_in_gb": getattr(n, "software_storage_size_in_gb", None),
            "time_created": str(getattr(n, "time_created", "")),
        }
    except Exception as e:
        logger.exception(f"Error getting DB Node: {e}")
        raise


def start_db_node(database_client: oci.database.DatabaseClient, db_node_id: str) -> Dict[str, Any]:
    """Start a DB Node."""
    try:
        database_client.db_node_action(db_node_id, "START")
        max_wait_time = 60
        wait_interval = 5
        waited = 0
        while waited < max_wait_time:
            time.sleep(wait_interval)
            waited += wait_interval
            node = database_client.get_db_node(db_node_id).data
            if node.lifecycle_state in ["AVAILABLE", "PROVISIONING", "UPDATING"]:
                return {
                    "success": True,
                    "message": f"DB Node {db_node_id} start requested successfully",
                    "current_state": node.lifecycle_state,
                }
        node = database_client.get_db_node(db_node_id).data
        return {
            "success": True,
            "message": f"DB Node {db_node_id} start in progress",
            "current_state": node.lifecycle_state,
        }
    except Exception as e:
        logger.exception(f"Error starting DB Node: {e}")
        raise


def stop_db_node(database_client: oci.database.DatabaseClient, db_node_id: str, soft: bool = True) -> Dict[str, Any]:
    """Stop a DB Node."""
    try:
        action = "STOP"
        database_client.db_node_action(db_node_id, action)
        max_wait_time = 60
        wait_interval = 5
        waited = 0
        while waited < max_wait_time:
            time.sleep(wait_interval)
            waited += wait_interval
            node = database_client.get_db_node(db_node_id).data
            if node.lifecycle_state in ["STOPPED", "STOPPING"]:
                return {
                    "success": True,
                    "message": f"DB Node {db_node_id} stop requested successfully",
                    "current_state": node.lifecycle_state,
                }
        node = database_client.get_db_node(db_node_id).data
        return {
            "success": True,
            "message": f"DB Node {db_node_id} stop in progress",
            "current_state": node.lifecycle_state,
        }
    except Exception as e:
        logger.exception(f"Error stopping DB Node: {e}")
        raise


def reboot_db_node(database_client: oci.database.DatabaseClient, db_node_id: str) -> Dict[str, Any]:
    """Reboot a DB Node."""
    try:
        database_client.db_node_action(db_node_id, "REBOOT")
        return {
            "success": True,
            "message": f"DB Node {db_node_id} reboot requested successfully",
        }
    except Exception as e:
        logger.exception(f"Error rebooting DB Node: {e}")
        raise


def reset_db_node(database_client: oci.database.DatabaseClient, db_node_id: str) -> Dict[str, Any]:
    """Reset (force reboot) a DB Node."""
    try:
        database_client.db_node_action(db_node_id, "RESET")
        return {
            "success": True,
            "message": f"DB Node {db_node_id} reset requested successfully",
        }
    except Exception as e:
        logger.exception(f"Error resetting DB Node: {e}")
        raise


def softreset_db_node(database_client: oci.database.DatabaseClient, db_node_id: str) -> Dict[str, Any]:
    """Soft reset (graceful reboot) a DB Node."""
    try:
        database_client.db_node_action(db_node_id, "SOFTRESET")
        return {
            "success": True,
            "message": f"DB Node {db_node_id} soft reset requested successfully",
        }
    except Exception as e:
        logger.exception(f"Error soft resetting DB Node: {e}")
        raise


def start_db_system_all_nodes(database_client: oci.database.DatabaseClient, db_system_id: str, compartment_id: str) -> Dict[str, Any]:
    """Start all nodes of a DB System. Requires compartment_id to list nodes correctly."""
    try:
        nodes = list_db_nodes(database_client, db_system_id=db_system_id, compartment_id=compartment_id)
        if not nodes:
            return {"success": False, "message": f"No DB Nodes found for DB System {db_system_id}"}
        results = []
        for node in nodes:
            try:
                res = start_db_node(database_client, node["id"])
                results.append({"db_node_id": node["id"], **res})
            except Exception as e:
                results.append({
                    "db_node_id": node["id"],
                    "success": False,
                    "message": f"Error starting node: {str(e)}"
                })
        return {
            "success": True,
            "message": f"Start requested for {len(nodes)} DB Nodes",
            "results": results
        }
    except Exception as e:
        logger.exception(f"Error starting DB System nodes: {e}")
        raise


def stop_db_system_all_nodes(database_client: oci.database.DatabaseClient, db_system_id: str, compartment_id: str, soft: bool = True) -> Dict[str, Any]:
    """Stop all nodes of a DB System. Requires compartment_id to list nodes correctly."""
    try:
        nodes = list_db_nodes(database_client, db_system_id=db_system_id, compartment_id=compartment_id)
        if not nodes:
            return {"success": False, "message": f"No DB Nodes found for DB System {db_system_id}"}
        results = []
        for node in nodes:
            try:
                res = stop_db_node(database_client, node["id"], soft=soft)
                results.append({"db_node_id": node["id"], **res})
            except Exception as e:
                results.append({
                    "db_node_id": node["id"],
                    "success": False,
                    "message": f"Error stopping node: {str(e)}"
                })
        return {
            "success": True,
            "message": f"Stop requested for {len(nodes)} DB Nodes",
            "results": results
        }
    except Exception as e:
        logger.exception(f"Error stopping DB System nodes: {e}")
        raise
