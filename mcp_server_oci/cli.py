"""
Simplified CLI for MCP OCI server.
"""

import os
import sys
import logging
from typing import Optional

import click
import uvicorn
from mcp.server import Server

from mcp_server_oci.server import create_oci_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server_oci")

# Variable global para almacenar la instancia del servidor
server_instance = None

@click.command()
@click.option(
    "--profile", 
    help="OCI profile to use", 
    default=lambda: os.environ.get("OCI_CLI_PROFILE", "DEFAULT")
)
@click.option(
    "--host", 
    help="Host to bind the server to", 
    default="127.0.0.1"
)
@click.option(
    "--port", 
    help="Port to bind the server to", 
    default=45678
)
@click.option(
    "--debug", 
    help="Enable debug mode", 
    is_flag=True
)
def main(profile: str, host: str, port: int, debug: bool):
    """Start the MCP server for Oracle Cloud Infrastructure."""
    global server_instance
    
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"Starting MCP OCI server with profile: {profile}")
    
    try:
        # Create the MCP server with OCI tools
        tools = create_oci_tools(profile)
        server_instance = Server(tools, "OCI MCP Server")
        
        # Start the server
        logger.info(f"Starting server on {host}:{port}")
        
        # Intenta diferentes métodos para iniciar el servidor
        try:
            # Método 1: Si Server tiene un atributo 'app'
            if hasattr(server_instance, 'app'):
                logger.info("Usando server_instance.app")
                uvicorn.run(server_instance.app, host=host, port=port)
                return
        except Exception as e1:
            logger.warning(f"Método 1 falló: {e1}")
        
        try:
            # Método 2: Si Server es directamente una app ASGI
            logger.info("Usando server_instance directamente")
            uvicorn.run(server_instance, host=host, port=port)
            return
        except Exception as e2:
            logger.warning(f"Método 2 falló: {e2}")
        
        try:
            # Método 3: Usar el método serve() si existe
            if hasattr(server_instance, 'serve'):
                logger.info("Usando server_instance.serve()")
                server_instance.serve(host=host, port=port)
                return
        except Exception as e3:
            logger.warning(f"Método 3 falló: {e3}")

        # Si ningún método funciona, intentar obtener más información
        logger.error("No se pudo determinar cómo iniciar el servidor MCP.")
        logger.info("Propiedades del objeto Server:")
        for attr in dir(server_instance):
            if not attr.startswith('_'):
                logger.info(f"- {attr}")
        
        # Intento final si la API ha cambiado completamente
        try:
            logger.info("Intentando como último recurso...")
            server_instance.run(host=host, port=port)
        except Exception as e4:
            logger.error(f"Intento final falló: {e4}")
            raise RuntimeError("No se pudo iniciar el servidor MCP. Consulta la documentación actualizada.")
            
    except Exception as e:
        logger.exception(f"Error starting MCP OCI server: {e}")
        sys.exit(1)


# Este objeto estará disponible para uvicorn cuando se usa la sintaxis de módulo
# por ejemplo: uvicorn mcp_server_oci.cli:app
app = None

if __name__ == "__main__":
    main()
