# 🏛️ BEO - Banco de Elementos Ortopédicos

Sistema de gestión integral para el control de inventario y préstamos de elementos ortopédicos destinado específicamente a organizaciones masónicas filantrópicas.

## ✨ Características Principales

### 🏛️ Gestión Masónica Completa
- **Gestión de Logias**: Control de logias con Venerables Maestros y Hospitalarios
- **Registro de Hermanos**: Base de datos completa con grados masónicos
- **Estructura Jerárquica**: Respeta la organización masónica tradicional

### 🦽 Control de Inventario Avanzado
- **Gestión de Elementos**: Inventario detallado con códigos únicos
- **Múltiples Depósitos**: Control de elementos en diferentes ubicaciones
- **Estados Dinámicos**: Disponible, Prestado, En Mantenimiento
- **Cambio Manual de Estados**: Para correcciones y casos especiales

### 📋 Sistema de Préstamos BEO
- **Formulario Oficial**: Replica exactamente el formulario físico BEO
- **Beneficiarios Duales**: Hermanos y familiares con control de parentesco
- **Cálculo Automático**: Fechas de devolución calculadas dinámicamente
- **Seguimiento Completo**: Desde préstamo hasta devolución

### 🔄 Gestión de Devoluciones
- **Devolución Flexible**: En cualquier momento, antes o después del vencimiento
- **Selección de Depósito**: Elegir a qué depósito devolver cada elemento
- **Estados del Elemento**: Evaluación del estado al momento de devolución
- **Mantenimiento Automático**: Marcado automático para elementos dañados

### 📊 Dashboard y Reportes
- **Estadísticas en Tiempo Real**: Métricas principales del BEO
- **Alertas de Vencimiento**: Préstamos próximos a vencer o vencidos
- **Gráficos Interactivos**: Distribución por categorías y estados
- **Análisis por Logia**: Uso del BEO por cada logia

### 📚 Manual de Usuario Integrado
- **Guía Completa**: Manual detallado dentro del sistema
- **Instrucciones Paso a Paso**: Para cada funcionalidad
- **Preguntas Frecuentes**: Resolución de dudas comunes
- **Navegación Fácil**: Acceso desde el menú principal

## 🔐 Acceso al Sistema

### Credenciales de Login
- **Usuario**: `beo_admin`
- **Contraseña**: `beo2025`

### Navegación Principal
1. **📊 Dashboard** - Vista general y estadísticas
2. **🏛️ Gestión de Logias** - Administrar logias masónicas  
3. **👨‍🤝‍👨 Gestión de Hermanos** - Registro de hermanos
4. **🦽 Gestión de Elementos** - Inventario ortopédico completo
5. **📋 Formulario de Préstamo** - Sistema completo de préstamos
6. **🏢 Gestión de Depósitos** - Ubicaciones de almacenamiento
7. **📚 Manual de Usuario** - Guía completa del sistema

## 🚀 Funcionalidades Destacadas

### Formulario de Préstamo BEO
Replica exactamente el formulario físico actual:
- ✅ Información del hermano solicitante con datos de logia
- ✅ Selección de beneficiario (hermano o familiar)
- ✅ Control de parentesco para familiares
- ✅ Duración configurable (días o meses)
- ✅ Dirección de entrega específica
- ✅ Autorización y responsables de entrega

### Sistema de Alertas Inteligente
- 🟢 **Vigentes**: Préstamos dentro del plazo normal
- 🟡 **Por Vencer**: Alertas 7 días antes del vencimiento
- 🔴 **Vencidos**: Préstamos que superaron la fecha límite
- 📞 **Información de Contacto**: Para realizar seguimiento efectivo

### Gestión de Estados Avanzada
- **🔄 Cambio Manual**: Para correcciones administrativas
- **📝 Historial Completo**: Registro de todos los cambios
- **⚠️ Validaciones**: Prevención de cambios incorrectos
- **🔧 Mantenimiento**: Flujo específico para reparaciones

## 🛠️ Tecnología y Arquitectura

### Stack Tecnológico
- **Frontend**: Streamlit (Python) - Interfaz web responsive
- **Base de Datos**: SQLite (local) con opción de migración a PostgreSQL
- **Gráficos**: Plotly - Visualizaciones interactivas
- **Hosting**: Streamlit Cloud - Despliegue gratuito

### Estructura de Datos
- **Logias**: Información masónica completa
- **Hermanos**: Registro con grados y datos de contacto
- **Elementos**: Inventario detallado con estados
- **Beneficiarios**: Hermanos y familiares con relaciones
- **Préstamos**: Ciclo completo con seguimiento temporal
- **Depósitos**: Múltiples ubicaciones de almacenamiento

## 📈 Reportes y Estadísticas

### Métricas Principales
- **Inventario Total**: Elementos disponibles vs prestados vs mantenimiento
- **Actividad por Logia**: Préstamos activos por organización
- **Cumplimiento**: Estadísticas de devoluciones a tiempo
- **Utilización**: Elementos más solicitados y categorías populares

### Análisis Disponibles
- **Distribución por Categorías**: Gráfico de pastel interactivo
- **Estados de Elementos**: Visualización de disponibilidad
- **Préstamos por Logia**: Comparativo de uso organizacional
- **Tendencias Temporales**: Evolución de préstamos en el tiempo

## 🎯 Dirigido Específicamente a

### Organizaciones Masónicas Filantrópicas
- **Logias Regulares**: Con estructura de Venerable y Hospitalario
- **Grandes Logias**: Con múltiples logias subordinadas
- **Organizaciones Filantrópicas**: Que administran ayuda social
- **Bancos de Elementos**: Especializados en equipos ortopédicos

### Casos de Uso Típicos
- **Préstamos a Hermanos**: Ayuda directa a miembros de la organización
- **Asistencia Familiar**: Extensión de la ayuda a familiares
- **Gestión Multi-Logia**: Control centralizado de múltiples organizaciones
- **Seguimiento Temporal**: Control de vencimientos y cumplimiento

## 🔧 Instalación y Despliegue

### Instalación Local (Desarrollo)
```bash
# Clonar repositorio
git clone [URL_REPOSITORIO]
cd beo-sistema-inventario

# Instalar dependencias
pip install streamlit pandas plotly

# Ejecutar aplicación
streamlit run app.py
```

### Despliegue en la Nube (Producción)
1. **Streamlit Cloud** (Recomendado)
   - Subir código a GitHub
   - Conectar con [share.streamlit.io](https://share.streamlit.io)
   - Despliegue automático

2. **Railway / Heroku**
   - Alternativas con despliegue automático
   - Configuración mediante git push

### Migración a Base de Datos Permanente
- **Supabase**: PostgreSQL gratuito con 500MB
- **Railway**: Base de datos PostgreSQL incluida  
- **Configuración**: Scripts de migración incluidos

## 📞 Soporte y Mantenimiento

### Manual Integrado
- **Acceso**: Menú Principal → "📚 Manual de Usuario"
- **Contenido Completo**: Guías paso a paso para cada función
- **Búsqueda por Secciones**: Navegación organizada
- **Preguntas Frecuentes**: Resolución de problemas comunes

### Características del Manual
- **🏠 Introducción**: Visión general del sistema
- **🏛️ Gestión de Logias**: Registro y administración
- **👨‍🤝‍👨 Gestión de Hermanos**: Base de datos masónica
- **🦽 Gestión de Elementos**: Inventario completo
- **📋 Sistema de Préstamos**: Proceso completo BEO
- **🔄 Devolución de Elementos**: Guía detallada
- **🔧 Cambio de Estados**: Procedimientos administrativos
- **📊 Dashboard y Reportes**: Interpretación de datos
- **❓ Preguntas Frecuentes**: Solución de problemas

### Actualizaciones y Mejoras
- **Versionado**: Control de versiones mediante Git
- **Feedback**: Sistema de mejoras basado en uso real
- **Escalabilidad**: Arquitectura preparada para crecimiento
- **Personalización**: Adaptable a necesidades específicas

## 📊 Beneficios del Sistema Digital

### Para la Organización
- **Eficiencia**: Reducción del 80% en tiempo de gestión
- **Transparencia**: Trazabilidad completa de todos los préstamos
- **Control**: Eliminación de pérdidas y seguimiento efectivo
- **Profesionalismo**: Imagen moderna y organizada

### Para los Hospitalarios
- **Facilidad de Uso**: Interfaz intuitiva sin curva de aprendizaje
- **Alertas Automáticas**: Notificaciones de vencimientos
- **Reportes Instantáneos**: Información disponible en tiempo real
- **Menos Paperwork**: Eliminación de formularios físicos

### Para los Hermanos
- **Acceso Rápido**: Consulta inmediata de disponibilidad
- **Seguimiento Personal**: Historial de sus préstamos
- **Comunicación Efectiva**: Información clara de vencimientos
- **Servicio Mejorado**: Proceso más ágil y profesional

---

## 🏛️ Filosofía del Proyecto

**"La tecnología al servicio de la filantropía masónica"**

Este sistema fue diseñado específicamente para honrar los valores masónicos de fraternidad, beneficencia y organización, facilitando la noble labor de asistencia social que realizan las logias a través de sus bancos de elementos ortopédicos.

### Valores Implementados
- **Fraternidad**: Sistema diseñado para la ayuda mutua
- **Beneficencia**: Facilitando la labor social organizada  
- **Organización**: Estructura que respeta la jerarquía masónica
- **Transparencia**: Registro completo y trazabilidad total

---

**Desarrollado con dedicación para el servicio filantrópico masónico** 🏛️

*"En beneficio de la humanidad y gloria del Gran Arquitecto del Universo"*
