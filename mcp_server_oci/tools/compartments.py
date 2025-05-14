"""
Tools for managing OCI compartments.
"""

import logging
from typing import Dict, List, Any

import oci

logger = logging.getLogger(__name__)


def list_compartments(identity_client: oci.identity.IdentityClient) -> List[Dict[str, Any]]:
    """
    List all compartments accessible to the user.
    
    Args:
        identity_client: OCI Identity client
        
    Returns:
        List of compartments with their details
    """
    try:
        # Get tenant ID (root compartment)
        tenant_id = identity_client.get_user(identity_client.base_client.config.get("user")).data.compartment_id
        
        # Get all compartments (including nested ones)
        compartments = []
        
        # Get root compartment first
        try:
            root_compartment = identity_client.get_compartment(tenant_id).data
            compartments.append({
                "id": root_compartment.id,
                "name": root_compartment.name,
                "description": root_compartment.description,
                "lifecycle_state": root_compartment.lifecycle_state,
                "is_accessible": True,
                "time_created": str(root_compartment.time_created),
                "is_root": True,
            })
        except Exception as e:
            logger.warning(f"Could not get root compartment: {e}")
        
        # Get all compartments in the tenancy
        list_compartments_response = oci.pagination.list_call_get_all_results(
            identity_client.list_compartments,
            tenant_id,
            compartment_id_in_subtree=True,
            lifecycle_state="ACTIVE",
        )
        
        # Format the compartments
        for compartment in list_compartments_response.data:
            compartments.append({
                "id": compartment.id,
                "name": compartment.name,
                "description": compartment.description,
                "parent_compartment_id": compartment.compartment_id,
                "lifecycle_state": compartment.lifecycle_state,
                "is_accessible": compartment.lifecycle_state == "ACTIVE",
                "time_created": str(compartment.time_created),
                "is_root": False,
            })
        
        logger.info(f"Found {len(compartments)} compartments")
        return compartments
        
    except Exception as e:
        logger.exception(f"Error listing compartments: {e}")
        raise
