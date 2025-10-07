# MCP Server for Oracle Cloud Infrastructure (OCI)

This project implements a Model Context Protocol (MCP) server for Oracle Cloud Infrastructure, allowing LLMs like Claude to interact directly with OCI resources.

![presentation](/images/front.jpeg)

## Features

- **Dynamic Profile Selection**: Switch between OCI profiles/tenancies without restarting the server
- Connection to Oracle Cloud using standard OCI CLI configuration
- Comprehensive tools to list and manage OCI resources
- Instance lifecycle management (start, stop)
- Database Systems and DB Nodes management
- Integration with the MCP protocol to facilitate access from Claude Desktop

## Prerequisites

- Python 3.10 or higher
- OCI CLI configured (`oci setup config`)
- Appropriate permissions in Oracle Cloud

## Installation

Clone this repo

```bash
pip install git+https://github.com/modelcontextprotocol/python-sdk.git
pip install oci fastapi uvicorn click pydantic loguru
pip install -e .
```

## Usage

### Starting the Server

**Option 1: Dynamic Profile Selection (Recommended)**

Start without a profile and select it at runtime:

```bash
python -m mcp_server_oci.mcp_server
```

Then use the MCP tools to manage profiles:
- `list_oci_profiles` - See available profiles from ~/.oci/config
- `set_oci_profile` - Activate a specific profile
- `get_current_oci_profile` - Check which profile is active

**Option 2: With Default Profile**

Start with a specific profile pre-loaded:

```bash
python -m mcp_server_oci.mcp_server --profile DEFAULT
```

With `uv`:

```bash
uv --directory /path/to/mcp-server-oci run python -m mcp_server_oci.mcp_server --profile DEFAULT
```

### Switching Between Tenancies

You can switch between different OCI tenancies without restarting:

```bash
# In your MCP client (e.g., Claude):
# 1. List available profiles
"Show me available OCI profiles"

# 2. Switch to a different tenancy
"Switch to the 'production' OCI profile"

# 3. Verify current profile
"What OCI profile am I using?"
```

## Configuration for Claude Desktop (MacOS)

Add this configuration to your file:
`/Users/<usuario>/Library/Application Support/Claude/claude_desktop_config.json`

**With dynamic profile selection (recommended):**

```json
"mcpServers": {
  "mcp-server-oci": {
    "command": "python",
    "args": [
      "-m",
      "mcp_server_oci.mcp_server"
    ],
    "env": {
      "PYTHONPATH": "/<PATH_TO_MCP>/mcp-server-oci",
      "FASTMCP_LOG_LEVEL": "INFO"
    }
  }
}
```

**With fixed profile:**

```json
"mcpServers": {
  "mcp-server-oci": {
    "command": "python",
    "args": [
      "-m",
      "mcp_server_oci.mcp_server",
      "--profile", "DEFAULT"
    ],
    "env": {
      "PYTHONPATH": "/<PATH_TO_MCP>/mcp-server-oci",
      "FASTMCP_LOG_LEVEL": "INFO"
    }
  }
}
```

**With `uv` and dynamic profiles:**

```json
"mcpServers": {
  "mcp-server-oci": {
    "command": "uv",
    "args": [
      "--directory",
      "/<PATH_TO_MCP>/mcp-server-oci",
      "run",
      "python",
      "-m",
      "mcp_server_oci.mcp_server"
    ],
    "env": {
      "FASTMCP_LOG_LEVEL": "INFO"
    }
  }
}
```

## 📋 **Available MCP Tools**

### **Profile Management** 🆕
- `list_oci_profiles` - List all available OCI profiles from ~/.oci/config
- `set_oci_profile` - Activate a specific profile for API calls
- `get_current_oci_profile` - Show currently active profile

### **Identity & Access Management**
- `list_compartments` - List all compartments accessible to you

### **Compute Resources**
- `list_instances` - List virtual machine instances in a compartment
- `get_instance` - Get detailed information about a specific instance
- `start_instance` - Start a stopped instance
- `stop_instance` - Stop a running instance (supports soft/force stop)

### **Database Systems** 🔥
- `list_db_systems` - List DB Systems in a compartment
- `get_db_system` - Get detailed DB System information
- `list_db_nodes` - List DB Nodes in a compartment (optionally filtered by DB System)
- `get_db_node` - Get detailed DB Node information
- `start_db_node` - Start a stopped DB Node
- `stop_db_node` - Stop a running DB Node (soft or hard stop)
- `reboot_db_node` - Reboot a DB Node
- `reset_db_node` - Reset (force reboot) a DB Node
- `softreset_db_node` - Soft reset (graceful reboot) a DB Node
- `start_db_system` - Start all nodes of a DB System
- `stop_db_system` - Stop all nodes of a DB System

## 💡 **Usage Examples**

### **Profile Management**
```bash
# From Claude or any MCP client:

# List available profiles
"Show me all available OCI profiles"

# Activate a specific profile
"Set the OCI profile to 'production'"

# Check current profile
"What OCI profile am I currently using?"

# Switch between tenancies
"Switch to the DEFAULT profile"
```

### **Compute Instance Management**
```bash
# List instances
"Show me all compute instances in compartment ocid1.compartment.oc1..."

# Get instance details
"Get details for instance ocid1.instance.oc1..."

# Start/stop instances
"Start the instance ocid1.instance.oc1..."
"Stop the instance ocid1.instance.oc1... with force stop"
```

### **Database Systems Management**
```bash
# List DB Systems
"Show me all DB Systems in compartment ocid1.compartment.oc1..."

# Get DB System details
"Get details for DB System ocid1.dbsystem.oc1..."

# Manage DB Nodes
"List all DB Nodes for DB System ocid1.dbsystem.oc1..."
"Start DB Node ocid1.dbnode.oc1..."
"Stop all nodes of DB System ocid1.dbsystem.oc1..."

# Reboot operations
"Reboot DB Node ocid1.dbnode.oc1..."
"Soft reset DB Node ocid1.dbnode.oc1..."
```

### **Resource Discovery**
```bash
# List compartments
"List all compartments in my tenancy"

# Cross-resource queries
"Show me all running instances in compartment X"
"List all DB Systems and their current states"
```

## 🚀 **Recent Improvements**

### v1.5 - Dynamic Profile Selection (Latest) 🔥
- **Multi-tenancy support**: Switch between OCI profiles without restarting
- New MCP tools: `list_oci_profiles`, `set_oci_profile`, `get_current_oci_profile`
- Profile requirement validation in all OCI tools
- Optional `--profile` argument (lazy initialization)
- Complete documentation in `DYNAMIC_PROFILE_SELECTION.md`
- Updated README with accurate tool listing

### v1.4 - Centralized Configuration
- Created centralized `config.py` with all configuration constants
- Eliminated magic numbers throughout the codebase
- Improved maintainability and discoverability of configuration values

### v1.3 - Async Operations
- Removed all blocking `time.sleep()` calls
- Made all operations truly asynchronous
- Improved server responsiveness

### v1.2 - Standardized Error Handling
- Implemented Hybrid Error Handling Pattern
- Technical errors → raise exceptions
- Business states → return success dictionaries
- Comprehensive documentation in `ERROR_HANDLING_PATTERN.md`

### v1.1 - DRY Principle
- Created `mcp_tool_wrapper` decorator
- Eliminated ~150 lines of repetitive code
- Consistent error handling and logging across all tools

### v1.0 - Code Cleanup
- Removed unused/obsolete files
- Cleaned up commented code
- Established clean baseline

## 📚 **Documentation**

- [Dynamic Profile Selection Guide](DYNAMIC_PROFILE_SELECTION.md) - Complete guide for multi-tenancy support
- [Error Handling Pattern](ERROR_HANDLING_PATTERN.md) - Developer guide for error handling
- [Error Handling Examples](EXAMPLE_ERROR_HANDLING.py) - Practical examples

## 🤝 **Contributing**

Contributions are welcome! The codebase follows these patterns:
- Hybrid error handling (raise for technical errors, return dict for business states)
- Async operations (no blocking calls)
- Centralized configuration (constants in `config.py`)
- DRY principle (use decorators for common patterns)

## 📝 **License**

[Add your license here]
