# Dynamic OCI Profile Selection

This feature allows you to dynamically select and switch between OCI profiles without restarting the server.

## Overview

Previously, the MCP server required specifying an OCI profile at startup via `--profile` argument. Now, you can:

1. Start the server without specifying a profile
2. List available profiles from your `~/.oci/config` file
3. Select a profile dynamically when needed
4. Switch between profiles at any time (to query different tenancies)

## New MCP Tools

### `list_oci_profiles`

Lists all available OCI profiles from your `~/.oci/config` file.

**Usage:**
```python
result = mcp_client.call_tool("list_oci_profiles")
```

**Returns:**
```json
[
  {
    "name": "DEFAULT",
    "user": "ocid1.user.oc1...",
    "tenancy": "ocid1.tenancy.oc1...",
    "region": "us-ashburn-1",
    "fingerprint": "aa:bb:cc:dd:..."
  },
  {
    "name": "production",
    "user": "ocid1.user.oc1...",
    "tenancy": "ocid1.tenancy.oc1...",
    "region": "eu-frankfurt-1",
    "fingerprint": "ee:ff:gg:hh:..."
  }
]
```

### `set_oci_profile`

Sets the active OCI profile to use for API calls.

**Parameters:**
- `profile_name` (string): Name of the profile to activate

**Usage:**
```python
result = mcp_client.call_tool("set_oci_profile", {"profile_name": "production"})
```

**Returns:**
```json
{
  "success": true,
  "message": "Profile 'production' activated successfully",
  "current_profile": "production",
  "profile_details": {
    "name": "production",
    "user": "ocid1.user.oc1...",
    "tenancy": "ocid1.tenancy.oc1...",
    "region": "eu-frankfurt-1",
    "fingerprint": "ee:ff:gg:hh:..."
  }
}
```

### `get_current_oci_profile`

Gets the currently active OCI profile.

**Usage:**
```python
result = mcp_client.call_tool("get_current_oci_profile")
```

**Returns (when profile is active):**
```json
{
  "active": true,
  "current_profile": "production",
  "profile_details": {
    "name": "production",
    "user": "ocid1.user.oc1...",
    "tenancy": "ocid1.tenancy.oc1...",
    "region": "eu-frankfurt-1",
    "fingerprint": "ee:ff:gg:hh:..."
  }
}
```

**Returns (when no profile is active):**
```json
{
  "active": false,
  "message": "No profile selected. Use list_oci_profiles to see available profiles, then set_oci_profile to activate one."
}
```

## Usage Workflow

### Starting Without Profile

```bash
# Start server without specifying a profile
python -m mcp_server_oci.mcp_server
```

The server will start and log:
```
Starting OCI MCP Server without a default profile
Use 'list_oci_profiles' to see available profiles and 'set_oci_profile' to activate one
```

### Starting With Profile (Optional)

You can still start with a profile if desired:

```bash
# Start server with a specific profile
python -m mcp_server_oci.mcp_server --profile DEFAULT
```

### Typical Workflow

1. **Start the server** (with or without profile)
2. **List available profiles** (if needed):
   ```python
   profiles = mcp_client.call_tool("list_oci_profiles")
   ```

3. **Select a profile**:
   ```python
   result = mcp_client.call_tool("set_oci_profile", {"profile_name": "DEFAULT"})
   ```

4. **Use OCI tools** (now they will work):
   ```python
   compartments = mcp_client.call_tool("list_compartments")
   instances = mcp_client.call_tool("list_instances", {"compartment_id": "ocid1.compartment..."})
   ```

5. **Switch to different tenancy** (if needed):
   ```python
   result = mcp_client.call_tool("set_oci_profile", {"profile_name": "production"})
   # Now all subsequent calls will use the 'production' profile
   ```

## Profile Requirement

All OCI resource tools (like `list_compartments`, `list_instances`, etc.) now check for an active profile before executing.

If you try to call an OCI tool without setting a profile first, you'll receive:

```json
{
  "error": "No OCI profile selected. Use 'list_oci_profiles' to see available profiles, then 'set_oci_profile' to activate one.",
  "requires_profile": true
}
```

## Benefits

1. **Flexibility**: Start the server once, switch between multiple tenancies/profiles
2. **Multi-tenancy**: Easily work with multiple OCI tenancies in a single session
3. **No restart needed**: Change profiles on-the-fly without restarting the server
4. **Discovery**: List available profiles from config file automatically
5. **Backward compatible**: Can still use `--profile` argument if preferred

## Technical Details

- Profile information is read from `~/.oci/config` (or path specified by `OCI_CONFIG_FILE` environment variable)
- OCI clients are initialized/reinitialized when a profile is set
- The `mcp_tool_wrapper` decorator automatically checks for active profile before executing OCI tools
- Profile management tools (`list_oci_profiles`, `set_oci_profile`, `get_current_oci_profile`) don't require a profile to run

## Example Session

```python
# 1. List available profiles
profiles = client.call_tool("list_oci_profiles")
# Output: [{"name": "DEFAULT", ...}, {"name": "prod", ...}]

# 2. Activate DEFAULT profile
result = client.call_tool("set_oci_profile", {"profile_name": "DEFAULT"})
# Output: {"success": true, "current_profile": "DEFAULT", ...}

# 3. Query compartments in DEFAULT tenancy
compartments = client.call_tool("list_compartments")
# Output: [{"id": "ocid1.compartment...", "name": "root", ...}]

# 4. Switch to production profile
result = client.call_tool("set_oci_profile", {"profile_name": "prod"})
# Output: {"success": true, "current_profile": "prod", ...}

# 5. Query compartments in production tenancy
prod_compartments = client.call_tool("list_compartments")
# Output: [{"id": "ocid1.compartment...", "name": "prod-root", ...}]

# 6. Check current profile
current = client.call_tool("get_current_oci_profile")
# Output: {"active": true, "current_profile": "prod", ...}
```

## Implementation Files

- `mcp_server_oci/profile_manager.py` - Profile management functions
- `mcp_server_oci/mcp_server.py` - MCP tools and profile verification logic
