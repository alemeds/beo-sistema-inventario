import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
import hashlib
import os
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
    def __init__(self, db_path: str = "beo_inventario.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Inicializa las tablas de la base de datos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabla de logias
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                numero INTEGER,
                oriente TEXT,
                venerable_maestro TEXT,
                telefono_venerable TEXT,
                hospitalario TEXT,
                telefono_hospitalario TEXT,
                direccion TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de depósitos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS depositos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                direccion TEXT,
                responsable TEXT,
                telefono TEXT,
                email TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de categorías de elementos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT
            )
        """)
        
        # Tabla de elementos ortopédicos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS elementos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                categoria_id INTEGER,
                deposito_id INTEGER,
                estado TEXT DEFAULT 'disponible',
                descripcion TEXT,
                marca TEXT,
                modelo TEXT,
                numero_serie TEXT,
                fecha_ingreso DATE,
                observaciones TEXT,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                FOREIGN KEY (deposito_id) REFERENCES depositos (id)
            )
        """)
        
        # Tabla de hermanos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hermanos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT,
                logia_id INTEGER,
                grado TEXT,
                direccion TEXT,
                email TEXT,
                fecha_iniciacion DATE,
                activo BOOLEAN DEFAULT 1,
                observaciones TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (logia_id) REFERENCES logias (id)
            )
        """)
        
        # Tabla de beneficiarios (hermanos o familiares)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS beneficiarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL, -- 'hermano' o 'familiar'
                hermano_id INTEGER, -- si es hermano, referencia a hermanos
                hermano_responsable_id INTEGER, -- si es familiar, de qué hermano
                parentesco TEXT, -- si es familiar
                nombre TEXT NOT NULL,
                telefono TEXT,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_prestamo DATE NOT NULL,
                elemento_id INTEGER,
                beneficiario_id INTEGER,
                hermano_solicitante_id INTEGER,
                duracion_dias INTEGER,
                fecha_devolucion_estimada DATE,
                fecha_devolucion_real DATE,
                estado TEXT DEFAULT 'activo', -- 'activo', 'devuelto', 'vencido'
                observaciones_prestamo TEXT,
                observaciones_devolucion TEXT,
                autorizado_por TEXT,
                entregado_por TEXT,
                recibido_por TEXT,
                FOREIGN KEY (elemento_id) REFERENCES elementos (id),
                FOREIGN KEY (beneficiario_id) REFERENCES beneficiarios (id),
                FOREIGN KEY (hermano_solicitante_id) REFERENCES hermanos (id)
            )
        """)
        
        # Insertar categorías básicas si no existen
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
            cursor.execute("INSERT OR IGNORE INTO categorias (nombre, descripcion) VALUES (?, ?)", 
                         (categoria, descripcion))
        
        # Insertar grados masónicos básicos
        grados_masonicos = ["Apr:.", "Comp:.", "M:.M:.", "Gr:. 4°", "Gr:. 18°", "Gr:. 30°", "Gr:. 32°", "Gr:. 33°"]
        
        conn.commit()
        conn.close()

# Inicializar la base de datos
db = DatabaseManager()

def hash_password(password: str) -> str:
    """Hash de contraseña simple para autenticación básica"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate():
    """Sistema de autenticación básico"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        # Header con logo BEO
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
                # Credenciales básicas (en producción usar base de datos)
                if username == "beo_admin" and password == "beo2025":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
        
        st.info("👤 Usuario: beo_admin | 🔑 Contraseña: beo2025")
        st.markdown("---")
        st.caption("Sistema de Gestión del Banco de Elementos Ortopédicos")
        return False
    
    return True

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
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (nombre, numero, oriente, venerable_maestro, telefono_venerable,
                             hospitalario, telefono_hospitalario, direccion))
                        conn.commit()
                        conn.close()
                        st.success("Logia guardada exitosamente")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Ya existe una logia con ese nombre")
                else:
                    st.error("El nombre de la logia es obligatorio")
    
    with col2:
        st.subheader("Logias Registradas")
        conn = db.get_connection()
        logias_df = pd.read_sql_query("""
            SELECT nombre, numero, oriente, venerable_maestro, hospitalario
            FROM logias ORDER BY numero, nombre
        """, conn)
        conn.close()
        
        if not logias_df.empty:
            st.dataframe(logias_df, use_container_width=True)
        else:
            st.info("No hay logias registradas")

def gestionar_hermanos():
    """Gestión de hermanos"""
    st.header("👨‍🤝‍👨 Gestión de Hermanos")
    
    tab1, tab2 = st.tabs(["Nuevo Hermano", "Lista de Hermanos"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        # Obtener logias
        conn = db.get_connection()
        logias_df = pd.read_sql_query("SELECT id, nombre, numero FROM logias ORDER BY numero, nombre", conn)
        conn.close()
        
        # FORMULARIO UNIFICADO - SOLUCIONA EL ERROR
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
                fecha_iniciacion = st.date_input("Fecha de Iniciación", value=None)
                observaciones = st.text_area("Observaciones")
            
            # BOTÓN DE ENVÍO - ESTO FALTABA
            submitted = st.form_submit_button("✅ Guardar Hermano", use_container_width=True)
            
            if submitted:
                if nombre and logia_id:
                    try:
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO hermanos (nombre, telefono, logia_id, grado, direccion, 
                                                email, fecha_iniciacion, observaciones)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (nombre, telefono, logia_id, grado, direccion, 
                             email, fecha_iniciacion, observaciones))
                        conn.commit()
                        conn.close()
                        st.success("✅ Hermano guardado exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al guardar hermano: {e}")
                else:
                    st.error("❌ Nombre y logia son obligatorios")
    
    with tab2:
        st.subheader("Lista de Hermanos")
        
        conn = db.get_connection()
        hermanos_df = pd.read_sql_query("""
            SELECT h.id, h.nombre, h.telefono, h.grado, l.nombre as logia, h.activo
            FROM hermanos h
            LEFT JOIN logias l ON h.logia_id = l.id
            WHERE h.activo = 1
            ORDER BY h.nombre
        """, conn)
        conn.close()
        
        if not hermanos_df.empty:
            st.dataframe(hermanos_df, use_container_width=True)
        else:
            st.info("No hay hermanos registrados")

def gestionar_elementos():
    """Gestión de elementos ortopédicos"""
    st.header("🦽 Gestión de Elementos Ortopédicos")
    
    tab1, tab2 = st.tabs(["Nuevo Elemento", "Inventario"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        # Obtener depósitos y categorías
        conn = db.get_connection()
        depositos_df = pd.read_sql_query("SELECT id, nombre FROM depositos", conn)
        categorias_df = pd.read_sql_query("SELECT id, nombre FROM categorias", conn)
        conn.close()
        
        # FORMULARIO UNIFICADO - SOLUCIONA EL ERROR
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
            
            # BOTÓN DE ENVÍO - ESTO FALTABA
            submitted = st.form_submit_button("🦽 Guardar Elemento", use_container_width=True)
            
            if submitted:
                if codigo and nombre and categoria_id and deposito_id:
                    try:
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO elementos 
                            (codigo, nombre, categoria_id, deposito_id, descripcion, marca, 
                             modelo, numero_serie, fecha_ingreso, observaciones)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (codigo, nombre, categoria_id, deposito_id, descripcion, 
                             marca, modelo, numero_serie, fecha_ingreso, observaciones))
                        conn.commit()
                        conn.close()
                        st.success("✅ Elemento guardado exitosamente")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Ya existe un elemento con ese código")
                else:
                    st.error("❌ Todos los campos marcados con * son obligatorios")
    
    with tab2:
        st.subheader("Inventario de Elementos")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        conn = db.get_connection()
        
        with col1:
            categorias_df = pd.read_sql_query("SELECT id, nombre FROM categorias", conn)
            categoria_filtro = st.selectbox(
                "Filtrar por Categoría",
                options=[None] + categorias_df['id'].tolist(),
                format_func=lambda x: "Todas las categorías" if x is None else categorias_df[categorias_df['id'] == x]['nombre'].iloc[0]
            )
        
        with col2:
            depositos_df = pd.read_sql_query("SELECT id, nombre FROM depositos", conn)
            deposito_filtro = st.selectbox(
                "Filtrar por Depósito",
                options=[None] + depositos_df['id'].tolist(),
                format_func=lambda x: "Todos los depósitos" if x is None else depositos_df[depositos_df['id'] == x]['nombre'].iloc[0]
            )
        
        with col3:
            estado_filtro = st.selectbox(
                "Filtrar por Estado",
                options=[None, "disponible", "prestado", "mantenimiento"],
                format_func=lambda x: "Todos los estados" if x is None else x.title()
            )
        
        # Consulta con filtros
        query = """
            SELECT e.id, e.codigo, e.nombre, c.nombre as categoria, d.nombre as deposito, 
                   e.estado, e.marca, e.modelo
            FROM elementos e
            JOIN categorias c ON e.categoria_id = c.id
            JOIN depositos d ON e.deposito_id = d.id
            WHERE 1=1
        """
        params = []
        
        if categoria_filtro:
            query += " AND e.categoria_id = ?"
            params.append(categoria_filtro)
        
        if deposito_filtro:
            query += " AND e.deposito_id = ?"
            params.append(deposito_filtro)
        
        if estado_filtro:
            query += " AND e.estado = ?"
            params.append(estado_filtro)
        
        query += " ORDER BY e.codigo"
        
        elementos_df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not elementos_df.empty:
            st.dataframe(elementos_df, use_container_width=True)
            
            # Estadísticas rápidas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Elementos", len(elementos_df))
            with col2:
                disponibles = len(elementos_df[elementos_df['estado'] == 'disponible'])
                st.metric("Disponibles", disponibles)
            with col3:
                prestados = len(elementos_df[elementos_df['estado'] == 'prestado'])
                st.metric("Prestados", prestados)
            with col4:
                mantenimiento = len(elementos_df[elementos_df['estado'] == 'mantenimiento'])
                st.metric("En Mantenimiento", mantenimiento)
        else:
            st.info("No se encontraron elementos con los filtros aplicados")

def gestionar_prestamos():
    """Gestión de préstamos según formulario BEO"""
    st.header("📋 Formulario de Préstamo BEO")
    
    tab1, tab2, tab3 = st.tabs(["Nuevo Préstamo", "Préstamos Activos", "Devoluciones"])
    
    with tab1:
        st.subheader("📝 Nuevo Formulario de Préstamo")
        st.caption("Completar la siguiente encuesta a fin de tener un control sobre los elementos ortopédicos prestados")
        
        with st.form("prestamo_beo_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📅 Información General")
                fecha_prestamo = st.date_input("Fecha*", value=date.today())
                
                # Duración del préstamo
                st.markdown("#### ⏱️ ¿Cuál es el pedido que se solicita?")
                col_dur1, col_dur2 = st.columns(2)
                with col_dur1:
                    duracion_tipo = st.selectbox("Tipo de duración", ["Días", "Meses"])
                with col_dur2:
                    duracion_cantidad = st.number_input("Cantidad", min_value=1, value=90 if duracion_tipo == "Días" else 3)
                
                # Cálculo de días
                if duracion_tipo == "Meses":
                    duracion_dias = duracion_cantidad * 30  # Aproximación
                else:
                    duracion_dias = duracion_cantidad
                
                st.markdown("#### 👨‍🤝‍👨 Hermano que solicita el pedido")
                
                # Obtener hermanos
                conn = db.get_connection()
                hermanos_df = pd.read_sql_query("""
                    SELECT h.id, h.nombre, h.telefono, h.grado, l.nombre as logia, 
                           l.hospitalario, l.telefono_hospitalario, l.venerable_maestro, l.telefono_venerable
                    FROM hermanos h
                    LEFT JOIN logias l ON h.logia_id = l.id
                    WHERE h.activo = 1
                    ORDER BY h.nombre
                """, conn)
                
                if not hermanos_df.empty:
                    hermano_idx = st.selectbox(
                        "Seleccionar Hermano",
                        options=range(len(hermanos_df)),
                        format_func=lambda x: f"{hermanos_df.iloc[x]['nombre']} - {hermanos_df.iloc[x]['logia']} ({hermanos_df.iloc[x]['grado']})"
                    )
                    hermano_seleccionado = hermanos_df.iloc[hermano_idx]
                    hermano_solicitante_id = hermano_seleccionado['id']
                    
                    # Mostrar información del hermano
                    st.info(f"""
                    **Hermano:** {hermano_seleccionado['nombre']}  
                    **Teléfono:** {hermano_seleccionado['telefono']}  
                    **Logia:** {hermano_seleccionado['logia']}  
                    **Grado:** {hermano_seleccionado['grado']}  
                    **Hospitalario:** {hermano_seleccionado['hospitalario']} - Tel: {hermano_seleccionado['telefono_hospitalario']}  
                    **Venerable:** {hermano_seleccionado['venerable_maestro']} - Tel: {hermano_seleccionado['telefono_venerable']}
                    """)
                else:
                    st.error("No hay hermanos registrados")
                    hermano_solicitante_id = None
            
            with col2:
                st.markdown("#### 🎯 ¿A quién va dirigido el pedido de préstamo?")
                tipo_beneficiario = st.radio("¿Es Hermano o Familiar?", ["Hermano", "Familiar"])
                
                if tipo_beneficiario == "Hermano":
                    # Si es hermano, seleccionar de la lista
                    if not hermanos_df.empty:
                        hermano_beneficiario_idx = st.selectbox(
                            "Seleccionar Hermano Beneficiario",
                            options=range(len(hermanos_df)),
                            format_func=lambda x: hermanos_df.iloc[x]['nombre']
                        )
                        beneficiario_nombre = hermanos_df.iloc[hermano_beneficiario_idx]['nombre']
                        beneficiario_telefono = hermanos_df.iloc[hermano_beneficiario_idx]['telefono']
                        parentesco = None
                        hermano_responsable_id = None
                    else:
                        beneficiario_nombre = ""
                        beneficiario_telefono = ""
                        parentesco = None
                        hermano_responsable_id = None
                
                else:  # Familiar
                    st.markdown("**Si es Familiar:**")
                    parentesco = st.selectbox(
                        "Tipo de parentesco",
                        ["Madre", "Padre", "Esposa/o", "Hijo/a", "Hermano/a", "Otro"]
                    )
                    
                    if parentesco == "Otro":
                        parentesco = st.text_input("Especificar parentesco")
                    
                    # De qué hermano
                    if not hermanos_df.empty:
                        hermano_resp_idx = st.selectbox(
                            "De qué Hermano",
                            options=range(len(hermanos_df)),
                            format_func=lambda x: hermanos_df.iloc[x]['nombre'],
                            key="hermano_responsable"
                        )
                        hermano_responsable_id = hermanos_df.iloc[hermano_resp_idx]['id']
                        st.info(f"Hermano responsable: {hermanos_df.iloc[hermano_resp_idx]['nombre']}")
                    else:
                        hermano_responsable_id = None
                    
                    beneficiario_nombre = st.text_input("Nombre del Familiar*")
                    beneficiario_telefono = st.text_input("Teléfono del Familiar")
                
                st.markdown("#### 📍 Dirección")
                direccion_entrega = st.text_area("Dirección donde va dirigido el Elemento Ortopédico*")
                
                st.markdown("#### 🦽 Elemento Solicitado")
                # Elementos disponibles
                elementos_disponibles = pd.read_sql_query("""
                    SELECT e.id, e.codigo, e.nombre, c.nombre as categoria, d.nombre as deposito
                    FROM elementos e
                    JOIN categorias c ON e.categoria_id = c.id
                    JOIN depositos d ON e.deposito_id = d.id
                    WHERE e.estado = 'disponible'
                    ORDER BY e.codigo
                """, conn)
                
                if not elementos_disponibles.empty:
                    elemento_id = st.selectbox(
                        "Elemento a Prestar*",
                        options=elementos_disponibles['id'].tolist(),
                        format_func=lambda x: f"{elementos_disponibles[elementos_disponibles['id'] == x]['codigo'].iloc[0]} - {elementos_disponibles[elementos_disponibles['id'] == x]['nombre'].iloc[0]} ({elementos_disponibles[elementos_disponibles['id'] == x]['categoria'].iloc[0]})"
                    )
                else:
                    st.error("No hay elementos disponibles para préstamo")
                    elemento_id = None
                
                conn.close()
                
                # Fecha estimada de devolución
                fecha_devolucion_estimada = fecha_prestamo + pd.Timedelta(days=duracion_dias)
                st.date_input("Fecha estimada de devolución", value=fecha_devolucion_estimada, disabled=True)
                
                st.markdown("#### 📝 Observaciones")
                observaciones_prestamo = st.text_area("Observaciones del préstamo")
                
                st.markdown("#### ✅ Autorización")
                autorizado_por = st.text_input("Autorizado por")
                entregado_por = st.text_input("Entregado por*")
            
            # Botón de envío
            col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])
            with col_submit2:
                submit_prestamo = st.form_submit_button("📋 Registrar Préstamo BEO", use_container_width=True)
            
            if submit_prestamo:
                if (hermano_solicitante_id and elemento_id and beneficiario_nombre and 
                    direccion_entrega and entregado_por):
                    try:
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        
                        # Crear beneficiario
                        cursor.execute("""
                            INSERT INTO beneficiarios (tipo, hermano_id, hermano_responsable_id, 
                                                     parentesco, nombre, telefono, direccion)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (tipo_beneficiario.lower(), 
                             hermano_solicitante_id if tipo_beneficiario == "Hermano" else None,
                             hermano_responsable_id if tipo_beneficiario == "Familiar" else None,
                             parentesco, beneficiario_nombre, beneficiario_telefono, direccion_entrega))
                        
                        beneficiario_id = cursor.lastrowid
                        
                        # Registrar préstamo
                        cursor.execute("""
                            INSERT INTO prestamos 
                            (fecha_prestamo, elemento_id, beneficiario_id, hermano_solicitante_id,
                             duracion_dias, fecha_devolucion_estimada, observaciones_prestamo,
                             autorizado_por, entregado_por)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (fecha_prestamo, elemento_id, beneficiario_id, hermano_solicitante_id,
                             duracion_dias, fecha_devolucion_estimada, observaciones_prestamo,
                             autorizado_por, entregado_por))
                        
                        # Actualizar estado del elemento
                        cursor.execute("UPDATE elementos SET estado = 'prestado' WHERE id = ?", (elemento_id,))
                        
                        conn.commit()
                        conn.close()
                        st.success("✅ Préstamo BEO registrado exitosamente")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al registrar préstamo: {e}")
                else:
                    st.error("❌ Todos los campos marcados con * son obligatorios")
    
    with tab2:
        st.subheader("📋 Préstamos Activos")
        
        conn = db.get_connection()
        prestamos_activos = pd.read_sql_query("""
            SELECT p.id, e.codigo, e.nombre as elemento, 
                   b.nombre as beneficiario, b.tipo,
                   h.nombre as hermano_solicitante,
                   l.nombre as logia,
                   p.fecha_prestamo, p.fecha_devolucion_estimada, 
                   CASE 
                       WHEN DATE('now') > p.fecha_devolucion_estimada THEN 'VENCIDO'
                       WHEN DATE(p.fecha_devolucion_estimada, '-7 days') <= DATE('now') THEN 'POR VENCER'
                       ELSE 'VIGENTE'
                   END as estado_vencimiento
            FROM prestamos p
            JOIN elementos e ON p.elemento_id = e.id
            JOIN beneficiarios b ON p.beneficiario_id = b.id
            JOIN hermanos h ON p.hermano_solicitante_id = h.id
            LEFT JOIN logias l ON h.logia_id = l.id
            WHERE p.estado = 'activo'
            ORDER BY p.fecha_devolucion_estimada ASC
        """, conn)
        conn.close()
        
        if not prestamos_activos.empty:
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
            col1, col2, col3 = st.columns(3)
            with col1:
                vigentes = len(prestamos_activos[prestamos_activos['estado_vencimiento'] == 'VIGENTE'])
                st.metric("✅ Vigentes", vigentes)
            with col2:
                por_vencer = len(prestamos_activos[prestamos_activos['estado_vencimiento'] == 'POR VENCER'])
                st.metric("⚠️ Por Vencer", por_vencer)
            with col3:
                vencidos = len(prestamos_activos[prestamos_activos['estado_vencimiento'] == 'VENCIDO'])
                st.metric("🚨 Vencidos", vencidos)
        else:
            st.info("No hay préstamos activos")
    
    with tab3:
        st.subheader("↩️ Registrar Devolución")
        
        conn = db.get_connection()
        prestamos_activos = pd.read_sql_query("""
            SELECT p.id, e.codigo, e.nombre as elemento, 
                   b.nombre as beneficiario,
                   h.nombre as hermano_solicitante,
                   p.fecha_prestamo
            FROM prestamos p
            JOIN elementos e ON p.elemento_id = e.id
            JOIN beneficiarios b ON p.beneficiario_id = b.id
            JOIN hermanos h ON p.hermano_solicitante_id = h.id
            WHERE p.estado = 'activo'
            ORDER BY p.fecha_prestamo DESC
        """, conn)
        
        if not prestamos_activos.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                prestamo_id = st.selectbox(
                    "Seleccionar Préstamo a Devolver",
                    options=prestamos_activos['id'].tolist(),
                    format_func=lambda x: f"{prestamos_activos[prestamos_activos['id'] == x]['codigo'].iloc[0]} - {prestamos_activos[prestamos_activos['id'] == x]['elemento'].iloc[0]} (Beneficiario: {prestamos_activos[prestamos_activos['id'] == x]['beneficiario'].iloc[0]})"
                )
            
            with col2:
                fecha_devolucion = st.date_input("Fecha de Devolución", value=date.today())
                recibido_por = st.text_input("Recibido por*")
                observaciones_devolucion = st.text_area("Observaciones de la Devolución")
            
            if st.button("✅ Registrar Devolución"):
                if recibido_por:
                    try:
                        cursor = conn.cursor()
                        
                        # Obtener elemento_id del préstamo
                        cursor.execute("SELECT elemento_id FROM prestamos WHERE id = ?", (prestamo_id,))
                        elemento_id = cursor.fetchone()[0]
                        
                        # Actualizar préstamo
                        cursor.execute("""
                            UPDATE prestamos 
                            SET fecha_devolucion_real = ?, estado = 'devuelto',
                                observaciones_devolucion = ?, recibido_por = ?
                            WHERE id = ?
                        """, (fecha_devolucion, observaciones_devolucion, recibido_por, prestamo_id))
                        
                        # Actualizar estado del elemento
                        cursor.execute("UPDATE elementos SET estado = 'disponible' WHERE id = ?", (elemento_id,))
                        
                        conn.commit()
                        st.success("✅ Devolución registrada exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al registrar devolución: {e}")
                else:
                    st.error("❌ El campo 'Recibido por' es obligatorio")
        else:
            st.info("No hay préstamos activos para devolver")
        
        conn.close()

def gestionar_depositos():
    """Gestión de depósitos"""
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
                            VALUES (?, ?, ?, ?, ?)
                        """, (nombre, direccion, responsable, telefono, email))
                        conn.commit()
                        conn.close()
                        st.success("Depósito guardado exitosamente")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Ya existe un depósito con ese nombre")
                else:
                    st.error("El nombre del depósito es obligatorio")
    
    with col2:
        st.subheader("Depósitos Registrados")
        conn = db.get_connection()
        depositos_df = pd.read_sql_query("SELECT * FROM depositos ORDER BY nombre", conn)
        conn.close()
        
        if not depositos_df.empty:
            st.dataframe(depositos_df, use_container_width=True)
        else:
            st.info("No hay depósitos registrados")

def mostrar_dashboard():
    """Dashboard con estadísticas y gráficos"""
    st.header("📊 Dashboard BEO")
    
    conn = db.get_connection()
    
    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    
    # Total elementos
    total_elementos = pd.read_sql_query("SELECT COUNT(*) as total FROM elementos", conn).iloc[0]['total']
    
    # Elementos disponibles
    disponibles = pd.read_sql_query("SELECT COUNT(*) as total FROM elementos WHERE estado = 'disponible'", conn).iloc[0]['total']
    
    # Préstamos activos
    prestamos_activos = pd.read_sql_query("SELECT COUNT(*) as total FROM prestamos WHERE estado = 'activo'", conn).iloc[0]['total']
    
    # Total hermanos activos
    total_hermanos = pd.read_sql_query("SELECT COUNT(*) as total FROM hermanos WHERE activo = 1", conn).iloc[0]['total']
    
    with col1:
        st.metric("🦽 Total Elementos", total_elementos)
    with col2:
        st.metric("✅ Disponibles", disponibles)
    with col3:
        st.metric("📋 Préstamos Activos", prestamos_activos)
    with col4:
        st.metric("👨‍🤝‍👨 Hermanos Activos", total_hermanos)
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🦽 Elementos por Categoría")
        elementos_categoria = pd.read_sql_query("""
            SELECT c.nombre, COUNT(e.id) as cantidad
            FROM categorias c
            LEFT JOIN elementos e ON c.id = e.categoria_id
            GROUP BY c.id, c.nombre
            ORDER BY cantidad DESC
        """, conn)
        
        if not elementos_categoria.empty:
            fig = px.pie(elementos_categoria, values='cantidad', names='nombre')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Estado de Elementos")
        estado_elementos = pd.read_sql_query("""
            SELECT estado, COUNT(*) as cantidad
            FROM elementos
            GROUP BY estado
        """, conn)
        
        if not estado_elementos.empty:
            fig = px.bar(estado_elementos, x='estado', y='cantidad', 
                        color='estado',
                        color_discrete_map={
                            'disponible': '#4CAF50',
                            'prestado': '#FF9800', 
                            'mantenimiento': '#F44336'
                        })
            st.plotly_chart(fig, use_container_width=True)
    
    # Préstamos por logia
    st.subheader("🏛️ Préstamos por Logia")
    prestamos_logia = pd.read_sql_query("""
        SELECT l.nombre as logia, COUNT(p.id) as cantidad_prestamos
        FROM prestamos p
        JOIN hermanos h ON p.hermano_solicitante_id = h.id
        JOIN logias l ON h.logia_id = l.id
        WHERE p.estado = 'activo'
        GROUP BY l.id, l.nombre
        ORDER BY cantidad_prestamos DESC
    """, conn)
    
    if not prestamos_logia.empty:
        fig = px.bar(prestamos_logia, x='logia', y='cantidad_prestamos', 
                    title="Préstamos Activos por Logia")
        fig.update_xaxis(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Alertas de vencimiento
    st.subheader("🚨 Alertas de Vencimiento")
    prestamos_vencer = pd.read_sql_query("""
        SELECT e.codigo, e.nombre as elemento, 
               b.nombre as beneficiario, b.telefono,
               h.nombre as hermano_solicitante,
               l.nombre as logia,
               p.fecha_devolucion_estimada,
               CASE 
                   WHEN DATE('now') > p.fecha_devolucion_estimada THEN 'VENCIDO'
                   WHEN DATE(p.fecha_devolucion_estimada, '-7 days') <= DATE('now') THEN 'POR VENCER'
               END as estado_alerta
        FROM prestamos p
        JOIN elementos e ON p.elemento_id = e.id
        JOIN beneficiarios b ON p.beneficiario_id = b.id
        JOIN hermanos h ON p.hermano_solicitante_id = h.id
        LEFT JOIN logias l ON h.logia_id = l.id
        WHERE p.estado = 'activo' 
        AND (DATE('now') > p.fecha_devolucion_estimada 
             OR DATE(p.fecha_devolucion_estimada, '-7 days') <= DATE('now'))
        ORDER BY p.fecha_devolucion_estimada ASC
    """, conn)
    
    if not prestamos_vencer.empty:
        st.dataframe(prestamos_vencer, use_container_width=True)
    else:
        st.success("✅ No hay préstamos próximos a vencer en los próximos 7 días")
    
    conn.close()

def main():
    """Función principal de la aplicación"""
    if not authenticate():
        return
    
    # Header principal
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.title("🏛️ BEO - Banco de Elementos Ortopédicos")
        st.caption("Sistema de Gestión Integral")
    
    # Sidebar para navegación
    st.sidebar.title("🏛️ BEO Sistema")
    st.sidebar.markdown("---")
    
    menu_options = {
        "Dashboard": "📊",
        "Gestión de Logias": "🏛️",
        "Gestión de Hermanos": "👨‍🤝‍👨",
        "Gestión de Elementos": "🦽",
        "Formulario de Préstamo": "📋",
        "Gestión de Depósitos": "🏢"
    }
    
    selected_option = st.sidebar.selectbox(
        "Seleccionar Sección",
        list(menu_options.keys()),
        format_func=lambda x: f"{menu_options[x]} {x}"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Banco de Elementos Ortopédicos")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.authenticated = False
        st.rerun()
    
    # Mostrar la sección seleccionada
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

if __name__ == "__main__":
    main()
