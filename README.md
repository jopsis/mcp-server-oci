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

### **Identity & Access Management** 🆕
#### Compartments
- `list_compartments` - List all compartments accessible to you

#### Users
- `list_users` - List all IAM users in a compartment with capabilities and MFA status
- `get_user` - Get detailed user information including group memberships

#### Groups
- `list_groups` - List all IAM groups in a compartment with member count
- `get_group` - Get detailed group information including members

#### Policies
- `list_policies` - List all IAM policies in a compartment with statements
- `get_policy` - Get detailed policy information with all policy statements

#### Dynamic Groups
- `list_dynamic_groups` - List all dynamic groups with matching rules
- `get_dynamic_group` - Get detailed dynamic group info with instance principal rules

### **Compute Resources**
- `list_instances` - List virtual machine instances in a compartment
- `get_instance` - Get detailed information about a specific instance
- `start_instance` - Start a stopped instance
- `stop_instance` - Stop a running instance (supports soft/force stop)

### **Databases** 🔥
#### DB Systems
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

#### Regular Databases 🆕
- `list_databases` - List databases in a compartment (optionally filtered by DB System)
- `get_database` - Get detailed database information including connection strings and PDB name

#### Autonomous Databases 🆕
- `list_autonomous_databases` - List Autonomous Databases with workload type and connection info
- `get_autonomous_database` - Get detailed ADB info including wallet info and auto-scaling settings

### **Networking**
#### Virtual Cloud Networks (VCNs)
- `list_vcns` - List all VCNs in a compartment with CIDR blocks and DNS info
- `get_vcn` - Get detailed VCN information including IPv6 CIDR blocks

#### Subnets
- `list_subnets` - List all subnets in a compartment (optionally filtered by VCN)
- `get_subnet` - Get detailed subnet information with security lists and routing

#### Virtual Network Interface Cards (VNICs)
- `list_vnics` - List all VNICs in a compartment (optionally filtered by instance)
- `get_vnic` - Get detailed VNIC information including IP addresses and NSG associations

#### Security
- `list_security_lists` - List security lists with ingress/egress rules (optionally filtered by VCN)
- `get_security_list` - Get detailed security list with all rules
- `list_network_security_groups` - List Network Security Groups (NSGs) in a compartment
- `get_network_security_group` - Get detailed NSG information with all security rules

### **Storage** 🆕
#### Object Storage
- `get_namespace` - Get the Object Storage namespace for the tenancy
- `list_buckets` - List all Object Storage buckets in a compartment
- `get_bucket` - Get detailed bucket information including public access settings and versioning

#### Block Storage
- `list_volumes` - List all Block Storage volumes in a compartment
- `get_volume` - Get detailed volume information including size, performance tier, and backup policy
- `list_boot_volumes` - List all boot volumes in a compartment (optionally filtered by AD)
- `get_boot_volume` - Get detailed boot volume information including source image

#### File Storage
- `list_file_systems` - List all File Storage file systems in a compartment and AD
- `get_file_system` - Get detailed file system information including metered bytes and snapshots

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

### **Identity & Access Management** 🆕
```bash
# Users
"List all IAM users in my tenancy"
"Show me details for user ocid1.user.oc1..."
"Does this user have MFA enabled?"
"What groups is this user a member of?"

# Groups
"List all IAM groups in compartment X"
"Show me members of group 'Administrators'"
"Get details for group ocid1.group.oc1..."

# Policies
"List all IAM policies in the root compartment"
"Show me policy statements for 'network-admins-policy'"
"What permissions does this policy grant?"
"Get details for policy ocid1.policy.oc1..."

# Dynamic Groups
"List all dynamic groups in my tenancy"
"Show me matching rules for dynamic group 'instance-principals'"
"What instances match this dynamic group?"
"Get details for dynamic group ocid1.dynamicgroup.oc1..."

# Security auditing
"Which users have admin access?"
"Show me all policies that grant object storage access"
"What dynamic groups allow instance principals?"
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

### **Database Management**
```bash
# DB Systems
"Show me all DB Systems in compartment ocid1.compartment.oc1..."
"Get details for DB System ocid1.dbsystem.oc1..."

# DB Nodes management
"List all DB Nodes for DB System ocid1.dbsystem.oc1..."
"Start DB Node ocid1.dbnode.oc1..."
"Stop all nodes of DB System ocid1.dbsystem.oc1..."
"Reboot DB Node ocid1.dbnode.oc1..."
"Soft reset DB Node ocid1.dbnode.oc1..."

# Regular Databases 🆕
"List all databases in compartment X"
"Show me databases in DB System Y"
"Get connection strings for database ocid1.database.oc1..."
"What is the character set and PDB name of this database?"

# Autonomous Databases 🆕
"List all Autonomous Databases in compartment Z"
"Show me details for ADB ocid1.autonomousdatabase.oc1..."
"What workload type is this Autonomous Database?"
"Get connection strings and wallet info for this ADB"
"Is auto-scaling enabled on this Autonomous Database?"
```

### **Networking Management**
```bash
# VCN operations
"List all VCNs in compartment ocid1.compartment.oc1..."
"Show me details for VCN ocid1.vcn.oc1..."

# Subnet operations
"List all subnets in VCN ocid1.vcn.oc1..."
"Get details for subnet ocid1.subnet.oc1..."

# Security operations
"Show me all security lists in compartment X"
"List all network security groups in VCN Y"
"Get security rules for security list ocid1.securitylist.oc1..."

# VNIC operations
"List all VNICs for instance ocid1.instance.oc1..."
"Show me details for VNIC ocid1.vnic.oc1..."
```

### **Storage Management** 🆕
```bash
# Object Storage operations
"What is my Object Storage namespace?"
"List all buckets in compartment X"
"Show me details for bucket 'my-data-bucket'"
"Is bucket 'public-bucket' publicly accessible?"

# Block Storage operations
"List all volumes in compartment Y"
"Show me details for volume ocid1.volume.oc1..."
"List all boot volumes in compartment Z"
"What is the size and performance tier of this volume?"

# File Storage operations
"List all file systems in compartment W and AD-1"
"Show me details for file system ocid1.filesystem.oc1..."
"How many bytes is this file system using?"
```

### **Resource Discovery**
```bash
# List compartments
"List all compartments in my tenancy"

# Cross-resource queries
"Show me all running instances in compartment X"
"List all DB Systems and their current states"
"Show me the complete network topology for compartment X"
```

## 🚀 **Recent Improvements**

### v1.9 - Identity & Access Management Tools (Latest) 🔐
- **8 new IAM tools**: Users, Groups, Policies, Dynamic Groups
- **Security auditing**: Review user capabilities, MFA status, and group memberships
- **Policy management**: List and inspect all IAM policy statements
- **Dynamic groups**: View instance principal matching rules
- Essential for compliance, security audits, and access troubleshooting
- Total MCP tools increased from 42 to 50
- Added comprehensive IAM usage examples in README

### v1.8 - Database Tools 🗄️
- **4 new database tools**: Regular Databases and Autonomous Databases
- **Regular Databases**: List/get databases with connection strings and PDB names
- **Autonomous Databases**: List/get ADB with workload type, wallet info, and auto-scaling
- Complete database ecosystem coverage: DB Systems, DB Nodes, Databases, and ADB
- Total MCP tools increased from 38 to 42
- Added comprehensive database usage examples in README

### v1.7 - Storage Tools 💾
- **9 new storage tools**: Object Storage, Block Storage, File Storage
- **Object Storage**: Get namespace, list/get buckets with public access info
- **Block Storage**: List/get volumes and boot volumes with performance tiers
- **File Storage**: List/get file systems with metered bytes
- Total MCP tools increased from 29 to 38
- Added comprehensive storage usage examples in README

### v1.6 - Comprehensive Networking Tools 🌐
- **10 new networking tools**: VCNs, Subnets, VNICs, Security Lists, NSGs
- **Network topology discovery**: Complete visibility of network infrastructure
- **Security auditing**: Review security rules and network access controls
- **Connectivity troubleshooting**: VNIC and routing information
- Total MCP tools increased from 19 to 29
- Added comprehensive networking usage examples in README

### v1.5 - Dynamic Profile Selection 🔥
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
