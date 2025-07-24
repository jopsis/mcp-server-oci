"""
Tools for managing OCI Identity and Access Management resources.
"""

import logging
from typing import Dict, List, Any, Optional

import oci

logger = logging.getLogger(__name__)


def list_users(identity_client: oci.identity.IdentityClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all users in a compartment.
    
    Args:
        identity_client: OCI Identity client
        compartment_id: OCID of the compartment
        
    Returns:
        List of users with their details
    """
    try:
        users_response = oci.pagination.list_call_get_all_results(
            identity_client.list_users,
            compartment_id
        )
        
        users = []
        for user in users_response.data:
            users.append({
                "id": user.id,
                "name": user.name,
                "description": user.description,
                "email": user.email,
                "email_verified": user.email_verified,
                "is_mfa_activated": user.is_mfa_activated,
                "lifecycle_state": user.lifecycle_state,
                "time_created": str(user.time_created),
                "compartment_id": user.compartment_id,
                "capabilities": {
                    "can_use_console_password": user.capabilities.can_use_console_password if user.capabilities else None,
                    "can_use_api_keys": user.capabilities.can_use_api_keys if user.capabilities else None,
                    "can_use_auth_tokens": user.capabilities.can_use_auth_tokens if user.capabilities else None,
                    "can_use_smtp_credentials": user.capabilities.can_use_smtp_credentials if user.capabilities else None,
                } if user.capabilities else None,
            })
        
        logger.info(f"Found {len(users)} users in compartment {compartment_id}")
        return users
        
    except Exception as e:
        logger.exception(f"Error listing users: {e}")
        raise


def get_user(identity_client: oci.identity.IdentityClient, user_id: str) -> Dict[str, Any]:
    """
    Get details of a specific user.
    
    Args:
        identity_client: OCI Identity client
        user_id: OCID of the user
        
    Returns:
        Details of the user
    """
    try:
        user = identity_client.get_user(user_id).data
        
        user_details = {
            "id": user.id,
            "name": user.name,
            "description": user.description,
            "email": user.email,
            "email_verified": user.email_verified,
            "is_mfa_activated": user.is_mfa_activated,
            "lifecycle_state": user.lifecycle_state,
            "time_created": str(user.time_created),
            "compartment_id": user.compartment_id,
            "capabilities": {
                "can_use_console_password": user.capabilities.can_use_console_password if user.capabilities else None,
                "can_use_api_keys": user.capabilities.can_use_api_keys if user.capabilities else None,
                "can_use_auth_tokens": user.capabilities.can_use_auth_tokens if user.capabilities else None,
                "can_use_smtp_credentials": user.capabilities.can_use_smtp_credentials if user.capabilities else None,
            } if user.capabilities else None,
        }
        
        logger.info(f"Retrieved details for user {user_id}")
        return user_details
        
    except Exception as e:
        logger.exception(f"Error getting user details: {e}")
        raise


def list_groups(identity_client: oci.identity.IdentityClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all groups in a compartment.
    
    Args:
        identity_client: OCI Identity client
        compartment_id: OCID of the compartment
        
    Returns:
        List of groups with their details
    """
    try:
        groups_response = oci.pagination.list_call_get_all_results(
            identity_client.list_groups,
            compartment_id
        )
        
        groups = []
        for group in groups_response.data:
            groups.append({
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "lifecycle_state": group.lifecycle_state,
                "time_created": str(group.time_created),
                "compartment_id": group.compartment_id,
            })
        
        logger.info(f"Found {len(groups)} groups in compartment {compartment_id}")
        return groups
        
    except Exception as e:
        logger.exception(f"Error listing groups: {e}")
        raise


def get_group(identity_client: oci.identity.IdentityClient, group_id: str) -> Dict[str, Any]:
    """
    Get details of a specific group.
    
    Args:
        identity_client: OCI Identity client
        group_id: OCID of the group
        
    Returns:
        Details of the group
    """
    try:
        group = identity_client.get_group(group_id).data
        
        group_details = {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "lifecycle_state": group.lifecycle_state,
            "time_created": str(group.time_created),
            "compartment_id": group.compartment_id,
        }
        
        logger.info(f"Retrieved details for group {group_id}")
        return group_details
        
    except Exception as e:
        logger.exception(f"Error getting group details: {e}")
        raise


def list_policies(identity_client: oci.identity.IdentityClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all policies in a compartment.
    
    Args:
        identity_client: OCI Identity client
        compartment_id: OCID of the compartment
        
    Returns:
        List of policies with their details
    """
    try:
        policies_response = oci.pagination.list_call_get_all_results(
            identity_client.list_policies,
            compartment_id
        )
        
        policies = []
        for policy in policies_response.data:
            policies.append({
                "id": policy.id,
                "name": policy.name,
                "description": policy.description,
                "statements": policy.statements,
                "version_date": str(policy.version_date) if policy.version_date else None,
                "lifecycle_state": policy.lifecycle_state,
                "time_created": str(policy.time_created),
                "compartment_id": policy.compartment_id,
            })
        
        logger.info(f"Found {len(policies)} policies in compartment {compartment_id}")
        return policies
        
    except Exception as e:
        logger.exception(f"Error listing policies: {e}")
        raise


def get_policy(identity_client: oci.identity.IdentityClient, policy_id: str) -> Dict[str, Any]:
    """
    Get details of a specific policy.
    
    Args:
        identity_client: OCI Identity client
        policy_id: OCID of the policy
        
    Returns:
        Details of the policy
    """
    try:
        policy = identity_client.get_policy(policy_id).data
        
        policy_details = {
            "id": policy.id,
            "name": policy.name,
            "description": policy.description,
            "statements": policy.statements,
            "version_date": str(policy.version_date) if policy.version_date else None,
            "lifecycle_state": policy.lifecycle_state,
            "time_created": str(policy.time_created),
            "compartment_id": policy.compartment_id,
        }
        
        logger.info(f"Retrieved details for policy {policy_id}")
        return policy_details
        
    except Exception as e:
        logger.exception(f"Error getting policy details: {e}")
        raise


def list_dynamic_groups(identity_client: oci.identity.IdentityClient, compartment_id: str) -> List[Dict[str, Any]]:
    """
    List all dynamic groups in a compartment.
    
    Args:
        identity_client: OCI Identity client
        compartment_id: OCID of the compartment
        
    Returns:
        List of dynamic groups with their details
    """
    try:
        dynamic_groups_response = oci.pagination.list_call_get_all_results(
            identity_client.list_dynamic_groups,
            compartment_id
        )
        
        dynamic_groups = []
        for dynamic_group in dynamic_groups_response.data:
            dynamic_groups.append({
                "id": dynamic_group.id,
                "name": dynamic_group.name,
                "description": dynamic_group.description,
                "matching_rule": dynamic_group.matching_rule,
                "lifecycle_state": dynamic_group.lifecycle_state,
                "time_created": str(dynamic_group.time_created),
                "compartment_id": dynamic_group.compartment_id,
            })
        
        logger.info(f"Found {len(dynamic_groups)} dynamic groups in compartment {compartment_id}")
        return dynamic_groups
        
    except Exception as e:
        logger.exception(f"Error listing dynamic groups: {e}")
        raise


def get_dynamic_group(identity_client: oci.identity.IdentityClient, dynamic_group_id: str) -> Dict[str, Any]:
    """
    Get details of a specific dynamic group.
    
    Args:
        identity_client: OCI Identity client
        dynamic_group_id: OCID of the dynamic group
        
    Returns:
        Details of the dynamic group
    """
    try:
        dynamic_group = identity_client.get_dynamic_group(dynamic_group_id).data
        
        dynamic_group_details = {
            "id": dynamic_group.id,
            "name": dynamic_group.name,
            "description": dynamic_group.description,
            "matching_rule": dynamic_group.matching_rule,
            "lifecycle_state": dynamic_group.lifecycle_state,
            "time_created": str(dynamic_group.time_created),
            "compartment_id": dynamic_group.compartment_id,
        }
        
        logger.info(f"Retrieved details for dynamic group {dynamic_group_id}")
        return dynamic_group_details
        
    except Exception as e:
        logger.exception(f"Error getting dynamic group details: {e}")
        raise
