"""
Configuration constants for MCP OCI Server.

This module centralizes all configuration values, magic numbers, and defaults
to make them easily discoverable and modifiable.
"""

# ============================================================================
# Server Configuration
# ============================================================================

# Default port for SSE (Server-Sent Events) transport
DEFAULT_SSE_PORT = 45678

# Default log level for the server
DEFAULT_LOG_LEVEL = "INFO"

# Default OCI CLI profile name
DEFAULT_OCI_PROFILE = "DEFAULT"


# ============================================================================
# SSH Key Generation
# ============================================================================

# Default SSH key size in bits (RSA)
DEFAULT_SSH_KEY_SIZE = 2048

# Public exponent for RSA key generation (standard value)
RSA_PUBLIC_EXPONENT = 65537

# Default comment for generated SSH keys
DEFAULT_SSH_KEY_COMMENT = "oci-mcp-server-key"


# ============================================================================
# File Permissions
# ============================================================================

# Unix file permissions for private SSH keys (owner read/write only)
PRIVATE_KEY_PERMISSIONS = 0o600


# ============================================================================
# HTTP Status Codes (for error handling)
# ============================================================================

HTTP_NOT_FOUND = 404
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_INTERNAL_ERROR = 500


# ============================================================================
# OCI Resource States
# ============================================================================

# Compute Instance States
class InstanceState:
    """OCI Compute Instance lifecycle states."""
    PROVISIONING = "PROVISIONING"
    RUNNING = "RUNNING"
    STARTING = "STARTING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    CREATING_IMAGE = "CREATING_IMAGE"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"


# DB Node States
class DBNodeState:
    """OCI Database Node lifecycle states."""
    PROVISIONING = "PROVISIONING"
    AVAILABLE = "AVAILABLE"
    UPDATING = "UPDATING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"
    FAILED = "FAILED"


# Compartment States
class CompartmentState:
    """OCI Compartment lifecycle states."""
    CREATING = "CREATING"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DELETING = "DELETING"
    DELETED = "DELETED"


# ============================================================================
# OCI API Configuration
# ============================================================================

# Default timeout for OCI API calls (None means use SDK default)
OCI_API_TIMEOUT = None

# Retry configuration
OCI_MAX_RETRIES = 3
OCI_RETRY_BACKOFF_FACTOR = 2  # Exponential backoff multiplier


# ============================================================================
# Pagination
# ============================================================================

# Default page size for list operations
DEFAULT_PAGE_SIZE = 100

# Maximum results to return (None for unlimited)
MAX_RESULTS = None


# ============================================================================
# Resource Naming
# ============================================================================

# Prefix for temporary resources created by MCP server
TEMP_RESOURCE_PREFIX = "mcp_temp_"

# Tag key for resources managed by MCP
MCP_MANAGED_TAG_KEY = "mcp-managed"
MCP_MANAGED_TAG_VALUE = "true"
