# OCI MCP Server - Complete Resource Discovery Tool

A comprehensive Model Context Protocol (MCP) server for Oracle Cloud Infrastructure that provides **safe, read-only access** to all your OCI resources. Perfect for discovering, exploring, and auditing your cloud infrastructure.

## 🔍 **What This Tool Does**

This MCP server gives you **complete visibility** into your OCI tenancy through a simple, consistent interface. It implements **only `get` and `list` operations** - no destructive actions, making it perfect for:

- **Infrastructure Discovery**: Explore what resources exist in your tenancy
- **Security Auditing**: Review users, groups, policies, and security configurations  
- **Resource Inventory**: Get detailed information about compute, networking, storage, and database resources
- **Compliance Reporting**: Generate comprehensive reports about your cloud infrastructure
- **Troubleshooting**: Quickly understand your current infrastructure state

## 🛡️ **Safety First**

This tool is designed with safety as the top priority:
- ✅ **Read-Only Operations**: Only `list` and `get` functions - no create, modify, or delete
- ✅ **No Destructive Actions**: Cannot start, stop, terminate, or modify any resources (except basic instance start/stop)
- ✅ **Secure Authentication**: Uses your existing OCI CLI configuration and profiles
- ✅ **Minimal Permissions**: Requires only read permissions on resources you want to inspect

## 📋 **Complete Resource Coverage**

### **Identity & Access Management**
- `list_compartments` - List all compartments accessible to you
- `list_users` / `get_user` - User accounts and their capabilities
- `list_groups` / `get_group` - User groups and memberships
- `list_policies` / `get_policy` - IAM policies and their statements
- `list_dynamic_groups` / `get_dynamic_group` - Dynamic groups and matching rules

### **Compute Resources**
- `list_instances` / `get_instance` - Virtual machine instances and their configurations
- `start_instance` / `stop_instance` - Basic instance lifecycle management
- `list_images` / `get_image` - Available OS images and custom images
- `list_shapes` - Available compute shapes and their specifications

### **Networking**
- `list_vcns` / `get_vcn` - Virtual Cloud Networks and their configurations
- `list_subnets` / `get_subnet` - Subnets and their routing/security settings
- `list_vnics` / `get_vnic` - Virtual Network Interface Cards
- `list_security_lists` / `get_security_list` - Network security rules (ingress/egress)
- `list_network_security_groups` / `get_network_security_group` - Advanced security groups

### **Storage**
- `get_namespace` - Object Storage namespace for your tenancy
- `list_buckets` / `get_bucket` - Object Storage buckets and their configurations
- `list_volumes` / `get_volume` - Block Storage volumes
- `list_boot_volumes` / `get_boot_volume` - Boot volumes for instances
- `list_file_systems` / `get_file_system` - File Storage systems

### **Databases**
- `list_db_systems` / `get_db_system` - Database systems and their configurations
- `list_databases` / `get_database` - Individual databases within DB systems
- `list_autonomous_databases` / `get_autonomous_database` - Autonomous databases with connection details

### **Load Balancers**
- `list_load_balancers` / `get_load_balancer` - Classic load balancers with listeners and backend sets
- `list_network_load_balancers` / `get_network_load_balancer` - Network load balancers

### **Security & Encryption**
- `list_vaults` / `get_vault` - Key Management Service vaults

### **Infrastructure Utilities**
- `list_availability_domains` - Available ADs in your region
- `list_fault_domains` - Fault domains within ADs
- `list_regions` - All OCI regions
- `get_tenancy_info` - Your tenancy details and configuration

## 🚀 **Installation & Setup**

### **Prerequisites**
- Python 3.8+
- OCI CLI configured with valid credentials
- Proper OCI IAM permissions for resources you want to query

### **Installation**
```bash
cd /Users/jocebal/Work/mcp/mcp-server-oci
pip install -e .
```

### **Configuration**
The server uses your existing OCI CLI configuration. Make sure you have:

1. **OCI Config File**: `~/.oci/config` with your credentials
2. **Profile Setup**: Default profile or specify with `--profile`
3. **Permissions**: Read access to resources you want to query

## 💡 **Usage Examples**

### **Basic Discovery**
```bash
# Run the server
python -m mcp_server_oci

# From Claude or any MCP client:
# "List all compartments in my tenancy"
# "Show me all compute instances in compartment ocid1.compartment.oc1..."
# "What VCNs do I have and their CIDR blocks?"
```

### **Security Auditing**
```bash
# "List all users and their capabilities"
# "Show me all policies in the root compartment"
# "What are the security list rules for subnet X?"
```

### **Infrastructure Inventory**
```bash
# "List all databases and their configurations"
# "Show me all storage volumes and their sizes"
# "What load balancers do I have and their backend configurations?"
```

### **Advanced Queries**
```bash
# "Show me the complete network topology for compartment X"
# "List all resources that are publicly accessible"
# "Generate a report of all compute instances with their shapes and states"
```

## 🔧 **Development Features**

- **Proper MCP Protocol**: Full stdio transport implementation
- **Structured Schemas**: All tools have proper validation and clear parameters
- **Consistent JSON Responses**: Standardized output format across all tools
- **Comprehensive Logging**: Debug-friendly with detailed operation logs
- **Error Handling**: Graceful error handling with informative messages
- **Local Operation**: Runs entirely on your machine using your credentials

## 🎯 **Perfect For**

- **Cloud Architects**: Understanding existing infrastructure
- **Security Teams**: Auditing IAM configurations and network security
- **DevOps Engineers**: Infrastructure discovery and documentation
- **Compliance Officers**: Generating infrastructure reports
- **New Team Members**: Learning about existing OCI setups
- **Troubleshooting**: Quick infrastructure state investigation

## 🔒 **Security Notes**

- Uses your existing OCI credentials - no additional secrets needed
- All operations are read-only - cannot modify your infrastructure (except basic start/stop)
- Respects OCI IAM permissions - you can only see what you have access to
- No data is stored or transmitted - all operations are real-time queries
- Runs locally on your machine - no cloud dependencies

## 📊 **Output Format**

All tools return structured JSON with:
- Complete resource details
- Relevant metadata (creation time, lifecycle state, etc.)
- Relationships between resources (subnet → VCN, instance → compartment)
- Configuration details (CIDR blocks, security rules, database parameters)

## 🤝 **Integration with Claude**

This MCP server is designed to work seamlessly with Claude, enabling natural language queries like:
- "What compute instances are running in production?"
- "Show me the security configuration for my web tier subnet"
- "Are there any databases that aren't using encryption?"
- "What's the total storage capacity I'm using across all regions?"

Claude can understand the resource relationships and provide comprehensive answers about your OCI infrastructure.

---

**Ready to explore your OCI infrastructure safely and comprehensively!** 🚀