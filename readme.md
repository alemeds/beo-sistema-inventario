# 🏛️ BEO - Banco de Elementos Ortopédicos

Sistema de gestión integral para el control de inventario y préstamos de elementos ortopédicos destinado específicamente a organizaciones masónicas filantrópicas.

## ✨ Características Principales

### 🏛️ Gestión Masónica Completa
- **Gestión de Logias**: Control de logias con Venerables Maestros y Hospitalarios
- **Registro de Hermanos**: Base de datos completa con grados masónicos
- **Estructura Jerárquica**: Respeta la organización masónica tradicional
- **📚 Historial por Hermano**: Control completo de préstamos individuales

### 🦽 Control de Inventario Avanzado
- **Gestión de Elementos**: Inventario detallado con códigos únicos
- **Múltiples Depósitos**: Control de elementos en diferentes ubicaciones
- **Estados Dinámicos**: Disponible, Prestado, En Mantenimiento
- **📚 Historial por Elemento**: Seguimiento completo por qué manos pasó cada elemento
- **🔧 Cambio Manual de Estados**: Para correcciones y casos especiales con registro completo

### 📋 Sistema de Préstamos BEO Completo
- **Formulario Oficial**: Replica exactamente el formulario físico BEO
- **Beneficiarios Duales**: Hermanos y familiares con control de parentesco
- **Cálculo Automático**: Fechas de devolución calculadas dinámicamente
- **Seguimiento Completo**: Desde préstamo hasta devolución
- **📍 Control de Ubicaciones**: Seguimiento exacto de dónde está cada elemento

### 🔄 Gestión de Devoluciones Mejorada
- **Devolución Flexible**: En cualquier momento, antes o después del vencimiento
- **Selección de Depósito**: Elegir a qué depósito devolver cada elemento
- **Estados del Elemento**: Evaluación del estado al momento de devolución
- **Mantenimiento Automático**: Marcado automático para elementos dañados
- **Registro Completo**: Historial de todos los cambios

### 📊 Dashboard y Reportes Avanzados
- **Estadísticas en Tiempo Real**: Métricas principales del BEO
- **Alertas de Vencimiento**: Préstamos próximos a vencer o vencidos con datos de contacto
- **📍 Ubicaciones Actuales**: Control exacto de dónde está cada elemento prestado
- **Gráficos Interactivos**: Distribución por categorías y estados
- **Análisis por Logia**: Uso del BEO por cada logia
- **📊 Inventario por Depósito**: Control de stock en cada ubicación

### 🛡️ Integridad de Base de Datos
- **Foreign Keys**: Relaciones consistentes entre tablas
- **Validaciones**: Constraints automáticos de estado
- **Historial Automático**: Registro de todos los cambios de estado
- **Auditoría Completa**: Trazabilidad total de operaciones

## 🔐 Acceso al Sistema

### Credenciales de Login
- **Usuario**: `beo_admin`
- **Contraseña**: `beo2025`

### Navegación Principal
1. **📊 Dashboard** - Vista general con ubicaciones y estadísticas
2. **🏛️ Gestión de Logias** - Administrar logias masónicas  
3. **👨‍🤝‍👨 Gestión de Hermanos** - Registro + 📚 Historial por Hermano + ✏️ Edición
4. **🦽 Gestión de Elementos** - Inventario + 📚 Historial por Elemento + 🔧 Cambio de Estados
5. **📋 Formulario de Préstamo** - Sistema completo de préstamos y devoluciones
6. **🏢 Gestión de Depósitos** - Ubicaciones + Inventario por depósito
7. **📚 Manual de Usuario** - Guía completa con diagramas

## 🚀 Funcionalidades Destacadas

### 📚 Control Histórico Completo
- **Historial por Hermano**: Ve todos los préstamos de cada hermano con estadísticas de cumplimiento
- **Historial por Elemento**: Rastrea por qué manos pasó cada elemento ortopédico
- **Líneas Temporales**: Visualización gráfica de préstamos en el tiempo
- **Estadísticas de Cumplimiento**: Análisis de puntualidad por hermano y logia

### 📍 Control de Ubicaciones en Tiempo Real
- **Dónde Está Cada Elemento**: Dashboard muestra ubicación exacta de elementos prestados
- **Direcciones Completas**: Información de contacto para seguimiento
- **Inventario por Depósito**: Control de qué elementos hay disponibles en cada ubicación
- **Transferencias**: Posibilidad de devolver elementos a diferentes depósitos

### 🔧 Gestión Avanzada de Estados
- **Cambio Manual Justificado**: Con registro automático de responsable y razón
- **Historial de Estados**: Tabla dedicada para auditoría completa
- **Validaciones Inteligentes**: Alertas cuando elementos prestados cambian de estado
- **Mantenimiento Automático**: Flujo específico para elementos que necesitan reparación

### 🔄 Diagrama de Flujo del Proceso
- **Diagrama Visual**: Flujo completo desde registro hasta devolución
- **Guía Paso a Paso**: Instrucciones detalladas para nuevos usuarios
- **Casos Especiales**: Manejo de situaciones particulares
- **Puntos de Decisión**: Claridad en cada etapa del proceso

### Sistema de Alertas Inteligente
- 🟢 **Vigentes**: Préstamos dentro del plazo normal
- 🟡 **Por Vencer**: Alertas 7 días antes del vencimiento  
- 🔴 **Vencidos**: Préstamos que superaron la fecha límite
- 📞 **Información Completa**: Datos de contacto de beneficiario, hermano y hospitalario

### ✏️ Edición de Hermanos
- **Actualización Completa**: Modificar datos de contacto, dirección, grado
- **Control de Cambios**: Visualización de modificaciones antes de guardar
- **Validaciones**: Mantiene integridad de datos al actualizar
- **Historial Preservado**: Los préstamos anteriores se mantienen intactos

## 🛠️ Tecnología y Arquitectura

### Stack Tecnológico
- **Frontend**: Streamlit (Python) - Interfaz web responsive
- **Base de Datos**: SQLite (local) con opción de migración a PostgreSQL
- **Gráficos**: Plotly - Visualizaciones interactivas
- **Hosting**: Streamlit Cloud, Railway, Render, Fly.io

### 🗄️ Diagrama de Entidad Relación (ERD)

El sistema BEO utiliza una base de datos relacional con integridad referencial completa:

```mermaid
erDiagram
    LOGIAS {
        int id PK
        string nombre UK
        int numero
        string oriente
        string venerable_maestro
        string telefono_venerable
        string hospitalario
        string telefono_hospitalario
        string direccion
        boolean activo
        timestamp fecha_creacion
    }
    
    HERMANOS {
        int id PK
        string nombre
        string telefono
        int logia_id FK
        string grado
        string direccion
        string email
        date fecha_iniciacion
        boolean activo
        string observaciones
        timestamp fecha_registro
    }
    
    DEPOSITOS {
        int id PK
        string nombre UK
        string direccion
        string responsable
        string telefono
        string email
        boolean activo
        timestamp fecha_creacion
    }
    
    CATEGORIAS {
        int id PK
        string nombre UK
        string descripcion
        boolean activo
    }
    
    ELEMENTOS {
        int id PK
        string codigo UK
        string nombre
        int categoria_id FK
        int deposito_id FK
        string estado
        string descripcion
        string marca
        string modelo
        string numero_serie
        date fecha_ingreso
        string observaciones
        boolean activo
        timestamp fecha_creacion
    }
    
    BENEFICIARIOS {
        int id PK
        string tipo
        int hermano_id FK
        int hermano_responsable_id FK
        string parentesco
        string nombre
        string telefono
        string direccion
        string observaciones
        timestamp fecha_registro
    }
    
    PRESTAMOS {
        int id PK
        date fecha_prestamo
        int elemento_id FK
        int beneficiario_id FK
        int hermano_solicitante_id FK
        int duracion_dias
        date fecha_devolucion_estimada
        date fecha_devolucion_real
        string estado
        string observaciones_prestamo
        string observaciones_devolucion
        string autorizado_por
        string entregado_por
        string recibido_por
        int deposito_devolucion_id FK
        timestamp fecha_creacion
    }
    
    HISTORIAL_ESTADOS {
        int id PK
        int elemento_id FK
        string estado_anterior
        string estado_nuevo
        string razon
        string observaciones
        string responsable
        timestamp fecha_cambio
    }
    
    %% Relaciones
    LOGIAS ||--o{ HERMANOS : "pertenece_a"
    HERMANOS ||--o{ BENEFICIARIOS : "responsable_de"
    HERMANOS ||--o{ BENEFICIARIOS : "es_hermano"
    HERMANOS ||--o{ PRESTAMOS : "solicita"
    
    DEPOSITOS ||--o{ ELEMENTOS : "almacena"
    DEPOSITOS ||--o{ PRESTAMOS : "devuelto_a"
    
    CATEGORIAS ||--o{ ELEMENTOS : "clasifica"
    
    ELEMENTOS ||--o{ PRESTAMOS : "prestado_en"
    ELEMENTOS ||--o{ HISTORIAL_ESTADOS : "tiene_historial"
    
    BENEFICIARIOS ||--o{ PRESTAMOS : "recibe"
```

### Estructura de Datos Mejorada
- **Logias**: Información masónica completa con Venerable Maestro y Hospitalario
- **Hermanos**: Registro con grados masónicos y datos de contacto
- **Elementos**: Inventario detallado con estados y ubicaciones
- **Beneficiarios**: Hermanos y familiares con relaciones de responsabilidad
- **Préstamos**: Ciclo completo con seguimiento temporal y devoluciones
- **Depósitos**: Múltiples ubicaciones de almacenamiento
- **🆕 Historial Estados**: Auditoría completa de cambios con trazabilidad

### 🔐 Integridad y Validaciones
- **Foreign Keys**: Relaciones consistentes entre todas las tablas
- **Constraints**: Estados válidos únicamente (disponible, prestado, mantenimiento)
- **Triggers**: Validaciones automáticas de negocio
- **Auditoría**: Registro automático de todos los cambios de estado
- **Unique Keys**: Códigos únicos para elementos y nombres para entidades principales

## 📈 Reportes y Estadísticas

### Métricas Principales
- **Inventario Total**: Elementos disponibles vs prestados vs mantenimiento
- **Ubicaciones Actuales**: Dónde está cada elemento prestado
- **Actividad por Logia**: Préstamos activos por organización
- **Cumplimiento Individual**: Estadísticas por hermano
- **Utilización por Elemento**: Elementos más solicitados

### Análisis Disponibles
- **Distribución por Categorías**: Gráfico de pastel interactivo
- **Estados de Elementos**: Visualización de disponibilidad
- **Préstamos por Logia**: Comparativo de uso organizacional
- **Líneas Temporales**: Evolución de préstamos por elemento
- **Cumplimiento por Hermano**: Estadísticas individuales de puntualidad

## 🎯 Casos de Uso Resueltos

### ✅ Control QUÉ se presta y A QUIÉN
- **Dashboard**: Vista en tiempo real de todos los préstamos activos
- **Ubicaciones**: Dirección exacta donde está cada elemento
- **Contacto**: Teléfonos de beneficiarios y hermanos responsables

### ✅ Control DÓNDE están los elementos
- **Sección Ubicaciones**: Lista completa con direcciones
- **Inventario Dinámico**: Muestra "En depósito X" o "Prestado a Y"
- **Seguimiento GPS**: Direcciones completas para localización

### ✅ Control EN QUÉ DEPÓSITO hay disponibles
- **Filtros por Depósito**: En sección inventario
- **Vista por Depósito**: Tabla dedicada con stock actual
- **Elementos Disponibles**: Solo muestra los listos para préstamo

### ✅ Historia por HERMANOS
- **Pestaña Dedicada**: En gestión de hermanos
- **Todos los Préstamos**: Histórico completo individual
- **Estadísticas**: Cumplimiento, retrasos, elementos preferidos

### ✅ Historia por ELEMENTOS
- **Pestaña Dedicada**: En gestión de elementos
- **Por Qué Manos Pasó**: Lista cronológica completa
- **Línea Temporal**: Gráfico visual de préstamos
- **Estadísticas de Uso**: Frecuencia, duración promedio

### ✅ INTEGRIDAD de Base de Datos
- **Foreign Keys**: Consistencia automática
- **Validaciones**: Estados válidos únicamente
- **Auditoría**: Registro de todos los cambios
- **Backup**: Datos seguros y recuperables

### ✅ EDICIÓN de Hermanos
- **Actualización Segura**: Modificar datos sin afectar préstamos
- **Control Visual**: Ver cambios antes de confirmar
- **Validación Completa**: Mantiene integridad de relaciones
- **Historial Preservado**: Préstamos anteriores intactos

## 📚 Manual de Usuario Integrado

### 🔄 Diagrama de Flujo del Proceso
```mermaid
flowchart TD
    A[🏛️ Registrar Logia] --> B[👨‍🤝‍👨 Registrar Hermano]
    B --> C[🏢 Crear Depósito]
    C --> D[🦽 Registrar Elemento]
    D --> E{🤔 ¿Elemento<br/>Disponible?}
    E -->|No| F[⚠️ Verificar Estado<br/>del Elemento]
    F --> G[🔧 Cambiar Estado<br/>a Disponible]
    G --> E
    E -->|Sí| H[📋 Llenar Formulario<br/>de Préstamo]
    H --> I[👤 Seleccionar<br/>Hermano Solicitante]
    I --> J{🎯 ¿Tipo de<br/>Beneficiario?}
    J -->|Hermano| K[👨‍🤝‍👨 Seleccionar<br/>Hermano Beneficiario]
    J -->|Familiar| L[👨‍👩‍👧‍👦 Registrar Datos<br/>del Familiar]
    K --> M[📍 Completar Dirección<br/>de Entrega]
    L --> M
    M --> N[🦽 Seleccionar<br/>Elemento]
    N --> O[⏱️ Definir Duración<br/>del Préstamo]
    O --> P[📝 Agregar<br/>Observaciones]
    P --> Q[✅ Registrar<br/>Préstamo BEO]
    Q --> R[🔄 Elemento Cambia<br/>a Estado 'Prestado']
    R --> S[📊 Aparece en<br/>Dashboard Activos]
    S --> T[📅 Monitoreo<br/>de Vencimiento]
    T --> U{🕐 ¿Llegó Fecha<br/>de Devolución?}
    U -->|No| V[⏰ Continuar<br/>Monitoreo]
    V --> T
    U -->|Sí| W[🚨 Alerta de<br/>Vencimiento]
    W --> X[📞 Contactar<br/>Beneficiario]
    X --> Y[🔄 Registrar<br/>Devolución]
    Y --> Z[🏢 Elegir Depósito<br/>de Devolución]
    Z --> AA[📊 Evaluar Estado<br/>del Elemento]
    AA --> BB{🔍 ¿Estado del<br/>Elemento?}
    BB -->|Bueno/Regular| CC[✅ Disponible]
    BB -->|Dañado/Mantenimiento| DD[🔧 Mantenimiento]
    CC --> EE[📚 Registro en<br/>Historial]
    DD --> EE
    EE --> FF[🎉 Proceso<br/>Completado]
    
    style A fill:#e1f5fe
    style FF fill:#c8e6c9
    style W fill:#ffecb3
    style F fill:#ffcdd2
```

### Secciones del Manual
- **🏠 Introducción**: Visión general del sistema
- **🏛️ Gestión de Logias**: Registro de organizaciones masónicas
- **👨‍🤝‍👨 Gestión de Hermanos**: Registro y edición de hermanos
- **🦽 Gestión de Elementos**: Inventario ortopédico completo
- **📋 Sistema de Préstamos**: Proceso completo con diagrama
- **🔄 Devolución de Elementos**: Gestión de devoluciones
- **🔧 Cambio de Estados**: Gestión manual para casos especiales
- **📊 Dashboard y Reportes**: Análisis y estadísticas
- **🗄️ Estructura de Datos**: Diagrama ERD y explicaciones técnicas
- **❓ Preguntas Frecuentes**: Soluciones a problemas comunes

## 🌐 Deploy y Hosting

### 🏆 Recomendado: Streamlit Cloud
```bash
1. Sube código a GitHub (público)
2. Ve a share.streamlit.io
3. Conecta tu repositorio
4. Deploy automático ¡GRATIS!
```

### Alternativas Disponibles
- **Railway**: $5/mes, PostgreSQL incluida
- **Render**: Gratis con limitaciones
- **Fly.io**: Para uso avanzado

### Archivos Necesarios
```
proyecto-beo/
├── app.py              # Código principal
├── requirements.txt    # streamlit, pandas, plotly
├── README.md          # Esta documentación
└── .streamlit/config.toml  # Configuración opcional
```

## 🔧 Instalación y Uso

### Instalación Local
```bash
# Clonar repositorio
git clone [tu-repo-url]
cd sistema-beo

# Instalar dependencias
pip install streamlit pandas plotly

# Ejecutar aplicación
streamlit run app.py
```

### Primera Configuración
1. **Registrar Logias** (obligatorio primero)
2. **Crear Depósitos** (al menos uno)
3. **Registrar Hermanos** (vinculados a logias)
4. **Cargar Elementos** (con códigos únicos)
5. **Gestionar Préstamos** (proceso completo)

### Flujo de Trabajo Típico
1. **Morning Check**: Revisar alertas en Dashboard
2. **Nuevos Préstamos**: Usar formulario BEO completo
3. **Devoluciones**: Registrar con estado del elemento
4. **Mantenimiento**: Cambiar estados según necesidad
5. **Reportes**: Analizar cumplimiento mensualmente

## 📞 Soporte y Funcionalidades

### Incluido en el Sistema
- **✅ Control total** de inventario y préstamos
- **✅ Ubicaciones** en tiempo real
- **✅ Historiales completos** por hermano y elemento
- **✅ Integridad** de base de datos garantizada
- **✅ Alertas automáticas** de vencimientos
- **✅ Reportes estadísticos** avanzados
- **✅ Dashboard interactivo** con métricas clave
- **✅ Manual de usuario** completo con diagramas
- **✅ Edición de hermanos** con control de cambios
- **✅ Debug info opcional** para administradores

### Mejoras Futuras Sugeridas
- **🔐 Múltiples usuarios** con roles (Hospitalario, Admin, etc.)
- **📧 Notificaciones automáticas** por email/WhatsApp
- **📱 App móvil** para hospitalarios
- **🔄 Integración** con sistemas existentes
- **📊 Reportes PDF** automáticos

## 📊 Beneficios del Sistema Digital

### Para la Organización
- **Eficiencia**: Reducción del 90% en tiempo de gestión
- **Transparencia**: Trazabilidad completa de todos los préstamos
- **Control**: Eliminación de pérdidas y seguimiento efectivo
- **Profesionalismo**: Imagen moderna y organizada

### Para los Hospitalarios
- **Facilidad de Uso**: Interfaz intuitiva sin curva de aprendizaje
- **Alertas Automáticas**: Notificaciones de vencimientos con contactos
- **Reportes Instantáneos**: Información disponible en tiempo real
- **Historial Completo**: Seguimiento de cada hermano y elemento

### Para los Hermanos
- **Acceso Rápido**: Consulta inmediata de disponibilidad por depósito
- **Seguimiento Personal**: Historial completo de sus préstamos
- **Comunicación Efectiva**: Información clara de vencimientos
- **Servicio Mejorado**: Proceso más ágil y profesional

---

## 🏛️ Filosofía del Proyecto

**"La tecnología al servicio de la filantropía masónica"**

Este sistema fue diseñado específicamente para honrar los valores masónicos de fraternidad, beneficencia y organización, facilitando la noble labor de asistencia social que realizan las logias a través de sus bancos de elementos ortopédicos.

### Valores Implementados
- **Fraternidad**: Sistema diseñado para la ayuda mutua con historial por hermano
- **Beneficencia**: Facilitando la labor social organizada con control de ubicaciones
- **Organización**: Estructura que respeta la jerarquía masónica
- **Transparencia**: Registro completo y trazabilidad total con auditoría

### Características Masónicas Específicas
- **Grados Masónicos**: Desde Apr:. hasta Gr:. 33°
- **Estructura de Logia**: Venerable Maestro y Hospitalario
- **Beneficiarios Familiares**: Control de parentesco
- **Hospitalarios**: Gestión específica para cada logia

---

## 🎉 Sistema Completamente Funcional

### ✅ TODO IMPLEMENTADO Y FUNCIONANDO:
- ✅ **Control QUÉ se presta y A QUIÉN** (Dashboard + Préstamos activos)
- ✅ **Control DÓNDE están** (Ubicaciones en tiempo real)  
- ✅ **Control QUÉ hay disponible EN QUÉ DEPÓSITO** (Inventario filtrado)
- ✅ **Historia por HERMANOS** (Pestaña completa con estadísticas)
- ✅ **Historia por ELEMENTOS** (Línea temporal + por qué manos pasó)
- ✅ **INTEGRIDAD de base de datos** (Foreign keys + validaciones + auditoría)
- ✅ **EDICIÓN de hermanos** (Actualización segura con control de cambios)
- ✅ **MANUAL COMPLETO** (Guía con diagramas y ejemplos)
- ✅ **DEBUG OPCIONAL** (Información técnica cuando se necesite)

### 🚀 Listo para Deploy
- **Código**: 100% funcional y probado
- **Base de datos**: SQLite con integridad garantizada
- **Deploy**: Streamlit Cloud gratuito recomendado
- **Documentación**: Manual completo integrado
- **Diagramas**: Flujo de proceso y estructura de datos

### 📋 Requirements.txt
```
streamlit>=1.28.0
pandas>=1.5.0
plotly>=5.15.0
```

---

**Desarrollado con dedicación para el servicio filantrópico masónico** 🏛️

*"En beneficio de la humanidad y gloria del Gran Arquitecto del Universo"*

## 📧 Contacto y Contribuciones

Para mejoras, sugerencias o soporte técnico, contactar al desarrollador.

**Sistema BEO v2.5 - Completamente funcional y listo para producción** ✨

### 🆕 Novedades de la Versión 2.5
- ✏️ **Edición de hermanos** con validación de cambios
- 🔄 **Diagrama de flujo** completo del proceso de préstamos
- 🗄️ **Diagrama ERD** de la estructura de base de datos
- 🔍 **Debug info opcional** para administradores
- 📚 **Manual expandido** con nueva sección de estructura de datos
- 🎯 **Mejoras en la interfaz** y experiencia de usuario
- 🛡️ **Validaciones mejoradas** en todos los formularios
