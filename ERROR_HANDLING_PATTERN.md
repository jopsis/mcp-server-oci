# Error Handling Pattern - Opción A (Híbrido)

## Principio

**Errores técnicos → `raise Exception`**
**Estados de negocio → `return dict` con "success"**

---

## 1. Errores Técnicos (usar `raise`)

Situaciones donde algo técnicamente falló y no se puede continuar:

### Ejemplos:
- ❌ API de OCI no responde
- ❌ Permisos insuficientes (401/403)
- ❌ Recurso no encontrado (404)
- ❌ Parámetros inválidos
- ❌ Timeout de red
- ❌ Configuración OCI incorrecta

### Código:
```python
def get_instance(compute_client, instance_id):
    """Get instance details."""
    # Si falla, lanza ServiceError automáticamente
    instance = compute_client.get_instance(instance_id).data

    return {
        "id": instance.id,
        "name": instance.display_name,
        "state": instance.lifecycle_state,
        ...
    }
    # No try/except - dejamos que la excepción se propague
```

---

## 2. Estados de Negocio (usar `return dict`)

Situaciones válidas del sistema que requieren acción del usuario:

### Ejemplos:
- ✅ Instancia ya está corriendo (intentar start)
- ✅ Instancia no puede iniciarse desde estado PROVISIONING
- ✅ DB System ya está detenido
- ⚠️ Operación en progreso, verificar más tarde

### Código:
```python
def start_instance(compute_client, instance_id):
    """Start an instance."""
    # Error técnico: si no existe, lanza excepción
    instance = compute_client.get_instance(instance_id).data

    # Estado de negocio: ya está corriendo
    if instance.lifecycle_state == "RUNNING":
        return {
            "success": True,
            "already_running": True,
            "message": "Instance is already running",
            "current_state": "RUNNING"
        }

    # Estado de negocio: no se puede iniciar
    if instance.lifecycle_state not in ["STOPPED"]:
        return {
            "success": False,
            "message": f"Cannot start instance from state {instance.lifecycle_state}",
            "current_state": instance.lifecycle_state
        }

    # Operación real - puede lanzar excepción
    compute_client.instance_action(instance_id, "START")

    return {
        "success": True,
        "message": "Instance is starting",
        "current_state": "STARTING"
    }
```

---

## 3. Flujo Completo

```
Usuario
  ↓
MCP Tool (mcp_server.py)
  ↓
@mcp_tool_wrapper  ← Captura excepciones, convierte a {"error": ...}
  ↓
Tool Function (tools/*.py)
  ├─→ Error técnico → raise Exception
  └─→ Estado de negocio → return {"success": bool, ...}
  ↓
Decorator procesa:
  ├─→ Exception → return {"error": "..."}
  └─→ Dict → return as-is
  ↓
Cliente MCP recibe respuesta uniforme
```

---

## 4. Estructura de Respuestas

### Respuesta Exitosa (dato único):
```python
{
    "id": "ocid1...",
    "name": "my-instance",
    "state": "RUNNING",
    ...
}
```

### Respuesta Exitosa (lista):
```python
[
    {"id": "ocid1...", "name": "instance1"},
    {"id": "ocid2...", "name": "instance2"}
]
```

### Operación con Estado de Negocio:
```python
{
    "success": True,
    "message": "Instance is starting",
    "current_state": "STARTING",
    "instance_id": "ocid1...",  # opcional
}
```

### Error Técnico (convertido por decorator):
```python
{
    "error": "ServiceError: 404 NotFound - Instance not found"
}
```

---

## 5. Checklist para Desarrolladores

Al escribir una función tool:

- [ ] **Validaciones de parámetros**: Lanzar `ValueError` si parámetros inválidos
- [ ] **Llamadas OCI**: NO usar try/except, dejar que excepciones se propaguen
- [ ] **Estados de negocio**: Verificar condiciones y retornar dict con "success"
- [ ] **Logging**: Solo `logger.info()` para operaciones exitosas
- [ ] **No loguear excepciones**: El decorador ya lo hace

### Ejemplo Correcto:
```python
def terminate_instance(compute_client, instance_id, preserve_boot_volume=False):
    """Terminate an instance."""

    # Validación - error técnico
    if not instance_id:
        raise ValueError("instance_id is required")

    # Obtener instancia - puede lanzar ServiceError (404, 401, etc)
    instance = compute_client.get_instance(instance_id).data

    # Estado de negocio
    if instance.lifecycle_state == "TERMINATED":
        return {
            "success": True,
            "already_terminated": True,
            "message": "Instance already terminated"
        }

    # Operación - puede lanzar excepción
    compute_client.terminate_instance(instance_id, preserve_boot_volume)

    logger.info(f"Initiated termination of instance {instance_id}")

    return {
        "success": True,
        "message": "Instance termination initiated",
        "instance_id": instance_id
    }
```

---

## 6. Tipos de Excepciones OCI Comunes

- `oci.exceptions.ServiceError`: Error de API OCI (404, 401, 403, 500, etc)
- `oci.exceptions.RequestException`: Error de red/timeout
- `oci.exceptions.ConfigFileNotFound`: Configuración OCI no encontrada
- `oci.exceptions.InvalidConfig`: Configuración OCI inválida

**Todas deben propagarse** (no capturar)

---

## 7. Anti-patrones a Evitar

### ❌ MAL: Capturar y retornar error dict
```python
def get_instance(client, instance_id):
    try:
        instance = client.get_instance(instance_id).data
        return {"success": True, "data": instance}
    except Exception as e:
        return {"success": False, "error": str(e)}  # ❌ NO!
```

### ✅ BIEN: Dejar que excepción se propague
```python
def get_instance(client, instance_id):
    instance = client.get_instance(instance_id).data
    return {
        "id": instance.id,
        "name": instance.display_name,
        ...
    }
    # Si falla, el decorador captura la excepción
```

---

## 8. Testing

### Test Error Técnico:
```python
def test_get_instance_not_found():
    with pytest.raises(oci.exceptions.ServiceError) as exc:
        get_instance(mock_client, "invalid-id")
    assert exc.value.status == 404
```

### Test Estado de Negocio:
```python
def test_start_instance_already_running():
    result = start_instance(mock_client, "running-instance-id")
    assert result["success"] is True
    assert result["already_running"] is True
```
