#!/bin/bash
# Instalar dependencias del servidor MCP para OCI

# Directorio del proyecto
REPO_DIR=$(pwd)
echo "Instalando en: $REPO_DIR"

# Instalar dependencias
echo "Instalando dependencias..."
pip install git+https://github.com/modelcontextprotocol/python-sdk.git
pip install oci fastapi uvicorn click pydantic loguru
pip install -e .

# Comprobar instalación
echo "Verificando instalación..."
python -c "from mcp.server.fastmcp import FastMCP; print('MCP SDK instalado correctamente'); import oci; print('OCI SDK instalado correctamente')"

if [ $? -eq 0 ]; then
    echo "✅ Instalación completada correctamente"
    
    echo ""
    echo "Para usar con Claude Desktop, copia el archivo claude_config.json a:"
    echo "/Users/jocebal/Library/Application Support/Claude/claude_desktop_config.json"
    echo ""
    echo "Para iniciar el servidor manualmente:"
    echo "python -m mcp_server_oci.mcp_server --profile DEFAULT"
    echo ""
    
    # Preguntar si quiere iniciar el servidor
    echo "¿Deseas iniciar el servidor ahora? (s/n)"
    read -r start_server
    
    if [[ "$start_server" == "s" || "$start_server" == "S" ]]; then
        echo "Iniciando servidor..."
        python -m mcp_server_oci.mcp_server --profile DEFAULT
    fi
else
    echo "❌ Error en la instalación. Por favor revisa los mensajes anteriores."
fi
