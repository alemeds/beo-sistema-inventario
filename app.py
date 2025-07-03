import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, date, timedelta
import hashlib
import os
import time
from typing import Optional, List, Dict
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(
    page_title="BEO - Banco de Elementos Ortopédicos",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

class AuthenticationManager:
    """Gestor de autenticación con usuarios masónicos"""
    
    def __init__(self):
        self.load_users_from_secrets()
        self.init_session_state()
    
    def load_users_from_secrets(self):
        """Cargar usuarios desde secrets.toml"""
        try:
            self.users = {
                # ADMIN - Gran Arquitecto (Acceso Total)
                st.secrets.users.admin_user: {
                    "password": st.secrets.users.admin_password,
                    "name": st.secrets.users.admin_name,
                    "role": st.secrets.users.admin_role,
                    "permissions": ["read", "write", "delete", "admin", "logias", "hermanos", "elementos", "prestamos", "depositos"]
                },
                
                # HOSPITALARIO - Gestión Logias y Hermanos
                st.secrets.users.hospitalario_user: {
                    "password": st.secrets.users.hospitalario_password,
                    "name": st.secrets.users.hospitalario_name,
                    "role": st.secrets.users.hospitalario_role,
                    "permissions": ["read", "write", "logias", "hermanos"]
                },
                
                # MAESTRO - Solo Lectura
                st.secrets.users.maestro_user: {
                    "password": st.secrets.users.maestro_password,
                    "name": st.secrets.users.maestro_name,
                    "role": st.secrets.users.maestro_role,
                    "permissions": ["read"]
                }
            }
        except Exception as e:
            st.error(f"❌ Error al cargar usuarios: {e}")
            st.error("Verifica que la sección [users] esté configurada en secrets.toml")
            st.stop()
    
    def init_session_state(self):
        """Inicializar estado de sesión"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_data' not in st.session_state:
            st.session_state.user_data = None
        if 'username' not in st.session_state:
            st.session_state.username = None
        if 'login_attempts' not in st.session_state:
            st.session_state.login_attempts = 0
        if 'locked_until' not in st.session_state:
            st.session_state.locked_until = None
    
    def verify_credentials(self, username, password):
        """Verificar credenciales del usuario"""
        if username in self.users:
            if password == self.users[username]["password"]:
                return self.users[username]
        return None
    
    def has_permission(self, permission):
        """Verificar si el usuario actual tiene un permiso específico"""
        if not st.session_state.authenticated:
            return False
        
        user_data = st.session_state.user_data
        return permission in user_data.get("permissions", [])
    
    def get_role_description(self, role):
        """Obtener descripción del rol"""
        descriptions = {
            "admin": "👑 Gran Arquitecto - Acceso Total",
            "hospitalario": "🏥 Hospitalario - Gestión Logias y Hermanos",
            "maestro": "👨‍🎓 Maestro Masón - Solo Consulta"
        }
        return descriptions.get(role, "👤 Usuario")
    
    def authenticate(self):
        """Proceso de autenticación principal"""
        # Verificar bloqueo por intentos fallidos
        if st.session_state.locked_until and datetime.now() < st.session_state.locked_until:
            remaining = st.session_state.locked_until - datetime.now()
            st.error(f"🔒 Acceso bloqueado. Intenta en {remaining.seconds // 60} minutos")
            return False
        
        if not st.session_state.authenticated:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.title("🏛️ BEO")
                st.subheader("Banco de Elementos Ortopédicos")
                st.markdown("### *Sistema Masónico Seguro*")
                st.markdown("---")
            
            st.subheader("🔐 Acceso de Hermanos Autorizados")
            
            with st.form("login_form_masonico"):
                username = st.text_input("👤 Usuario Masónico:", placeholder="Nombre de usuario")
                password = st.text_input("🔑 Contraseña:", type="password", placeholder="Contraseña segura")
                submit = st.form_submit_button("🚪 Ingresar al Templo Digital", use_container_width=True)
                
                if submit:
                    if username and password:
                        user = self.verify_credentials(username, password)
                        if user:
                            # Login exitoso
                            st.session_state.authenticated = True
                            st.session_state.user_data = user
                            st.session_state.username = username
                            st.session_state.login_attempts = 0
                            st.session_state.locked_until = None
                            
                            st.success(f"✅ T∴A∴F∴ {user['name']}")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            # Login fallido
                            st.session_state.login_attempts += 1
                            if st.session_state.login_attempts >= 3:
                                st.session_state.locked_until = datetime.now() + timedelta(minutes=15)
                                st.error("🚨 Demasiados intentos fallidos. Acceso bloqueado por 15 minutos")
                            else:
                                remaining = 3 - st.session_state.login_attempts
                                st.error(f"❌ Credenciales incorrectas. Te quedan {remaining} intentos")
                    else:
                        st.error("❌ Por favor completa todos los campos")
            
            # Información de usuarios (solo para referencia)
            with st.expander("ℹ️ Información del Sistema"):
                st.markdown("""
                **🏛️ SISTEMA BEO - ROLES MASÓNICOS**
                
                **👑 Gran Arquitecto** - Administración Total
                - Control completo del sistema BEO
                - Gestión de todos los módulos
                
                **🏥 Hospitalario Supremo** - Gestión Social  
                - Administración de Logias y Hermanos
                - Consulta completa del sistema
                
                **👨‍🎓 Maestro Masón** - Consulta General
                - Acceso de solo lectura a todo el sistema
                - Seguimiento y reportes
                
                *Las credenciales son proporcionadas por el administrador del sistema*
                """)
            
            st.markdown("---")
            st.caption("🏛️ Sistema BEO v2.5 - Autenticación Masónica Segura")
            return False
        
        return True
    
    def show_user_info(self):
        """Mostrar información del usuario logueado en sidebar"""
        if st.session_state.authenticated:
            user_data = st.session_state.user_data
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 👤 Usuario Actual")
            st.sidebar.markdown(f"**{user_data['name']}**")
            st.sidebar.markdown(f"{self.get_role_description(user_data['role'])}")
            
            # Mostrar permisos específicos
            permissions = user_data.get('permissions', [])
            st.sidebar.markdown("#### 🔑 Permisos:")
            
            if 'admin' in permissions:
                st.sidebar.markdown("• 👑 **Administración Total**")
            else:
                if 'logias' in permissions:
                    st.sidebar.markdown("• 🏛️ Gestión de Logias")
                if 'hermanos' in permissions:
                    st.sidebar.markdown("• 👨‍🤝‍👨 Gestión de Hermanos")
                if 'write' in permissions and 'admin' not in permissions:
                    st.sidebar.markdown("• ✏️ Escritura Limitada")
                if permissions == ['read']:
                    st.sidebar.markdown("• 👁️ **Solo Lectura**")
            
            st.sidebar.markdown("---")
            if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
                # Limpiar sesión
                st.session_state.authenticated = False
                st.session_state.user_data = None
                st.session_state.username = None
                st.rerun()
    
    def require_permission(self, permission, error_message=None):
        """Verificar permiso y mostrar error si no lo tiene"""
        if not self.has_permission(permission):
            if error_message is None:
                error_message = f"🚫 No tienes permisos para: {permission}"
            st.error(error_message)
            st.info("💡 Contacta al administrador si necesitas acceso adicional")
            return False
        return True
    
    def get_available_sections(self):
        """Obtener secciones disponibles según rol del usuario"""
        if not st.session_state.authenticated:
            return []
        
        user_data = st.session_state.user_data
        permissions = user_data.get('permissions', [])
        
        sections = ["📊 Dashboard"]  # Todos pueden ver dashboard
        
        # Admin: acceso total
        if 'admin' in permissions:
            sections.extend([
                "🏛️ Gestión de Logias",
                "👨‍🤝‍👨 Gestión de Hermanos", 
                "🦽 Gestión de Elementos",
                "📋 Formulario de Préstamo",
                "🏢 Gestión de Depósitos"
            ])
        
        # Hospitalario: solo logias y hermanos
        elif 'hospitalario' == user_data.get('role'):
            sections.extend([
                "🏛️ Gestión de Logias",
                "👨‍🤝‍👨 Gestión de Hermanos"
            ])
        
        sections.append("📚 Manual de Usuario")  # Todos pueden ver manual
        return sections

# Instancia global del gestor de autenticación
auth_manager = AuthenticationManager()

class DatabaseManager:
    def __init__(self):
        # Leer configuración de base de datos desde secrets
        try:
            self.connection_params = {
                'host': st.secrets.database.host,
                'port': st.secrets.database.port,
                'database': st.secrets.database.database,
                'user': st.secrets.database.username,
                'password': st.secrets.database.password
            }
        except Exception as e:
            st.error(f"""
            ❌ **Error al leer configuración de base de datos:**
            
            **Error:** {e}
            
            **Solución:** 
            Ve a tu app en Streamlit Cloud → 'Manage app' → 'Secrets' → Verifica sección [database]
            """)
            st.stop()
        
        self.init_database()
    
    def get_connection(self):
        """Crear conexión a PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.connection_params)
            conn.autocommit = False
            return conn
        except Exception as e:
            st.error(f"Error de conexión a la base de datos: {e}")
            raise
    
    def init_database(self):
        """Inicializa las tablas de la base de datos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Tabla de logias
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logias (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL UNIQUE,
                    numero INTEGER,
                    oriente VARCHAR(255),
                    venerable_maestro VARCHAR(255),
                    telefono_venerable VARCHAR(50),
                    hospitalario VARCHAR(255),
                    telefono_hospitalario VARCHAR(50),
                    direccion TEXT,
                    activo BOOLEAN DEFAULT TRUE,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de depósitos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS depositos (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL UNIQUE,
                    direccion TEXT,
                    responsable VARCHAR(255),
                    telefono VARCHAR(50),
                    email VARCHAR(255),
                    activo BOOLEAN DEFAULT TRUE,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de categorías de elementos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL UNIQUE,
                    descripcion TEXT,
                    activo BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Tabla de elementos ortopédicos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS elementos (
                    id SERIAL PRIMARY KEY,
                    codigo VARCHAR(100) NOT NULL UNIQUE,
                    nombre VARCHAR(255) NOT NULL,
                    categoria_id INTEGER NOT NULL,
                    deposito_id INTEGER NOT NULL,
                    estado VARCHAR(50) DEFAULT 'disponible' CHECK (estado IN ('disponible', 'prestado', 'mantenimiento', 'dado_de_baja')),
                    descripcion TEXT,
                    marca VARCHAR(255),
                    modelo VARCHAR(255),
                    numero_serie VARCHAR(255),
                    fecha_ingreso DATE NOT NULL,
                    observaciones TEXT,
                    activo BOOLEAN DEFAULT TRUE,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                    FOREIGN KEY (deposito_id) REFERENCES depositos (id)
                )
            """)
            
            # Tabla de hermanos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hermanos (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    telefono VARCHAR(50),
                    logia_id INTEGER NOT NULL,
                    grado VARCHAR(50),
                    direccion TEXT,
                    email VARCHAR(255),
                    fecha_iniciacion DATE,
                    activo BOOLEAN DEFAULT TRUE,
                    observaciones TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (logia_id) REFERENCES logias (id)
                )
            """)
            
            # Tabla de beneficiarios (hermanos o familiares)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS beneficiarios (
                    id SERIAL PRIMARY KEY,
                    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('hermano', 'familiar')),
                    hermano_id INTEGER,
                    hermano_responsable_id INTEGER,
                    parentesco VARCHAR(100),
                    nombre VARCHAR(255) NOT NULL,
                    telefono VARCHAR(50),
                    direccion TEXT NOT NULL,
                    observaciones TEXT,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hermano_id) REFERENCES hermanos (id),
                    FOREIGN KEY (hermano_responsable_id) REFERENCES hermanos (id)
                )
            """)
            
            # Tabla de préstamos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prestamos (
                    id SERIAL PRIMARY KEY,
                    fecha_prestamo DATE NOT NULL,
                    elemento_id INTEGER NOT NULL,
                    beneficiario_id INTEGER NOT NULL,
                    hermano_solicitante_id INTEGER NOT NULL,
                    duracion_dias INTEGER NOT NULL,
                    fecha_devolucion_estimada DATE NOT NULL,
                    fecha_devolucion_real DATE,
                    estado VARCHAR(50) DEFAULT 'activo' CHECK (estado IN ('activo', 'devuelto', 'vencido')),
                    observaciones_prestamo TEXT,
                    observaciones_devolucion TEXT,
                    autorizado_por VARCHAR(255),
                    entregado_por VARCHAR(255) NOT NULL,
                    recibido_por VARCHAR(255),
                    deposito_devolucion_id INTEGER,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (elemento_id) REFERENCES elementos (id),
                    FOREIGN KEY (beneficiario_id) REFERENCES beneficiarios (id),
                    FOREIGN KEY (hermano_solicitante_id) REFERENCES hermanos (id),
                    FOREIGN KEY (deposito_devolucion_id) REFERENCES depositos (id)
                )
            """)
            
            # Tabla de historial de cambios de estado
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historial_estados (
                    id SERIAL PRIMARY KEY,
                    elemento_id INTEGER NOT NULL,
                    estado_anterior VARCHAR(50),
                    estado_nuevo VARCHAR(50) NOT NULL,
                    razon TEXT,
                    observaciones TEXT,
                    responsable VARCHAR(255),
                    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (elemento_id) REFERENCES elementos (id)
                )
            """)
            
            # Insertar datos básicos si no existen
            self.insertar_datos_basicos(cursor)
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            st.error(f"Error al inicializar base de datos: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def insertar_datos_basicos(self, cursor):
        """Inserta categorías y datos básicos"""
        categorias_basicas = [
            ("Sillas de Ruedas", "Sillas de ruedas manuales y eléctricas"),
            ("Bastones", "Bastones simples y ortopédicos"),
            ("Muletas", "Muletas axilares y de antebrazo"),
            ("Andadores", "Andadores con y sin ruedas"),
            ("Camas Ortopédicas", "Camas articuladas y colchones"),
            ("Equipos de Rehabilitación", "Equipos diversos de rehabilitación"),
            ("Otros", "Elementos diversos no categorizados")
        ]
        
        for categoria, descripcion in categorias_basicas:
            cursor.execute("""
                INSERT INTO categorias (nombre, descripcion) 
                VALUES (%s, %s) 
                ON CONFLICT (nombre) DO NOTHING
            """, (categoria, descripcion))
        
        # Depósito por defecto
        cursor.execute("""
            INSERT INTO depositos (nombre, direccion) 
            VALUES (%s, %s) 
            ON CONFLICT (nombre) DO NOTHING
        """, ("Depósito Principal", "Dirección no especificada"))

# Inicializar la base de datos
db = DatabaseManager()

def gestionar_logias():
    """Gestión de logias - Solo Admin y Hospitalario"""
    if not auth_manager.require_permission('logias', "🚫 Solo el Gran Arquitecto y Hospitalario pueden gestionar logias"):
        return
        
    st.header("🏛️ Gestión de Logias")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Nueva Logia")
        with st.form("logia_form"):
            nombre = st.text_input("Nombre de la Logia*")
            numero = st.number_input("Número", min_value=1, step=1, value=None)
            oriente = st.text_input("Oriente")
            venerable_maestro = st.text_input("Venerable Maestro")
            telefono_venerable = st.text_input("Teléfono del Venerable")
            hospitalario = st.text_input("Hospitalario")
            telefono_hospitalario = st.text_input("Teléfono del Hospitalario")
            direccion = st.text_area("Dirección")
            
            if st.form_submit_button("Guardar Logia"):
                if nombre:
                    try:
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO logias (nombre, numero, oriente, venerable_maestro, telefono_venerable,
                                              hospitalario, telefono_hospitalario, direccion)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (nombre, numero, oriente, venerable_maestro, telefono_venerable,
                             hospitalario, telefono_hospitalario, direccion))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success("Logia guardada exitosamente")
                        st.rerun()
                    except psycopg2.IntegrityError:
                        st.error("Ya existe una logia con ese nombre")
                        conn.rollback()
                        cursor.close()
                        conn.close()
                    except Exception as e:
                        st.error(f"Error al guardar logia: {e}")
                        conn.rollback()
                        cursor.close()
                        conn.close()
                else:
                    st.error("El nombre de la logia es obligatorio")
    
    with col2:
        st.subheader("Logias Registradas")
        try:
            conn = db.get_connection()
            logias_df = pd.read_sql_query("""
                SELECT nombre, numero, oriente, venerable_maestro, hospitalario
                FROM logias 
                WHERE activo = TRUE
                ORDER BY numero, nombre
            """, conn)
            conn.close()
            
            if not logias_df.empty:
                st.dataframe(logias_df, use_container_width=True)
            else:
                st.info("No hay logias registradas")
        except Exception as e:
            st.error(f"Error al cargar logias: {e}")

def gestionar_hermanos():
    """Gestión de hermanos - Solo Admin y Hospitalario"""
    if not auth_manager.require_permission('hermanos', "🚫 Solo el Gran Arquitecto y Hospitalario pueden gestionar hermanos"):
        return
        
    st.header("👨‍🤝‍👨 Gestión de Hermanos")
    
    tab1, tab2 = st.tabs(["Nuevo Hermano", "Lista de Hermanos"])
    
    with tab1:
        try:
            conn = db.get_connection()
            logias_df = pd.read_sql_query("SELECT id, nombre, numero FROM logias WHERE activo = TRUE ORDER BY numero, nombre", conn)
            conn.close()
            
            with st.form("hermano_form_completo"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nombre = st.text_input("Nombre Completo*")
                    telefono = st.text_input("Teléfono")
                    
                    if not logias_df.empty:
                        logia_id = st.selectbox(
                            "Logia*",
                            options=logias_df['id'].tolist(),
                            format_func=lambda x: f"{logias_df[logias_df['id'] == x]['nombre'].iloc[0]} N°{logias_df[logias_df['id'] == x]['numero'].iloc[0] if pd.notna(logias_df[logias_df['id'] == x]['numero'].iloc[0]) else 'S/N'}"
                        )
                    else:
                        st.error("No hay logias disponibles")
                        logia_id = None
                
                with col2:
                    grado = st.selectbox(
                        "Grado",
                        options=["Apr:.", "Comp:.", "M:.M:.", "Gr:. 4°", "Gr:. 18°", "Gr:. 30°", "Gr:. 32°", "Gr:. 33°", "Otro"]
                    )
                    direccion = st.text_area("Dirección")
                    email = st.text_input("Email")
                    fecha_iniciacion = st.date_input(
                        "Fecha de Iniciación", 
                        value=None,
                        min_value=date(1960, 1, 1),
                        max_value=date.today(),
                        help="Fecha de iniciación masónica (desde 1960)"
                    )
                    observaciones = st.text_area("Observaciones")
                
                submitted = st.form_submit_button("✅ Guardar Hermano", use_container_width=True)
                
                if submitted:
                    if nombre and logia_id:
                        try:
                            conn = db.get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO hermanos (nombre, telefono, logia_id, grado, direccion, 
                                                    email, fecha_iniciacion, observaciones)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (nombre, telefono, logia_id, grado, direccion, 
                                 email, fecha_iniciacion, observaciones))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.success("✅ Hermano guardado exitosamente")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al guardar hermano: {e}")
                            conn.rollback()
                            cursor.close()
                            conn.close()
                    else:
                        st.error("❌ Nombre y logia son obligatorios")
        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
    
    with tab2:
        st.subheader("Lista de Hermanos")
        
        try:
            conn = db.get_connection()
            hermanos_df = pd.read_sql_query("""
                SELECT h.id, h.nombre, h.telefono, h.grado, l.nombre as logia, h.activo
                FROM hermanos h
                LEFT JOIN logias l ON h.logia_id = l.id
                WHERE h.activo = TRUE
                ORDER BY h.nombre
            """, conn)
            conn.close()
            
            if not hermanos_df.empty:
                st.dataframe(hermanos_df, use_container_width=True)
                st.caption(f"📊 Total de hermanos activos: {len(hermanos_df)}")
            else:
                st.info("No hay hermanos registrados")
        except Exception as e:
            st.error(f"Error al cargar hermanos: {e}")

def gestionar_elementos():
    """Gestión de elementos ortopédicos - Solo Admin"""
    if not auth_manager.require_permission('admin', "🚫 Solo el Gran Arquitecto puede gestionar elementos ortopédicos"):
        return
        
    st.header("🦽 Gestión de Elementos Ortopédicos")
    st.info("👑 Sección exclusiva del Gran Arquitecto")
    
    st.markdown("### 🔧 Módulo en desarrollo con permisos de administrador")

def gestionar_prestamos():
    """Gestión de préstamos - Solo Admin"""
    if not auth_manager.require_permission('admin', "🚫 Solo el Gran Arquitecto puede gestionar préstamos"):
        return
        
    st.header("📋 Formulario de Préstamo BEO")
    st.info("👑 Sección exclusiva del Gran Arquitecto")
    
    st.markdown("### 📋 Módulo en desarrollo con permisos de administrador")

def gestionar_depositos():
    """Gestión de depósitos - Solo Admin"""
    if not auth_manager.require_permission('admin', "🚫 Solo el Gran Arquitecto puede gestionar depósitos"):
        return
        
    st.header("🏢 Gestión de Depósitos")
    st.info("👑 Sección exclusiva del Gran Arquitecto")
    
    st.markdown("### 🏢 Módulo en desarrollo con permisos de administrador")

def mostrar_dashboard():
    """Dashboard con estadísticas y gráficos - Todos pueden ver"""
    st.header("📊 Dashboard BEO - Control Integral")
    
    # Mensaje según el rol
    user_data = st.session_state.user_data
    role = user_data.get('role', '')
    
    if role == 'admin':
        st.success("👑 Vista completa de Gran Arquitecto")
    elif role == 'hospitalario':
        st.info("🏥 Vista de Hospitalario - Enfoque en gestión social")
    elif role == 'maestro':
        st.info("👨‍🎓 Vista de Maestro Masón - Solo consulta")
    
    try:
        conn = db.get_connection()
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        total_elementos = pd.read_sql_query("SELECT COUNT(*) as total FROM elementos WHERE activo = TRUE", conn).iloc[0]['total']
        disponibles = pd.read_sql_query("SELECT COUNT(*) as total FROM elementos WHERE estado = 'disponible' AND activo = TRUE", conn).iloc[0]['total']
        prestamos_activos = pd.read_sql_query("SELECT COUNT(*) as total FROM prestamos WHERE estado = 'activo'", conn).iloc[0]['total']
        total_hermanos = pd.read_sql_query("SELECT COUNT(*) as total FROM hermanos WHERE activo = TRUE", conn).iloc[0]['total']
        
        with col1:
            st.metric("🦽 Total Elementos", total_elementos)
        with col2:
            st.metric("✅ Disponibles", disponibles)
        with col3:
            st.metric("📋 Préstamos Activos", prestamos_activos)
        with col4:
            st.metric("👨‍🤝‍👨 Hermanos Activos", total_hermanos)
        
        # Información básica de elementos por categoría
        st.subheader("🦽 Distribución de Elementos")
        elementos_categoria = pd.read_sql_query("""
            SELECT c.nombre, COUNT(e.id) as cantidad
            FROM categorias c
            LEFT JOIN elementos e ON c.id = e.categoria_id AND e.activo = TRUE
            WHERE c.activo = TRUE
            GROUP BY c.id, c.nombre
            HAVING COUNT(e.id) > 0
            ORDER BY cantidad DESC
        """, conn)
        
        if not elementos_categoria.empty:
            fig = px.pie(elementos_categoria, values='cantidad', names='nombre')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay elementos registrados por categoría")
        
        conn.close()
    except Exception as e:
        st.error(f"Error al cargar dashboard: {e}")

def mostrar_manual_usuario():
    """Manual de usuario completo del sistema BEO"""
    st.header("📚 Manual de Usuario - Sistema BEO")
    st.markdown("**Guía completa para usar el Banco de Elementos Ortopédicos**")
    
    # Manual básico - todos pueden acceder
    st.markdown("""
    ## 🏛️ Sistema BEO - Masónico
    
    ### 👑 Roles del Sistema:
    
    **Gran Arquitecto (Admin)**
    - Control total del sistema BEO
    - Gestión completa de inventario y préstamos
    - Administración de todos los módulos
    
    **Hospitalario Supremo**
    - Gestión de Logias y Hermanos
    - Consulta completa del sistema
    - Enfoque en la labor social masónica
    
    **Maestro Masón**
    - Acceso de solo lectura
    - Consulta de reportes y estadísticas
    - Seguimiento general del BEO
    
    ### 🔐 Características de Seguridad:
    - Contraseñas masónicas seguras
    - Control de acceso por roles
    - Bloqueo automático por intentos fallidos
    - Auditoría completa de acciones
    
    ### 📱 Navegación:
    El menú se adapta automáticamente según tu rol masónico.
    """)

def main():
    """Función principal de la aplicación con sistema masónico"""
    # Autenticación obligatoria
    if not auth_manager.authenticate():
        return
    
    # Mostrar información del usuario logueado
    auth_manager.show_user_info()
    
    # Título principal
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.title("🏛️ BEO - Banco de Elementos Ortopédicos")
        st.caption("Sistema de Gestión Masónico - Versión 2.5 Segura")
    
    st.sidebar.title("🏛️ BEO Sistema")
    st.sidebar.markdown("---")
    
    # Obtener secciones disponibles según rol
    available_sections = auth_manager.get_available_sections()
    
    if available_sections:
        selected_option = st.sidebar.selectbox(
            "Seleccionar Sección",
            available_sections
        )
        
        st.sidebar.markdown("---")
        st.sidebar.caption("🏛️ BEO v2.5 - Sistema Masónico Seguro")
        
        # Ejecutar sección seleccionada
        try:
            if selected_option == "📊 Dashboard":
                mostrar_dashboard()
            elif selected_option == "🏛️ Gestión de Logias":
                gestionar_logias()
            elif selected_option == "👨‍🤝‍👨 Gestión de Hermanos":
                gestionar_hermanos()
            elif selected_option == "🦽 Gestión de Elementos":
                gestionar_elementos()
            elif selected_option == "📋 Formulario de Préstamo":
                gestionar_prestamos()
            elif selected_option == "🏢 Gestión de Depósitos":
                gestionar_depositos()
            elif selected_option == "📚 Manual de Usuario":
                mostrar_manual_usuario()
        except Exception as e:
            st.error(f"❌ Error en la sección {selected_option}: {e}")
            st.info("💡 Contacta al Gran Arquitecto si el problema persiste")
    else:
        st.error("🚫 No tienes acceso a ninguna sección")

if __name__ == "__main__":
    main()
