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

class DatabaseManager:
    def __init__(self):
        # Usar secrets de Streamlit o variables de entorno
        if hasattr(st, 'secrets') and 'database' in st.secrets:
            self.connection_params = {
                'host': st.secrets.database.host,
                'port': st.secrets.database.port,
                'database': st.secrets.database.database,
                'user': st.secrets.database.username,
                'password': st.secrets.database.password
            }
        else:
            # Fallback para desarrollo local
            self.connection_params = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'beo_inventario'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'password')
            }
        
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

def authenticate():
    """Sistema de autenticación básico"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🏛️ BEO")
            st.subheader("Banco de Elementos Ortopédicos")
            st.markdown("---")
        
        st.subheader("🔐 Iniciar Sesión")
        
        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Ingresar al Sistema")
            
            if submit:
                if username == "beo_admin" and password == "beo2025":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
        
        st.info("👤 Usuario: beo_admin | 🔑 Contraseña: beo2025")
        st.markdown("---")
        st.caption("Sistema de Gestión del Banco de Elementos Ortopédicos v2.5 - PostgreSQL")
        return False
    
    return True

def mostrar_manual_usuario():
    """Manual de usuario completo del sistema BEO"""
    st.header("📚 Manual de Usuario - Sistema BEO")
    st.markdown("**Guía completa para usar el Banco de Elementos Ortopédicos**")
    
    # Índice de contenidos en el sidebar
    st.sidebar.markdown("### 📋 Índice del Manual")
    seccion = st.sidebar.radio(
        "Seleccionar Sección:",
        [
            "🏠 Introducción",
            "🏛️ Gestión de Logias", 
            "👨‍🤝‍👨 Gestión de Hermanos",
            "🦽 Gestión de Elementos",
            "📋 Sistema de Préstamos",
            "🔄 Devolución de Elementos",
            "🔧 Cambio de Estados",
            "📊 Dashboard y Reportes",
            "🗄️ Estructura de Datos",
            "❓ Preguntas Frecuentes"
        ]
    )
    
    if seccion == "🏠 Introducción":
        st.markdown("""
        ## 🏠 Introducción al Sistema BEO
        
        ### ¿Qué es el Sistema BEO?
        El **Banco de Elementos Ortopédicos (BEO)** es un sistema digital diseñado específicamente para organizaciones masónicas filantrópicas que administran préstamos de elementos ortopédicos a hermanos y sus familias.
        
        ### 🎯 Objetivos del Sistema
        - **Organizar** el inventario de elementos ortopédicos
        - **Controlar** los préstamos y devoluciones
        - **Facilitar** la búsqueda y seguimiento de elementos
        - **Generar** reportes y estadísticas
        - **Mantener** un registro histórico completo
        
        ### 🏛️ Estructura Masónica
        El sistema está diseñado considerando la estructura masónica:
        - **Logias** con sus Venerables Maestros y Hospitalarios
        - **Hermanos** con sus grados masónicos
        - **Beneficiarios** (hermanos y familiares)
        - **Seguimiento** por logia y hermano responsable
        
        ### 🔐 Credenciales de Acceso
        - **Usuario:** `beo_admin`
        - **Contraseña:** `beo2025`
        
        ### 📱 Navegación Principal
        El sistema se organiza en las siguientes secciones:
        1. **Dashboard** - Vista general y estadísticas
        2. **Gestión de Logias** - Administrar logias masónicas
        3. **Gestión de Hermanos** - Registro de hermanos
        4. **Gestión de Elementos** - Inventario ortopédico
        5. **Formulario de Préstamo** - Gestión completa de préstamos
        6. **Gestión de Depósitos** - Ubicaciones de almacenamiento
        7. **Manual de Usuario** - Esta guía
        """)
    # ... resto del manual igual ...

def gestionar_logias():
    """Gestión de logias"""
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
    """Gestión de hermanos"""
    st.header("👨‍🤝‍👨 Gestión de Hermanos")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Nuevo Hermano", "Lista de Hermanos", "✏️ Editar Hermano", "📚 Historial por Hermano"])
    
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
    
    # Resto de tabs similar, adaptando queries...

def gestionar_elementos():
    """Gestión de elementos ortopédicos - Adaptado para PostgreSQL"""
    st.header("🦽 Gestión de Elementos Ortopédicos")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Nuevo Elemento", "Inventario", "🔧 Cambiar Estado", "📚 Historial por Elemento"])
    
    with tab1:
        try:
            conn = db.get_connection()
            depositos_df = pd.read_sql_query("SELECT id, nombre FROM depositos WHERE activo = TRUE", conn)
            categorias_df = pd.read_sql_query("SELECT id, nombre FROM categorias WHERE activo = TRUE", conn)
            conn.close()
            
            with st.form("elemento_form_completo"):
                col1, col2 = st.columns(2)
                
                with col1:
                    codigo = st.text_input("Código del Elemento*")
                    nombre = st.text_input("Nombre del Elemento*")
                    
                    if not categorias_df.empty:
                        categoria_id = st.selectbox(
                            "Categoría*",
                            options=categorias_df['id'].tolist(),
                            format_func=lambda x: categorias_df[categorias_df['id'] == x]['nombre'].iloc[0]
                        )
                    else:
                        st.error("No hay categorías disponibles")
                        categoria_id = None
                    
                    if not depositos_df.empty:
                        deposito_id = st.selectbox(
                            "Depósito*",
                            options=depositos_df['id'].tolist(),
                            format_func=lambda x: depositos_df[depositos_df['id'] == x]['nombre'].iloc[0]
                        )
                    else:
                        st.error("No hay depósitos disponibles")
                        deposito_id = None
                
                with col2:
                    descripcion = st.text_area("Descripción")
                    marca = st.text_input("Marca")
                    modelo = st.text_input("Modelo")
                    numero_serie = st.text_input("Número de Serie")
                    fecha_ingreso = st.date_input("Fecha de Ingreso", value=date.today())
                    observaciones = st.text_area("Observaciones")
                
                submitted = st.form_submit_button("🦽 Guardar Elemento", use_container_width=True)
                
                if submitted:
                    if codigo and nombre and categoria_id and deposito_id:
                        try:
                            conn = db.get_connection()
                            cursor = conn.cursor()
                            
                            # Insertar elemento
                            cursor.execute("""
                                INSERT INTO elementos 
                                (codigo, nombre, categoria_id, deposito_id, descripcion, marca, 
                                 modelo, numero_serie, fecha_ingreso, observaciones)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                RETURNING id
                            """, (codigo, nombre, categoria_id, deposito_id, descripcion, 
                                 marca, modelo, numero_serie, fecha_ingreso, observaciones))
                            
                            elemento_id = cursor.fetchone()[0]
                            
                            # Registrar en historial de estados
                            cursor.execute("""
                                INSERT INTO historial_estados 
                                (elemento_id, estado_anterior, estado_nuevo, razon, responsable)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (elemento_id, None, 'disponible', 'Ingreso inicial', 'Sistema'))
                            
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.success("✅ Elemento guardado exitosamente")
                            st.rerun()
                            
                        except psycopg2.IntegrityError:
                            st.error("❌ Ya existe un elemento con ese código")
                            conn.rollback()
                            cursor.close()
                            conn.close()
                        except Exception as e:
                            st.error(f"❌ Error al guardar elemento: {e}")
                            conn.rollback()
                            cursor.close()
                            conn.close()
                    else:
                        st.error("❌ Todos los campos marcados con * son obligatorios")
        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
    
    # Resto de tabs similar...

def gestionar_prestamos():
    """Gestión de préstamos - Adaptado para PostgreSQL"""
    st.header("📋 Formulario de Préstamo BEO")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Nuevo Préstamo", "Préstamos Activos", "🔄 Devolución", "Historial"])
    
    with tab2:
        st.subheader("📋 Préstamos Activos - Monitoreo Completo")
        
        try:
            conn = db.get_connection()
            # Query adaptada para PostgreSQL (usando EXTRACT en lugar de JULIANDAY)
            prestamos_activos = pd.read_sql_query("""
                SELECT p.id, e.codigo, e.nombre as elemento, 
                       b.nombre as beneficiario, b.tipo, b.telefono, b.direccion as ubicacion_actual,
                       h.nombre as hermano_solicitante,
                       l.nombre as logia,
                       p.fecha_prestamo, p.fecha_devolucion_estimada, p.entregado_por,
                       CASE 
                           WHEN CURRENT_DATE > p.fecha_devolucion_estimada THEN 'VENCIDO'
                           WHEN (p.fecha_devolucion_estimada - INTERVAL '7 days') <= CURRENT_DATE THEN 'POR VENCER'
                           ELSE 'VIGENTE'
                       END as estado_vencimiento,
                       (p.fecha_devolucion_estimada - CURRENT_DATE) as dias_restantes
                FROM prestamos p
                JOIN elementos e ON p.elemento_id = e.id
                JOIN beneficiarios b ON p.beneficiario_id = b.id
                JOIN hermanos h ON p.hermano_solicitante_id = h.id
                LEFT JOIN logias l ON h.logia_id = l.id
                WHERE p.estado = 'activo'
                ORDER BY p.fecha_devolucion_estimada ASC
            """, conn)
            
            if not prestamos_activos.empty:
                st.markdown("#### 🔍 Vista Completa de Préstamos Activos con Ubicaciones")
                
                # Aplicar colores según estado de vencimiento
                def highlight_vencimiento(row):
                    if row['estado_vencimiento'] == 'VENCIDO':
                        return ['background-color: #ffebee'] * len(row)
                    elif row['estado_vencimiento'] == 'POR VENCER':
                        return ['background-color: #fff3e0'] * len(row)
                    else:
                        return ['background-color: #e8f5e8'] * len(row)
                
                styled_df = prestamos_activos.style.apply(highlight_vencimiento, axis=1)
                st.dataframe(styled_df, use_container_width=True)
                
                # Resumen de estados
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    total_activos = len(prestamos_activos)
                    st.metric("📋 Total Activos", total_activos)
                with col2:
                    vigentes = len(prestamos_activos[prestamos_activos['estado_vencimiento'] == 'VIGENTE'])
                    st.metric("✅ Vigentes", vigentes)
                with col3:
                    por_vencer = len(prestamos_activos[prestamos_activos['estado_vencimiento'] == 'POR VENCER'])
                    st.metric("⚠️ Por Vencer", por_vencer)
                with col4:
                    vencidos = len(prestamos_activos[prestamos_activos['estado_vencimiento'] == 'VENCIDO'])
                    st.metric("🚨 Vencidos", vencidos)
            else:
                st.info("ℹ️ No hay préstamos activos en este momento")
            
            conn.close()
        except Exception as e:
            st.error(f"Error al cargar préstamos activos: {e}")
    
    # Resto de tabs similar...

def gestionar_depositos():
    """Gestión de depósitos - Adaptado para PostgreSQL"""
    st.header("🏢 Gestión de Depósitos")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Nuevo Depósito")
        with st.form("deposito_form"):
            nombre = st.text_input("Nombre del Depósito*")
            direccion = st.text_area("Dirección")
            responsable = st.text_input("Responsable")
            telefono = st.text_input("Teléfono")
            email = st.text_input("Email")
            
            if st.form_submit_button("Guardar Depósito"):
                if nombre:
                    try:
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO depositos (nombre, direccion, responsable, telefono, email)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (nombre, direccion, responsable, telefono, email))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        st.success("Depósito guardado exitosamente")
                        st.rerun()
                    except psycopg2.IntegrityError:
                        st.error("Ya existe un depósito con ese nombre")
                        conn.rollback()
                        cursor.close()
                        conn.close()
                    except Exception as e:
                        st.error(f"Error al guardar depósito: {e}")
                        conn.rollback()
                        cursor.close()
                        conn.close()
                else:
                    st.error("El nombre del depósito es obligatorio")
    
    with col2:
        st.subheader("Depósitos Registrados")
        try:
            conn = db.get_connection()
            depositos_df = pd.read_sql_query("SELECT * FROM depositos WHERE activo = TRUE ORDER BY nombre", conn)
            
            if not depositos_df.empty:
                # Mostrar tabla de depósitos
                depositos_display = depositos_df[['nombre', 'direccion', 'responsable', 'telefono', 'email']].copy()
                st.dataframe(depositos_display, use_container_width=True)
                
                # Mostrar inventario por depósito
                st.subheader("📦 Inventario por Depósito")
                inventario_depositos = pd.read_sql_query("""
                    SELECT 
                        d.nombre as deposito, 
                        e.estado, 
                        COUNT(*) as cantidad
                    FROM depositos d
                    LEFT JOIN elementos e ON d.id = e.deposito_id AND e.activo = TRUE
                    WHERE d.activo = TRUE
                    GROUP BY d.id, d.nombre, e.estado
                    ORDER BY d.nombre, e.estado
                """, conn)
                
                if not inventario_depositos.empty:
                    # Crear pivot table para mejor visualización
                    try:
                        pivot_inventario = inventario_depositos.pivot(index='deposito', columns='estado', values='cantidad').fillna(0)
                        # Convertir a enteros
                        for col in pivot_inventario.columns:
                            pivot_inventario[col] = pivot_inventario[col].astype(int)
                        st.dataframe(pivot_inventario, use_container_width=True)
                        
                        # Gráfico de inventario por depósito
                        fig = px.bar(
                            inventario_depositos, 
                            x='deposito', 
                            y='cantidad', 
                            color='estado',
                            title="Distribución de Elementos por Depósito",
                            color_discrete_map={
                                'disponible': 'green',
                                'prestado': 'orange', 
                                'mantenimiento': 'red'
                            }
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning("Error al crear pivot table del inventario")
                        st.dataframe(inventario_depositos, use_container_width=True)
                else:
                    st.info("No hay elementos registrados en los depósitos")
            else:
                st.info("No hay depósitos registrados")
            
            conn.close()
        except Exception as e:
            st.error(f"Error al cargar depósitos: {e}")

def mostrar_dashboard():
    """Dashboard con estadísticas y gráficos - Adaptado para PostgreSQL"""
    st.header("📊 Dashboard BEO - Control Integral")
    
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
        
        # Alertas de vencimiento mejoradas
        st.subheader("🚨 Alertas de Vencimiento - Control Detallado")
        # Query adaptada para PostgreSQL
        alertas_vencimiento = pd.read_sql_query("""
            SELECT e.codigo, e.nombre as elemento, 
                   b.nombre as beneficiario, b.telefono, b.direccion as ubicacion,
                   h.nombre as hermano_solicitante, h.telefono as telefono_hermano,
                   l.nombre as logia, l.hospitalario, l.telefono_hospitalario,
                   p.fecha_prestamo, p.fecha_devolucion_estimada,
                   (CURRENT_DATE - p.fecha_devolucion_estimada) as dias_vencido,
                   CASE 
                       WHEN CURRENT_DATE > p.fecha_devolucion_estimada THEN 'VENCIDO'
                       WHEN (p.fecha_devolucion_estimada - INTERVAL '7 days') <= CURRENT_DATE THEN 'POR VENCER'
                       ELSE 'VIGENTE'
                   END as estado_alerta
            FROM prestamos p
            JOIN elementos e ON p.elemento_id = e.id
            JOIN beneficiarios b ON p.beneficiario_id = b.id
            JOIN hermanos h ON p.hermano_solicitante_id = h.id
            LEFT JOIN logias l ON h.logia_id = l.id
            WHERE p.estado = 'activo' 
            AND (CURRENT_DATE > p.fecha_devolucion_estimada OR (p.fecha_devolucion_estimada - INTERVAL '7 days') <= CURRENT_DATE)
            ORDER BY p.fecha_devolucion_estimada ASC
        """, conn)
        
        if not alertas_vencimiento.empty:
            # Aplicar colores según alerta
            def highlight_alertas(row):
                if row['estado_alerta'] == 'VENCIDO':
                    return ['background-color: #ffebee'] * len(row)
                else:
                    return ['background-color: #fff3e0'] * len(row)
            
            styled_df = alertas_vencimiento.style.apply(highlight_alertas, axis=1)
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.success("✅ No hay préstamos próximos a vencer o vencidos")
        
        conn.close()
    except Exception as e:
        st.error(f"Error al cargar dashboard: {e}")

def debug_info():
    """Función de debug para verificar conexión PostgreSQL"""
    show_debug = st.sidebar.checkbox("🔍 Mostrar Debug Info", value=False, help="Activar para ver información técnica del sistema")
    
    if show_debug:
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            st.sidebar.markdown("---")
            st.sidebar.subheader("🔍 Debug Info - PostgreSQL")
            
            # Información de conexión
            st.sidebar.caption(f"🗄️ Base: {db.connection_params['database']}")
            st.sidebar.caption(f"🖥️ Host: {db.connection_params['host']}")
            
            # Contar registros en cada tabla
            tables = ['logias', 'hermanos', 'elementos', 'depositos', 'categorias', 'beneficiarios', 'prestamos']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                st.sidebar.caption(f"{table}: {count} registros")
            
            # Verificar versión PostgreSQL
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            st.sidebar.caption(f"PostgreSQL: {version.split()[1]}")
            
            cursor.close()
            conn.close()
        except Exception as e:
            st.sidebar.error(f"Debug error: {e}")

def main():
    """Función principal de la aplicación"""
    if not authenticate():
        return
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.title("🏛️ BEO - Banco de Elementos Ortopédicos")
        st.caption("Sistema de Gestión Integral - Versión 2.5 PostgreSQL")
    
    st.sidebar.title("🏛️ BEO Sistema")
    st.sidebar.markdown("---")
    
    menu_options = {
        "Dashboard": "📊",
        "Gestión de Logias": "🏛️", 
        "Gestión de Hermanos": "👨‍🤝‍👨",
        "Gestión de Elementos": "🦽",
        "Formulario de Préstamo": "📋",
        "Gestión de Depósitos": "🏢",
        "📚 Manual de Usuario": "📚"
    }
    
    selected_option = st.sidebar.selectbox(
        "Seleccionar Sección",
        list(menu_options.keys()),
        format_func=lambda x: f"{menu_options[x]} {x}"
    )
    
    # Añadir debug info opcional
    debug_info()
    
    st.sidebar.markdown("---")
    st.sidebar.caption("BEO v2.5 - PostgreSQL en Render")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.authenticated = False
        st.rerun()
    
    # Manejo de errores global para cada sección
    try:
        if selected_option == "Dashboard":
            mostrar_dashboard()
        elif selected_option == "Gestión de Logias":
            gestionar_logias()
        elif selected_option == "Gestión de Hermanos":
            gestionar_hermanos()
        elif selected_option == "Gestión de Elementos":
            gestionar_elementos()
        elif selected_option == "Formulario de Préstamo":
            gestionar_prestamos()
        elif selected_option == "Gestión de Depósitos":
            gestionar_depositos()
        elif selected_option == "📚 Manual de Usuario":
            mostrar_manual_usuario()
    except Exception as e:
        st.error(f"❌ Error en la sección {selected_option}: {e}")
        st.info("💡 Intenta recargar la página o contactar al administrador si el error persiste")

if __name__ == "__main__":
    main()
