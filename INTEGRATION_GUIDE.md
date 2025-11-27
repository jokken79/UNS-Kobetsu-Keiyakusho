# 🔗 GUÍA DE INTEGRACIÓN CON SISTEMAS EXTERNOS

**Fecha:** 2025-11-27
**Versión:** 2.0.0

---

## 📋 RESUMEN

Esta guía explica cómo integrar UNS Kobetsu Keiyakusho con sistemas externos como:
- **ERP** (Enterprise Resource Planning)
- **Sistema de Nómina** (給与計算システム)
- **Sistema de Facturación** (請求システム)
- **Otros sistemas corporativos**

---

## 🎯 MÉTODOS DE INTEGRACIÓN

### 1. **WEBHOOKS** (Recomendado)

Los webhooks permiten notificaciones en tiempo real cuando ocurren eventos importantes.

#### Eventos Disponibles:

```javascript
// Eventos de contratos
"contract.created"       // Nuevo contrato creado
"contract.updated"       // Contrato actualizado
"contract.approved"      // Contrato aprobado
"contract.signed"        // Contrato firmado
"contract.activated"     // Contrato activado
"contract.expired"       // Contrato vencido
"contract.renewed"       // Contrato renovado
"contract.cancelled"     // Contrato cancelado

// Eventos de empleados
"employee.assigned"      // Empleado asignado a contrato
"employee.removed"       // Empleado removido de contrato

// Eventos de alertas
"conflict_date.approaching"  // 抵触日 cercana (30/60/90 días)
"contract.expiring"          // Contrato por vencer
"visa.expiring"              // Visa por vencer
```

#### Configurar Webhook:

```bash
POST /api/v1/webhooks
Content-Type: application/json

{
  "name": "ERP Production System",
  "url": "https://tu-erp.com/api/webhooks/contracts",
  "secret": "tu_shared_secret_aqui",
  "events": [
    "contract.approved",
    "contract.signed",
    "contract.expired"
  ],
  "custom_headers": {
    "Authorization": "Bearer tu_token_api",
    "X-Company-ID": "12345"
  },
  "max_retries": 3,
  "retry_delay_seconds": 60
}
```

#### Payload del Webhook:

Cuando ocurre un evento, se envía un POST a tu URL:

```json
{
  "event": "contract.approved",
  "timestamp": "2024-12-01T10:30:00Z",
  "data": {
    "contract_id": 123,
    "contract_number": "KOB-202412-0001",
    "factory_id": 45,
    "factory_name": "Toyota Manufacturing Plant #3",
    "employee_ids": [67, 89, 101],
    "employee_count": 3,
    "start_date": "2024-12-01",
    "end_date": "2025-11-30",
    "hourly_rate": 1500.00,
    "status": "active",
    "approved_by": "manager@company.com",
    "approved_at": "2024-12-01T10:30:00Z"
  }
}
```

#### Validar Firma HMAC:

Para asegurar que el webhook es legítimo:

```python
import hmac
import hashlib
import json

def verify_webhook(request_body, signature, secret):
    """Verificar firma HMAC del webhook"""
    # El header viene como: "sha256=abc123..."
    expected_signature = signature.split('sha256=')[1]

    # Calcular HMAC
    payload_bytes = json.dumps(request_body).encode('utf-8')
    calculated_signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    # Comparar de forma segura
    return hmac.compare_digest(calculated_signature, expected_signature)

# En tu endpoint de webhook
@app.post("/api/webhooks/contracts")
def receive_webhook(request):
    signature = request.headers.get("X-Webhook-Signature")
    body = request.json

    if verify_webhook(body, signature, "tu_shared_secret_aqui"):
        # Webhook válido
        process_event(body)
    else:
        # Webhook inválido
        return {"error": "Invalid signature"}, 401
```

---

### 2. **API REST** (Polling)

Si tu sistema no puede recibir webhooks, puedes hacer polling de la API.

#### Obtener Contratos Recientes:

```bash
GET /api/v1/kobetsu?
    status=active&
    created_after=2024-11-27T00:00:00Z&
    limit=100&
    offset=0
```

#### Obtener Empleados de un Contrato:

```bash
GET /api/v1/kobetsu/{contract_id}/employees/details
```

Respuesta:
```json
{
  "contract_id": 123,
  "contract_number": "KOB-202412-0001",
  "employees": [
    {
      "employee_id": 67,
      "employee_number": "EMP-001",
      "name": "田中 太郎",
      "hourly_rate": 1500.00,
      "individual_start_date": "2024-12-01",
      "individual_end_date": "2025-11-30"
    }
  ]
}
```

---

## 💰 INTEGRACIÓN CON SISTEMA DE NÓMINA

### Flujo Recomendado:

```
1. Kobetsu Keiyakusho → Webhook → Sistema de Nómina
2. Evento: "contract.approved" o "employee.assigned"
3. Sistema de Nómina recibe:
   - employee_ids
   - hourly_rate
   - start_date / end_date
   - factory_id (para asignación de centro de costos)
```

### Endpoint para Nómina:

```bash
# Obtener datos de empleados para nómina
GET /api/v1/employees/for-payroll?
    status=active&
    contract_status=active
```

Respuesta:
```json
{
  "employees": [
    {
      "employee_id": 67,
      "employee_number": "EMP-001",
      "name": "田中 太郎",
      "bank_name": "三菱UFJ銀行",
      "bank_branch": "新宿支店",
      "bank_account_number": "1234567",
      "bank_account_type": "普通",
      "hourly_rate": 1500.00,
      "overtime_rate": 1875.00,
      "night_shift_rate": 1875.00,
      "holiday_rate": 2250.00,
      "current_contracts": [
        {
          "contract_id": 123,
          "contract_number": "KOB-202412-0001",
          "factory_name": "Toyota Plant #3",
          "start_date": "2024-12-01",
          "end_date": "2025-11-30"
        }
      ]
    }
  ],
  "total": 1
}
```

### Webhook para Sistema de Nómina:

```bash
POST /api/v1/webhooks
{
  "name": "Payroll System Integration",
  "url": "https://payroll.company.com/api/webhooks/dispatch-contracts",
  "events": [
    "contract.approved",      // Nuevo contrato aprobado → crear asignación
    "employee.assigned",      // Empleado asignado → actualizar nómina
    "employee.removed",       // Empleado removido → finalizar asignación
    "contract.expired"        // Contrato vencido → detener pagos
  ],
  "custom_headers": {
    "Authorization": "Bearer payroll_api_token",
    "X-System-ID": "payroll-prod"
  }
}
```

### Datos que el Sistema de Nómina Debe Procesar:

```javascript
// Al recibir webhook "contract.approved"
{
  "event": "contract.approved",
  "data": {
    // Para configurar pagos
    "employee_ids": [67, 89],
    "hourly_rate": 1500.00,
    "overtime_rate": 1875.00,
    "night_shift_rate": 1875.00,
    "holiday_rate": 2250.00,

    // Para período de pago
    "start_date": "2024-12-01",
    "end_date": "2025-11-30",

    // Para centro de costos
    "factory_id": 45,
    "factory_name": "Toyota Plant #3",

    // Para tracking
    "contract_number": "KOB-202412-0001"
  }
}

// Tu sistema de nómina debe:
1. Crear/actualizar empleado en nómina
2. Configurar tarifas horarias
3. Asignar a centro de costos (factory)
4. Establecer período activo (start_date - end_date)
5. Guardar contract_number para referencia
```

---

## 📊 INTEGRACIÓN CON ERP

### Flujo Recomendado:

```
Kobetsu → Webhook → ERP
       ↓
    Crear:
    - Asignación de empleado
    - Centro de costos
    - Código de proyecto
    - Registro de horas (si ERP gestiona timesheet)
```

### Webhook para ERP:

```bash
POST /api/v1/webhooks
{
  "name": "ERP Integration",
  "url": "https://erp.company.com/api/webhooks/dispatch",
  "events": [
    "contract.created",
    "contract.approved",
    "contract.signed",
    "contract.expired",
    "employee.assigned",
    "employee.removed"
  ],
  "custom_headers": {
    "Authorization": "Bearer erp_api_key",
    "X-Company-Code": "UNS"
  }
}
```

### Exportación Masiva para ERP:

```bash
# Exportar todos los contratos activos en CSV
GET /api/v1/kobetsu/export/csv?status=active

# Exportar en Excel con múltiples hojas
GET /api/v1/reports/export/excel?
    from_date=2024-01-01&
    to_date=2024-12-31
```

---

## 🔒 AUTENTICACIÓN

### API Key Authentication:

```bash
GET /api/v1/kobetsu
Authorization: Bearer tu_api_token_aqui
```

### Obtener Token (JWT):

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "api@company.com",
  "password": "secure_password"
}
```

Respuesta:
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer"
}
```

---

## 🔄 SINCRONIZACIÓN BIDIRECCIONAL

### Escenario: Sistema de Nómina actualiza horas trabajadas

Si tu sistema de nómina gestiona timesheet (勤怠管理), puede enviar datos de vuelta:

```bash
# Endpoint para recibir horas trabajadas (implementar)
POST /api/v1/timesheets
Authorization: Bearer api_token
Content-Type: application/json

{
  "contract_id": 123,
  "employee_id": 67,
  "date": "2024-12-01",
  "regular_hours": 8.0,
  "overtime_hours": 2.0,
  "night_shift_hours": 0.0,
  "holiday_hours": 0.0,
  "total_hours": 10.0
}
```

---

## 📦 EXPORTACIÓN PARA AUDITORÍAS

### Formato del Ministerio (厚生労働省):

```bash
GET /api/v1/reports/export/government?
    year=2024&
    quarter=4
```

Genera:
- 派遣元管理台帳 (Excel/PDF)
- 派遣先管理台帳 (Excel/PDF)
- 抵触日管理簿 (Excel/PDF)
- Todos los contratos en ZIP

---

## 🧪 TESTING DE INTEGRACIÓN

### 1. Test de Webhook:

```bash
POST /api/v1/webhooks/{webhook_id}/test
```

Envía un evento de prueba a tu endpoint.

### 2. Verificar Logs:

```bash
GET /api/v1/webhooks/{webhook_id}/logs
```

Ver todos los intentos de entrega con:
- Status code
- Response time
- Éxito/fallo
- Error messages

### 3. Retry Manual:

Si un webhook falló, puedes reintentarlo:

```bash
POST /api/v1/webhooks/logs/{log_id}/retry
```

---

## 🚨 MANEJO DE ERRORES

### Códigos de Error Comunes:

```
400 - Bad Request (datos inválidos)
401 - Unauthorized (token inválido)
403 - Forbidden (sin permisos)
404 - Not Found (recurso no existe)
409 - Conflict (conflicto de datos, ej: contrato duplicado)
422 - Unprocessable Entity (validación falló)
500 - Internal Server Error
503 - Service Unavailable
```

### Retry Logic:

Los webhooks se reintentarán automáticamente:
- Máximo 3 intentos (configurable)
- Delay de 60 segundos entre intentos (configurable)
- Exponential backoff recomendado

---

## 📞 ENDPOINTS PRINCIPALES PARA INTEGRACIÓN

### Contratos:
```
GET    /api/v1/kobetsu                  # Listar contratos
GET    /api/v1/kobetsu/{id}             # Obtener contrato
POST   /api/v1/kobetsu                  # Crear contrato
GET    /api/v1/kobetsu/stats            # Estadísticas
GET    /api/v1/kobetsu/expiring         # Próximos a vencer
```

### Empleados:
```
GET    /api/v1/employees                # Listar empleados
GET    /api/v1/employees/{id}           # Obtener empleado
GET    /api/v1/employees/for-payroll    # Para nómina
```

### Fábricas:
```
GET    /api/v1/factories                # Listar fábricas
GET    /api/v1/factories/{id}           # Obtener fábrica
```

### Webhooks:
```
GET    /api/v1/webhooks                 # Listar webhooks
POST   /api/v1/webhooks                 # Crear webhook
PUT    /api/v1/webhooks/{id}            # Actualizar webhook
DELETE /api/v1/webhooks/{id}            # Eliminar webhook
GET    /api/v1/webhooks/{id}/logs       # Ver logs
POST   /api/v1/webhooks/{id}/test       # Test webhook
```

### Exportación:
```
GET    /api/v1/kobetsu/export/csv       # CSV
GET    /api/v1/reports/export/excel     # Excel
GET    /api/v1/reports/export/government # Formato官庁
```

---

## 💡 MEJORES PRÁCTICAS

### 1. **Usar Webhooks en Lugar de Polling**
- Reduce carga en servidores
- Notificaciones en tiempo real
- Más eficiente

### 2. **Validar Firma HMAC**
- Siempre valida que el webhook es legítimo
- Usa `compare_digest` para evitar timing attacks

### 3. **Implementar Idempotencia**
- Guarda `contract_id` o `contract_number` para evitar duplicados
- Usa transaction logs

### 4. **Manejo de Errores Robusto**
- Implementa retry logic
- Log todos los errores
- Notifica a admins de fallos persistentes

### 5. **Rate Limiting**
- Respeta límites de API (si los hay)
- Implementa backoff exponencial

---

## 🔗 EJEMPLOS DE CÓDIGO

### Python:

```python
import requests
import hmac
import hashlib

class KobetsuAPI:
    def __init__(self, base_url, api_token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

    def get_active_contracts(self):
        url = f"{self.base_url}/api/v1/kobetsu?status=active"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def create_webhook(self, webhook_config):
        url = f"{self.base_url}/api/v1/webhooks"
        response = requests.post(url, json=webhook_config, headers=self.headers)
        return response.json()

# Uso
api = KobetsuAPI("http://localhost:8010", "your_api_token")
contracts = api.get_active_contracts()
```

### Node.js:

```javascript
const axios = require('axios');

class KobetsuAPI {
  constructor(baseURL, apiToken) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Authorization': `Bearer ${apiToken}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async getActiveContracts() {
    const response = await this.client.get('/api/v1/kobetsu?status=active');
    return response.data;
  }

  async createWebhook(config) {
    const response = await this.client.post('/api/v1/webhooks', config);
    return response.data;
  }
}

// Uso
const api = new KobetsuAPI('http://localhost:8010', 'your_api_token');
const contracts = await api.getActiveContracts();
```

---

## 📄 LICENCIA

MIT License - Ver LICENSE file para detalles.

---

## 📞 SOPORTE

Para preguntas de integración:
- Documentación API: http://localhost:8010/docs
- Email: support@uns-kikaku.jp
- Issues: GitHub repository

---

**¡Tu sistema ahora puede integrarse perfectamente con ERP y nómina!** 🚀
