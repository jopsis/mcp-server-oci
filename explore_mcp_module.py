# Explorador del módulo MCP
import sys
import inspect

try:
    import mcp
    print(f"Módulo MCP encontrado en: {mcp.__file__}")
    print(f"Versión de Python: {sys.version}")
    
    # Explorar el módulo mcp.server
    try:
        import mcp.server
        print("\nContenido de mcp.server:")
        for name in dir(mcp.server):
            if not name.startswith("_"):
                try:
                    attr = getattr(mcp.server, name)
                    attr_type = type(attr).__name__
                    if inspect.isclass(attr):
                        print(f"CLASE: {name}")
                        # Explorar los métodos de la clase
                        for method_name in dir(attr):
                            if not method_name.startswith("_"):
                                try:
                                    method = getattr(attr, method_name)
                                    if inspect.isfunction(method) or inspect.ismethod(method):
                                        print(f"  - Método: {method_name}")
                                except:
                                    pass
                    elif inspect.isfunction(attr):
                        print(f"FUNCIÓN: {name}")
                    else:
                        print(f"OTRO: {name} (tipo: {attr_type})")
                except Exception as e:
                    print(f"Error al inspeccionar {name}: {e}")
    except ImportError as e:
        print(f"Error al importar mcp.server: {e}")
except ImportError as e:
    print(f"Error al importar mcp: {e}")
