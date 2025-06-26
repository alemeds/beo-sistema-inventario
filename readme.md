# Sistema de Gestión de Inventario Ortopédico

Sistema web desarrollado en Python con Streamlit para gestionar el inventario de elementos ortopédicos en múltiples depósitos y controlar los préstamos a beneficiarios.

## Características Principales

- 🏢 **Gestión de Depósitos**: Administra múltiples ubicaciones de almacenamiento
- 🦽 **Inventario de Elementos**: Control completo de elementos ortopédicos (sillas de ruedas, bastones, muletas, etc.)
- 👥 **Gestión de Solicitantes**: Base de datos de beneficiarios con información completa
- 📋 **Sistema de Préstamos**: Control de préstamos y devoluciones con seguimiento temporal
- 📊 **Dashboard**: Estadísticas y reportes visuales del estado del inventario
- 🔐 **Autenticación**: Sistema básico de login para proteger el acceso

## Instalación

### Opción 1: Instalación Local

1. **Clonar o descargar el proyecto**
   ```bash
   # Si tienes git instalado
   git clone [URL_DEL_REPOSITORIO]
   cd inventario-ortopedico
   ```

2. **Crear un entorno virtual (recomendado)**
   ```bash
   python -m venv venv
   
   # En Windows
   venv\Scripts\activate
   
   # En Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   streamlit run app.py
   ```

5. **Acceder al sistema**
   - Abrir navegador en: http://localhost:8501
   - Usuario: `admin`
   - Contraseña: `admin123`

### Opción 2: Despliegue en la Nube (Gratuito)

#### Streamlit Cloud (Recomendado)
1. Subir el código a GitHub
2. Ir a [share.streamlit.io](https://share.streamlit.io)
3. Conectar con GitHub y seleccionar el repositorio
4. La aplicación se desplegará automáticamente

#### Railway
1. Crear cuenta en [Railway](https://railway.app)
2. Conectar con GitHub
3. Seleccionar el repositorio
4. Railway detectará automáticamente que es una app de Streamlit

#### Heroku (Con limitaciones gratuitas)
1. Crear cuenta en [Heroku](https://heroku.com)
2. Instalar Heroku CLI
3. Crear archivo `Procfile`:
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

## Estructura de la Base de Datos

El sistema utiliza SQLite como base de datos local con las siguientes tablas:

- **depositos**: Información de los lugares de almacenamiento
- **categorias**: Categorías de elementos ortopédicos
- **elementos**: Inventario completo de elementos
- **solicitantes**: Base de datos de beneficiarios
- **prestamos**: Registro de préstamos y devoluciones

## Uso del Sistema

### 1. Configuración Inicial

1. **Crear Depósitos**: Define las ubicaciones donde se almacenan los elementos
2. **Registrar Elementos**: Agrega el inventario con códigos únicos
3. **Registrar Solicitantes**: Crea perfiles de beneficiarios

### 2. Gestión de Préstamos

1. **Nuevo Préstamo**: Selecciona elemento y solicitante
2. **Seguimiento**: Monitorea préstamos activos y fechas de vencimiento
3. **Devoluciones**: Registra la devolución de elementos

### 3. Reportes y Estadísticas

- Dashboard con métricas principales
- Gráficos de distribución por categorías
- Alertas de préstamos próximos a vencer

## Campos del Formulario de Préstamo

Como no pudimos ver tu formulario original, incluimos estos campos estándar que puedes adaptar:

### Información del Elemento
- Código único
- Nombre/Descripción
- Categoría
- Depósito de origen
- Estado actual

### Información del Solicitante
- Nombre y Apellido
- DNI
- Teléfono y Email
- Dirección
- Obra Social

### Información del Préstamo
- Fecha de préstamo
- Fecha de devolución prevista
- Responsable que entrega
- Observaciones

## Personalización

### Modificar Categorías
Edita la lista `categorias_basicas` en el código para ajustar las categorías según tus necesidades.

### Agregar Campos
Para agregar campos adicionales:
1. Modifica las tablas en `init_database()`
2. Actualiza los formularios correspondientes
3. Ajusta las consultas SQL

### Cambiar Credenciales
Modifica la función `authenticate()` para cambiar usuario/contraseña o conectar con un sistema de autenticación más robusto.

## Backup de Datos

### Backup Manual
La base de datos SQLite se guarda en el archivo `inventario_ortopedico.db`. Copia este archivo regularmente.

### Backup Automático (Opcional)
Puedes configurar scripts para respaldar automáticamente en Google Drive, Dropbox u otros servicios cloud.

## Migración a Base de Datos en la Nube

Si necesitas una base de datos en la nube verdadera, puedes migrar a:

### PostgreSQL Gratuito
- **Supabase**: 500MB gratuitos
- **Railway**: 500MB gratuitos
- **Heroku Postgres**: 10,000 filas gratuitas

### Pasos para migrar:
1. Crear cuenta en el servicio elegido
2. Modificar `DatabaseManager` para usar PostgreSQL
3. Instalar `psycopg2-binary`
4. Actualizar string de conexión

## Soporte y Mantenimiento

### Logs y Errores
- Los errores se muestran en la interfaz
- Para debugging detallado, revisar logs de Streamlit

### Actualizaciones
- Hacer backup antes de actualizar
- Probar cambios en entorno de desarrollo

## Licencia

Este sistema está diseñado para organizaciones filantrópicas sin fines de lucro.

## Contacto

Para soporte técnico o personalizaciones adicionales, puedes contactar al desarrollador.

---

**Nota**: Este es un sistema básico que puede expandirse según las necesidades específicas de tu organización. Se recomienda hacer pruebas exhaustivas antes de usar en producción.
