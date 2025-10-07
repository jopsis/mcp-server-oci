"""
Example demonstrating the Hybrid Error Handling Pattern (Option A)

This shows how the pattern works in practice.
"""

# ===== Example 1: Technical Error (raises Exception) =====

def get_instance_example_technical_error(compute_client, instance_id):
    """
    Example: Getting an instance that doesn't exist
    Result: ServiceError 404 is raised and propagates
    """
    # This will raise oci.exceptions.ServiceError if not found
    instance = compute_client.get_instance(instance_id).data

    return {
        "id": instance.id,
        "name": instance.display_name,
        "state": instance.lifecycle_state
    }
    # No try/except - let exception propagate to decorator


# ===== Example 2: Business State (returns dict with success) =====

def start_instance_example_business_state(compute_client, instance_id):
    """
    Example: Starting an instance that's already running
    Result: Returns {"success": True, "already_running": True, ...}
    """
    # Get instance (may raise ServiceError if doesn't exist - technical error)
    instance = compute_client.get_instance(instance_id).data

    # Business state: already running
    if instance.lifecycle_state == "RUNNING":
        return {
            "success": True,
            "already_running": True,
            "message": "Instance is already running",
            "current_state": "RUNNING",
            "instance_id": instance_id
        }

    # Business state: cannot start from this state
    if instance.lifecycle_state not in ["STOPPED"]:
        return {
            "success": False,
            "message": f"Cannot start instance from state {instance.lifecycle_state}",
            "current_state": instance.lifecycle_state,
            "instance_id": instance_id
        }

    # Perform operation (may raise ServiceError - technical error)
    compute_client.instance_action(instance_id, "START")

    return {
        "success": True,
        "message": "Instance is starting",
        "current_state": "STARTING",
        "instance_id": instance_id
    }


# ===== Example 3: Simple Data Query (returns data directly) =====

def list_instances_example_data_query(compute_client, compartment_id):
    """
    Example: List all instances in a compartment
    Result: Returns list of dicts (or raises ServiceError if auth fails)
    """
    # This will raise ServiceError if auth fails or compartment doesn't exist
    instances_response = compute_client.list_instances(compartment_id).data

    return [
        {
            "id": instance.id,
            "name": instance.display_name,
            "state": instance.lifecycle_state
        }
        for instance in instances_response
    ]
    # No try/except - let exceptions propagate


# ===== How the Decorator Handles Each Case =====

"""
@mcp_tool_wrapper decorator behavior:

CASE 1: Technical Error (Exception raised)
    Input:  get_instance_example_technical_error(client, "invalid-id")
    Raises: oci.exceptions.ServiceError: 404 Not Found
    Decorator catches and returns: {"error": "Error getting instance: 404 Not Found"}
    User sees: {"error": "..."}

CASE 2: Business State Success (dict with success=True)
    Input:  start_instance_example_business_state(client, "running-instance")
    Returns: {"success": True, "already_running": True, "message": "..."}
    Decorator logs: "Instance is already running"
    User sees: {"success": True, "already_running": True, ...}

CASE 3: Business State Failure (dict with success=False)
    Input:  start_instance_example_business_state(client, "provisioning-instance")
    Returns: {"success": False, "message": "Cannot start from PROVISIONING"}
    Decorator logs: "Business state: Cannot start from PROVISIONING"
    User sees: {"success": False, "message": "..."}

CASE 4: Normal Data Query (returns data)
    Input:  list_instances_example_data_query(client, "compartment-id")
    Returns: [{"id": "...", "name": "...", "state": "..."}]
    Decorator logs success message (if provided)
    User sees: [{"id": "...", ...}]
"""


# ===== Client-Side Usage =====

def client_usage_example(mcp_client):
    """
    How a client would use the MCP tools
    """

    # Query data
    instances = mcp_client.call_tool("list_instances", {"compartment_id": "ocid1..."})
    if "error" in instances:
        print(f"Technical error: {instances['error']}")
    else:
        print(f"Found {len(instances)} instances")

    # Perform operation with business states
    result = mcp_client.call_tool("start_instance", {"instance_id": "ocid1..."})

    if "error" in result:
        # Technical error (network, permissions, etc.)
        print(f"Technical error: {result['error']}")
    elif result.get("success"):
        # Operation succeeded
        if result.get("already_running"):
            print("Instance was already running")
        else:
            print(f"Started instance: {result['message']}")
    else:
        # Business state prevents operation
        print(f"Cannot perform operation: {result['message']}")


# ===== Summary =====

"""
Pattern Decision Matrix:

Situation                           → Pattern to Use
=====================================================================================================
API call fails (404, 401, timeout)  → raise Exception (technical error)
Resource doesn't exist              → raise Exception (technical error)
Network error                       → raise Exception (technical error)
Invalid parameters                  → raise ValueError (technical error)

Resource already in target state    → return {"success": True, "already_done": True}
Resource in wrong state for op      → return {"success": False, "message": "why"}
Operation initiated successfully    → return {"success": True, "message": "initiated"}

Simple data query                   → return data directly (list or dict)
"""
