# MCP Server para Oracle Cloud Infrastructure (OCI)

Este proyecto implementa un servidor Model Context Protocol (MCP) para Oracle Cloud Infrastructure, permitiendo a los LLMs como Claude interactuar directamente con recursos de OCI.

## Características

- Conexión a Oracle Cloud utilizando la configuración estándar de OCI CLI
- Herramientas para listar y gestionar instancias y compartments en OCI
- Integración con el protocolo MCP para facilitar el acceso desde Claude Desktop

## Requisitos previos

- Python 3.10 o superior
- OCI CLI configurado (`oci setup config`)
- Permisos adecuados en Oracle Cloud

## Instalación

```bash
cd /Users/jocebal/Work/mcp/mcp-server-oci
pip install git+https://github.com/modelcontextprotocol/python-sdk.git
pip install oci fastapi uvicorn click pydantic loguru
pip install -e .
```

## Uso

Para iniciar el servidor MCP directamente:

```bash
python -m mcp_server_oci.mcp_server --profile DEFAULT
```

Con `uv`:

```bash
uv --directory /Users/jocebal/Work/mcp/mcp-server-oci run python -m mcp_server_oci.mcp_server --profile DEFAULT
```

También puedes especificar el perfil usando una variable de entorno:

```bash
OCI_CLI_PROFILE=PERFIL python -m mcp_server_oci.mcp_server
```

## Configuración para Claude Desktop (MacOS)

Añade esta configuración a tu archivo:
`/Users/<usuario>/Library/Application Support/Claude/claude_desktop_config.json`

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
      "PYTHONPATH": "/Users/jocebal/Work/mcp/mcp-server-oci",
      "FASTMCP_LOG_LEVEL": "INFO"
    }
  }
}
```

Alternativamente, puedes usar `uv`:

```json
"mcpServers": {
  "mcp-server-oci": {
    "command": "uv",
    "args": [
      "--directory",
      "/Users/jocebal/Work/mcp/mcp-server-oci",
      "run",
      "python",
      "-m",
      "mcp_server_oci.mcp_server",
      "--profile", "DEFAULT"
    ],
    "env": {
      "FASTMCP_LOG_LEVEL": "INFO"
    }
  }
}
```

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

