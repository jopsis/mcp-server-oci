"""
FastAPI server for OCI direct access, without using MCP SDK.
This is a simpler approach if the MCP SDK integration is causing issues.
"""

import os
import sys
import logging
import json
from typing import Dict, Any, List, Optional

import oci
from fastapi import FastAPI, HTTPException
import uvicorn

from mcp_server_oci.tools.compartments import list_compartments
from mcp_server_oci.tools.instances import (
    list_instances, 
    get_instance, 
    start_instance, 
    stop_instance
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server_oci_direct")

# Crear la aplicación FastAPI
app = FastAPI(title="OCI Direct API Server")

# Almacenar los clientes OCI
oci_clients = {}


@app.on_event("startup")
async def startup_event():
    """Initialize OCI clients on startup."""
    global oci_clients
    profile = os.environ.get("OCI_CLI_PROFILE", "DEFAULT")
    logger.info(f"Initializing OCI clients with profile: {profile}")
    
    try:
        # Use OCI config from standard location
        config = oci.config.from_file(profile_name=profile)
        
        # Create clients for various services
        compute_client = oci.core.ComputeClient(config)
        identity_client = oci.identity.IdentityClient(config)
        network_client = oci.core.VirtualNetworkClient(config)
        
        oci_clients = {
            "compute": compute_client,
            "identity": identity_client,
            "network": network_client,
            "config": config,
        }
        
        logger.info("OCI clients initialized successfully.")
    except Exception as e:
        logger.exception(f"Error initializing OCI clients: {e}")
        sys.exit(1)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "OCI Direct API Server",
        "description": "Access OCI resources directly without MCP",
        "endpoints": [
            "/compartments",
            "/instances/{compartment_id}",
            "/instance/{instance_id}",
            "/instance/{instance_id}/start",
            "/instance/{instance_id}/stop",
        ]
    }


@app.get("/compartments")
async def get_compartments():
    """List all compartments."""
    try:
        result = list_compartments(oci_clients["identity"])
        return {"compartments": result}
    except Exception as e:
        logger.exception(f"Error listing compartments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/instances/{compartment_id}")
async def get_instances(compartment_id: str):
    """List all instances in a compartment."""
    try:
        result = list_instances(oci_clients["compute"], compartment_id)
        return {"instances": result}
    except Exception as e:
        logger.exception(f"Error listing instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/instance/{instance_id}")
async def get_instance_details(instance_id: str):
    """Get details of a specific instance."""
    try:
        result = get_instance(oci_clients["compute"], instance_id)
        return result
    except Exception as e:
        logger.exception(f"Error getting instance details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/instance/{instance_id}/start")
async def start_instance_endpoint(instance_id: str):
    """Start an instance."""
    try:
        result = start_instance(oci_clients["compute"], instance_id)
        return result
    except Exception as e:
        logger.exception(f"Error starting instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/instance/{instance_id}/stop")
async def stop_instance_endpoint(instance_id: str, force: bool = False):
    """Stop an instance."""
    try:
        result = stop_instance(oci_clients["compute"], instance_id, force)
        return result
    except Exception as e:
        logger.exception(f"Error stopping instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Añadir un endpoint específico para MCP
@app.post("/mcp")
async def mcp_endpoint(request: Dict[str, Any]):
    """
    MCP-compatible endpoint that accepts tool name and parameters.
    This is a simplified version that tries to mimic the MCP API.
    """
    try:
        tool_name = request.get("name")
        parameters = request.get("parameters", {})
        
        if not tool_name:
            raise HTTPException(status_code=400, detail="Tool name is required")
        
        # Dispatch to the appropriate function
        if tool_name == "list_compartments":
            result = list_compartments(oci_clients["identity"])
        elif tool_name == "list_instances":
            compartment_id = parameters.get("compartment_id")
            if not compartment_id:
                raise HTTPException(status_code=400, detail="compartment_id is required")
            result = list_instances(oci_clients["compute"], compartment_id)
        elif tool_name == "get_instance":
            instance_id = parameters.get("instance_id")
            if not instance_id:
                raise HTTPException(status_code=400, detail="instance_id is required")
            result = get_instance(oci_clients["compute"], instance_id)
        elif tool_name == "start_instance":
            instance_id = parameters.get("instance_id")
            if not instance_id:
                raise HTTPException(status_code=400, detail="instance_id is required")
            result = start_instance(oci_clients["compute"], instance_id)
        elif tool_name == "stop_instance":
            instance_id = parameters.get("instance_id")
            force = parameters.get("force", False)
            if not instance_id:
                raise HTTPException(status_code=400, detail="instance_id is required")
            result = stop_instance(oci_clients["compute"], instance_id, force)
        else:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in MCP endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Run the FastAPI server."""
    profile = os.environ.get("OCI_CLI_PROFILE", "DEFAULT")
    logger.info(f"Starting OCI Direct API Server with profile: {profile}")
    uvicorn.run(app, host="127.0.0.1", port=45678)


if __name__ == "__main__":
    main()
