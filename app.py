with tab4:
        st.header("📚 Historial de Devoluciones")
        st.markdown("**Registro completo de todas las devoluciones realizadas**")
        
        conn = db.get_connection()
        
        # Obtener historial de devoluciones
        historial_devoluciones = pd.read_sql_query("""
            SELECT p.id, p.fecha_prestamo, p.fecha_devolucion_estimada, p.fecha_devolucion_real,
                   p.duracion_dias,
                   e.codigo, e.nombre as elemento,
                   c.nombre as categoria,
                   d.nombre as deposito_actual,
                   b.nombre as beneficiario, b.tipo,
                   h.nombre as hermano_solicitante,
                   l.nombre as logia,
                   p.entregado_por, p.recibido_por,
                   p.observaciones_prestamo, p.observaciones_devolucion,
                   CAST((JULIANDAY(p.fecha_devolucion_real) - JULIANDAY(p.fecha_devolucion_estimada)) AS INTEGER) as dias_diferencia
            FROM prestamos p
            JOIN elementos e ON p.elemento_id = e.id
            JOIN categorias c ON e.categoria_id = c.id
            JOIN depositos d ON e.deposito_id = d.id
            JOIN beneficiarios b ON p.beneficiario_id = b.id
            JOIN hermanos h ON p.hermano_solicitante_id = h.id
            LEFT JOIN logias l ON h.logia_id = l.id
            WHERE p.estado = 'devuelto'
            ORDER BY p.fecha_devolucion_real DESC
        """, conn)
        
        if not historial_devoluciones.empty:
            # Filtros para el historial
            col1, col2, col3 = st.columns(3)
            
            with col1:
                fecha_desde = st.date_input(
                    "Desde:",
                    value=date.today() - timedelta(days=90),
                    help="Filtrar devoluciones desde esta fecha"
                )
            
            with col2:
                fecha_hasta = st.date_input(
                    "Hasta:",
                    value=date.today(),
                    help="Filtrar devoluciones hasta esta fecha"
                )
            
            with col3:
                filtro_cumplimiento = st.selectbox(
                    "Cumplimiento:",
                    options=["Todos", "A Tiempo", "Con Retraso", "Anticipadas"],
                    help="Filtrar según cumplimiento de fechas"
                )
            
            # Aplicar filtros
            historial_filtrado = historial_devoluciones[
                (pd.to_datetime(historial_devoluciones['fecha_devolucion_real']) >= pd.to_datetime(fecha_desde)) &
                (pd.to_datetime(historial_devoluciones['fecha_devolucion_real']) <= pd.to_datetime(fecha_hasta))
            ]
            
            if filtro_cumplimiento != "Todos":
                if filtro_cumplimiento == "A Tiempo":
                    historial_filtrado = historial_filtrado[historial_filtrado['dias_diferencia'] == 0]
                elif filtro_cumplimiento == "Con Retraso":
                    historial_filtrado = historial_filtrado[historial_filtrado['dias_diferencia'] > 0]
                elif filtro_cumplimiento == "Anticipadas":
                    historial_filtrado = historial_filtrado[historial_filtrado['dias_diferencia'] < 0]
            
            if not historial_filtrado.empty:
                st.markdown(f"#### 📊 Mostrando {len(historial_filtrado)} de {len(historial_devoluciones)} devoluciones")
                
                # Estadísticas rápidas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Devoluciones", len(historial_filtrado))
                
                with col2:
                    a_tiempo = len(historial_filtrado[historial_filtrado['dias_diferencia'] == 0])
                    st.metric("A Tiempo", a_tiempo)
                
                with col3:
                    con_retraso = len(historial_filtrado[historial_filtrado['dias_diferencia'] > 0])
                    st.metric("Con Retraso", con_retraso)
                
                with col4:
                    anticipadas = len(historial_filtrado[historial_filtrado['dias_diferencia'] < 0])
                    st.metric("Anticipadas", anticipadas)
                
                st.markdown("---")
                
                # Mostrar cada devolución
                for idx, devolucion in historial_filtrado.iterrows():
                    # Determinar color según cumplimiento
                    if devolucion['dias_diferencia'] == 0:
                        cumplimiento_color = "#e8f5e8"  # Verde
                        cumplimiento_emoji = "✅"
                        cumplimiento_texto = "A tiempo"
                    elif devolucion['dias_diferencia'] > 0:
                        cumplimiento_color = "#ffebee"  # Rojo
                        cumplimiento_emoji = "⏰"
                        cumplimiento_texto = f"{devolucion['dias_diferencia']} días de retraso"
                    else:
                        cumplimiento_color = "#e3f2fd"  # Azul
                        cumplimiento_emoji = "⚡"
                        cumplimiento_texto = f"{abs(devolucion['dias_diferencia'])} días antes"
                    
                    with st.expander(f"{cumplimiento_emoji} {devolucion['codigo']} - {devolucion['elemento']} | Devuelto: {devolucion['fecha_devolucion_real']}"):
                        # Información en columnas
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown(f"""
                            **📦 ELEMENTO:**  
                            Código: {devolucion['codigo']}  
                            Nombre: {devolucion['elemento']}  
                            Categoría: {devolucion['categoria']}  
                            Depósito Actual: {devolucion['deposito_actual']}
                            """)
                        
                        with col2:
                            st.markdown(f"""
                            **👤 PRÉSTAMO:**  
                            Beneficiario: {devolucion['beneficiario']} ({devolucion['tipo']})  
                            Hermano: {devolucion['hermano_solicitante']}  
                            Logia: {devolucion['logia'] or 'No disponible'}  
                            Duración: {devolucion['duracion_dias']} días
                            """)
                        
                        with col3:
                            st.markdown(f"""
                            **📅 FECHAS:**  
                            Préstamo: {devolucion['fecha_prestamo']}  
                            Devolución Prevista: {devolucion['fecha_devolucion_estimada']}  
                            Devolución Real: {devolucion['fecha_devolucion_real']}  
                            Cumplimiento: {cumplimiento_texto}
                            """)
                        
                        # Responsables y observaciones
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"""
                            **👥 RESPONSABLES:**  
                            Entregado por: {devolucion['entregado_por']}  
                            Recibido por: {devolucion['recibido_por']}
                            """)
                        
                        with col2:
                            if devolucion['observaciones_prestamo'] or devolucion['observaciones_devolucion']:
                                st.markdown("**📝 OBSERVACIONES:**")
                                if devolucion['observaciones_prestamo']:
                                    st.text(f"Préstamo: {devolucion['observaciones_prestamo']}")
                                if devolucion['observaciones_devolucion']:
                                    st.text(f"Devolución: {devolucion['observaciones_devolucion']}")
            else:
                st.warning("❌ No se encontraron devoluciones en el rango de fechas seleccionado")
        
        else:
            st.info("ℹ️ **No hay devoluciones registradas aún**")
            st.markdown("Las devoluciones aparecerán aquí una vez que se registren en la pestaña **'DEVOLVER ELEMENTOS'**")
        
        conn.close()import streamlit as st
import pandas as pd
import sqlite3
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
    
    tab1, tab2, tab3 = st.tabs(["Nuevo Elemento", "Inventario", "🔧 Cambiar Estado de Elementos"])
    
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
    
    with tab3:
        st.header("🔧 Cambiar Estado de Elementos")
        st.markdown("**Gestión manual de estados para casos especiales, correcciones o mantenimiento**")
        
        conn = db.get_connection()
        
        # Obtener todos los elementos con información detallada
        elementos_completos = pd.read_sql_query("""
            SELECT e.id, e.codigo, e.nombre, c.nombre as categoria, d.nombre as deposito, 
                   e.estado, e.marca, e.modelo, e.fecha_ingreso, e.observaciones,
                   p.id as prestamo_id, p.fecha_prestamo, p.fecha_devolucion_estimada,
                   b.nombre as beneficiario_actual,
                   h.nombre as hermano_solicitante
            FROM elementos e
            JOIN categorias c ON e.categoria_id = c.id
            JOIN depositos d ON e.deposito_id = d.id
            LEFT JOIN prestamos p ON e.id = p.elemento_id AND p.estado = 'activo'
            LEFT JOIN beneficiarios b ON p.beneficiario_id = b.id
            LEFT JOIN hermanos h ON p.hermano_solicitante_id = h.id
            ORDER BY e.codigo
        """, conn)
        
        if not elementos_completos.empty:
            # Filtros
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filtro_estado_actual = st.selectbox(
                    "Filtrar por Estado Actual:",
                    options=["Todos", "disponible", "prestado", "mantenimiento"],
                    help="Filtrar elementos según su estado actual"
                )
            
            with col2:
                busqueda_codigo = st.text_input(
                    "Buscar por Código:",
                    placeholder="Ej: SR-001",
                    help="Buscar elemento por su código"
                )
            
            with col3:
                busqueda_nombre = st.text_input(
                    "Buscar por Nombre:",
                    placeholder="Ej: Silla de ruedas",
                    help="Buscar elemento por su nombre"
                )
            
            # Aplicar filtros
            elementos_filtrados = elementos_completos.copy()
            
            if filtro_estado_actual != "Todos":
                elementos_filtrados = elementos_filtrados[elementos_filtrados['estado'] == filtro_estado_actual]
            
            if busqueda_codigo:
                elementos_filtrados = elementos_filtrados[
                    elementos_filtrados['codigo'].str.contains(busqueda_codigo, case=False, na=False)
                ]
            
            if busqueda_nombre:
                elementos_filtrados = elementos_filtrados[
                    elementos_filtrados['nombre'].str.contains(busqueda_nombre, case=False, na=False)
                ]
            
            if not elementos_filtrados.empty:
                st.markdown(f"#### 🔍 Mostrando {len(elementos_filtrados)} de {len(elementos_completos)} elementos")
                
                # Mostrar cada elemento con opción de cambio de estado
                for idx, elemento in elementos_filtrados.iterrows():
                    # Determinar color según estado actual
                    if elemento['estado'] == 'disponible':
                        estado_color = "#e8f5e8"  # Verde
                        estado_emoji = "✅"
                    elif elemento['estado'] == 'prestado':
                        estado_color = "#fff3e0"  # Naranja
                        estado_emoji = "📋"
                    elif elemento['estado'] == 'mantenimiento':
                        estado_color = "#ffebee"  # Rojo
                        estado_emoji = "🔧"
                    else:
                        estado_color = "#f5f5f5"  # Gris
                        estado_emoji = "❓"
                    
                    # Tarjeta del elemento
                    with st.container():
                        st.markdown(f"""
                        <div style="background-color: {estado_color}; padding: 15px; border-radius: 10px; margin: 10px 0;">
                        <h4>{estado_emoji} {elemento['codigo']} - {elemento['nombre']}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Información del elemento
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown(f"""
                            **📦 ELEMENTO:**  
                            Código: {elemento['codigo']}  
                            Nombre: {elemento['nombre']}  
                            Categoría: {elemento['categoria']}  
                            Estado Actual: **{elemento['estado'].upper()}**
                            """)
                        
                        with col2:
                            st.markdown(f"""
                            **📍 UBICACIÓN:**  
                            Depósito: {elemento['deposito']}  
                            Marca: {elemento['marca'] or 'N/A'}  
                            Modelo: {elemento['modelo'] or 'N/A'}  
                            Ingreso: {elemento['fecha_ingreso']}
                            """)
                        
                        with col3:
                            if elemento['estado'] == 'prestado' and elemento['prestamo_id']:
                                st.markdown(f"""
                                **📋 PRÉSTAMO ACTIVO:**  
                                Beneficiario: {elemento['beneficiario_actual']}  
                                Hermano: {elemento['hermano_solicitante']}  
                                Desde: {elemento['fecha_prestamo']}  
                                Hasta: {elemento['fecha_devolucion_estimada']}
                                """)
                            else:
                                st.markdown(f"""
                                **📝 INFORMACIÓN:**  
                                Sin préstamo activo  
                                Disponible para cambios  
                                """)
                                if elemento['observaciones']:
                                    st.text(f"Obs: {elemento['observaciones'][:50]}...")
                        
                        with col4:
                            # Botón para cambiar estado
                            if st.button(
                                f"🔄 Cambiar Estado", 
                                key=f"cambiar_estado_{elemento['id']}", 
                                help=f"Cambiar estado del elemento {elemento['codigo']}"
                            ):
                                st.session_state[f'mostrar_cambio_estado_{elemento["id"]}'] = True
                        
                        # Formulario para cambiar estado
                        if st.session_state.get(f'mostrar_cambio_estado_{elemento["id"]}', False):
                            st.markdown("---")
                            st.markdown(f"### 🔄 Cambiar Estado: {elemento['codigo']} - {elemento['nombre']}")
                            
                            # Advertencia si está prestado
                            if elemento['estado'] == 'prestado' and elemento['prestamo_id']:
                                st.warning(f"""
                                ⚠️ **ATENCIÓN:** Este elemento está actualmente prestado a {elemento['beneficiario_actual']}.
                                
                                **Antes de cambiar el estado, considera:**
                                - ¿El elemento fue devuelto pero no se registró la devolución?
                                - ¿Necesitas registrar la devolución oficial primero?
                                - ¿Es realmente necesario cambiar el estado manualmente?
                                
                                **Recomendación:** Usa la pestaña "🔄 DEVOLVER ELEMENTOS" para devoluciones normales.
                                """)
                            
                            with st.form(f"form_cambio_estado_{elemento['id']}"):
                                col_form1, col_form2 = st.columns(2)
                                
                                with col_form1:
                                    st.markdown("#### 📊 Nuevo Estado")
                                    
                                    # Estados disponibles
                                    estados_disponibles = ["disponible", "prestado", "mantenimiento"]
                                    estado_actual_idx = estados_disponibles.index(elemento['estado']) if elemento['estado'] in estados_disponibles else 0
                                    
                                    nuevo_estado = st.selectbox(
                                        "Seleccionar Nuevo Estado:",
                                        options=estados_disponibles,
                                        index=estado_actual_idx,
                                        format_func=lambda x: {
                                            'disponible': '✅ Disponible',
                                            'prestado': '📋 Prestado', 
                                            'mantenimiento': '🔧 En Mantenimiento'
                                        }[x],
                                        help="Selecciona el nuevo estado del elemento"
                                    )
                                    
                                    # Explicación del estado seleccionado
                                    if nuevo_estado == 'disponible':
                                        st.info("✅ **Disponible:** El elemento puede ser prestado")
                                    elif nuevo_estado == 'prestado':
                                        st.warning("📋 **Prestado:** Marca el elemento como prestado (sin crear préstamo formal)")
                                    elif nuevo_estado == 'mantenimiento':
                                        st.error("🔧 **Mantenimiento:** El elemento necesita reparación o revisión")
                                
                                with col_form2:
                                    st.markdown("#### 📝 Información del Cambio")
                                    
                                    razon_cambio = st.selectbox(
                                        "Razón del Cambio:",
                                        options=[
                                            "Corrección administrativa",
                                            "Devolución no registrada",
                                            "Elemento perdido/dañado",
                                            "Mantenimiento preventivo",
                                            "Error en registro anterior",
                                            "Otro"
                                        ],
                                        help="Selecciona la razón principal del cambio"
                                    )
                                    
                                    if razon_cambio == "Otro":
                                        razon_cambio = st.text_input("Especificar razón:")
                                    
                                    observaciones_cambio = st.text_area(
                                        "Observaciones del Cambio:",
                                        placeholder="Describe el motivo detallado del cambio de estado...",
                                        help="Información adicional sobre por qué se cambia el estado"
                                    )
                                    
                                    responsable_cambio = st.text_input(
                                        "Responsable del Cambio:*",
                                        placeholder="Nombre de quien autoriza el cambio",
                                        help="Persona responsable que autoriza este cambio"
                                    )
                                
                                # Mostrar cambio propuesto
                                st.markdown("#### 📋 Resumen del Cambio")
                                col_resumen1, col_resumen2, col_resumen3 = st.columns(3)
                                with col_resumen1:
                                    st.markdown(f"**Estado Actual:** {elemento['estado'].upper()}")
                                with col_resumen2:
                                    st.markdown(f"**Nuevo Estado:** {nuevo_estado.upper()}")
                                with col_resumen3:
                                    st.markdown(f"**Razón:** {razon_cambio}")
                                
                                # Botones de acción
                                col_btn1, col_btn2, col_btn3 = st.columns(3)
                                
                                with col_btn1:
                                    submitted = st.form_submit_button(
                                        "✅ CONFIRMAR CAMBIO",
                                        type="primary",
                                        use_container_width=True
                                    )
                                
                                with col_btn2:
                                    if st.form_submit_button(
                                        "❌ Cancelar",
                                        use_container_width=True
                                    ):
                                        del st.session_state[f'mostrar_cambio_estado_{elemento["id"]}']
                                        st.rerun()
                                
                                with col_btn3:
                                    # Acción especial si está prestado
                                    if elemento['estado'] == 'prestado' and elemento['prestamo_id']:
                                        if st.form_submit_button(
                                            "📋 Ver Préstamo",
                                            use_container_width=True,
                                            help="Ir a la gestión de préstamos para ver detalles"
                                        ):
                                            st.info("💡 Para gestionar este préstamo, ve a 'Formulario de Préstamo' → 'Préstamos Activos'")
                                
                                # Procesar el cambio
                                if submitted:
                                    if responsable_cambio:
                                        try:
                                            cursor = conn.cursor()
                                            
                                            # Validaciones especiales
                                            cambio_valido = True
                                            mensaje_error = ""
                                            
                                            # Si cambia a 'prestado' manualmente, verificar que no haya préstamo activo
                                            if nuevo_estado == 'prestado' and elemento['estado'] != 'prestado':
                                                if elemento['prestamo_id']:
                                                    cambio_valido = False
                                                    mensaje_error = "No se puede marcar como prestado: ya tiene un préstamo activo registrado"
                                            
                                            # Si cambia desde 'prestado', considerar cerrar préstamo
                                            if elemento['estado'] == 'prestado' and nuevo_estado != 'prestado' and elemento['prestamo_id']:
                                                st.warning("⚠️ **ATENCIÓN:** Cambiar el estado cerrará automáticamente el préstamo activo. ¿Estás seguro?")
                                                # Aquí podrías agregar confirmación adicional
                                            
                                            if cambio_valido:
                                                # Actualizar estado del elemento
                                                cursor.execute("""
                                                    UPDATE elementos 
                                                    SET estado = ?,
                                                        observaciones = COALESCE(observaciones, '') || 
                                                        CASE WHEN observaciones IS NULL OR observaciones = '' 
                                                             THEN ? 
                                                             ELSE '\n' || ? 
                                                        END
                                                    WHERE id = ?
                                                """, (
                                                    nuevo_estado,
                                                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Estado cambiado de '{elemento['estado']}' a '{nuevo_estado}' por {responsable_cambio}. Razón: {razon_cambio}. {observaciones_cambio}",
                                                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Estado cambiado de '{elemento['estado']}' a '{nuevo_estado}' por {responsable_cambio}. Razón: {razon_cambio}. {observaciones_cambio}",
                                                    elemento['id']
                                                ))
                                                
                                                # Si había préstamo activo y se cambia el estado, cerrar préstamo
                                                if elemento['estado'] == 'prestado' and nuevo_estado != 'prestado' and elemento['prestamo_id']:
                                                    cursor.execute("""
                                                        UPDATE prestamos 
                                                        SET estado = 'devuelto', 
                                                            fecha_devolucion_real = DATE('now'),
                                                            observaciones_devolucion = ?,
                                                            recibido_por = ?
                                                        WHERE id = ?
                                                    """, (
                                                        f"Préstamo cerrado automáticamente por cambio de estado manual. {observaciones_cambio}",
                                                        responsable_cambio,
                                                        elemento['prestamo_id']
                                                    ))
                                                
                                                conn.commit()
                                                
                                                # Mensaje de éxito
                                                st.success(f"""
                                                ✅ **Estado Cambiado Exitosamente**
                                                
                                                📦 **Elemento:** {elemento['codigo']} - {elemento['nombre']}  
                                                📊 **Estado:** {elemento['estado']} → **{nuevo_estado}**  
                                                👤 **Responsable:** {responsable_cambio}  
                                                📅 **Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  
                                                📝 **Razón:** {razon_cambio}
                                                """)
                                                
                                                # Limpiar estado y recargar
                                                del st.session_state[f'mostrar_cambio_estado_{elemento["id"]}']
                                                time.sleep(2)
                                                st.rerun()
                                            else:
                                                st.error(f"❌ {mensaje_error}")
                                                
                                        except Exception as e:
                                            st.error(f"❌ Error al cambiar estado: {e}")
                                    else:
                                        st.error("❌ El campo 'Responsable del Cambio' es obligatorio")
                        
                        st.markdown("---")
            else:
                st.warning("❌ No se encontraron elementos que coincidan con los filtros aplicados.")
        
        else:
            st.info("ℹ️ **No hay elementos registrados en el sistema**")
            st.markdown("Para agregar elementos, ve a la pestaña **'Nuevo Elemento'**")
        
        conn.close()

def gestionar_prestamos():
    """Gestión de préstamos según formulario BEO"""
    st.header("📋 Formulario de Préstamo BEO")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Nuevo Préstamo", "Préstamos Activos", "🔄 DEVOLVER ELEMENTOS", "Historial de Devoluciones"])
    
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
                    if duracion_tipo == "Días":
                        duracion_cantidad = st.number_input("Cantidad", min_value=1, value=90, key="duracion_dias")
                    else:
                        duracion_cantidad = st.number_input("Cantidad", min_value=1, value=3, key="duracion_meses")
                
                # Cálculo de días
                if duracion_tipo == "Meses":
                    duracion_dias = duracion_cantidad * 30  # Aproximación
                else:
                    duracion_dias = duracion_cantidad
                
                # Mostrar cálculo en tiempo real
                st.info(f"📅 **Duración del préstamo:** {duracion_dias} días ({duracion_cantidad} {duracion_tipo.lower()})")
                
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
                
                # Fecha estimada de devolución - CORREGIDA
                from datetime import timedelta
                fecha_devolucion_estimada = fecha_prestamo + timedelta(days=duracion_dias)
                st.markdown("#### 📅 Fecha Estimada de Devolución")
                st.date_input(
                    "Devolución prevista", 
                    value=fecha_devolucion_estimada, 
                    disabled=True,
                    help=f"Calculada automáticamente: {fecha_prestamo.strftime('%d/%m/%Y')} + {duracion_dias} días = {fecha_devolucion_estimada.strftime('%d/%m/%Y')}"
                )
                
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
        st.subheader("📋 Préstamos Activos - Vista de Monitoreo")
        st.info("💡 **Para devolver elementos, utiliza la pestaña '🔄 DEVOLVER ELEMENTOS' que está diseñada específicamente para esa función.**")
        
        conn = db.get_connection()
        prestamos_activos = pd.read_sql_query("""
            SELECT p.id, e.codigo, e.nombre as elemento, 
                   b.nombre as beneficiario, b.tipo, b.telefono,
                   h.nombre as hermano_solicitante,
                   l.nombre as logia,
                   p.fecha_prestamo, p.fecha_devolucion_estimada, p.entregado_por,
                   CASE 
                       WHEN DATE('now') > p.fecha_devolucion_estimada THEN 'VENCIDO'
                       WHEN DATE(p.fecha_devolucion_estimada, '-7 days') <= DATE('now') THEN 'POR VENCER'
                       ELSE 'VIGENTE'
                   END as estado_vencimiento,
                   CAST((JULIANDAY(p.fecha_devolucion_estimada) - JULIANDAY('now')) AS INTEGER) as dias_restantes
            FROM prestamos p
            JOIN elementos e ON p.elemento_id = e.id
            JOIN beneficiarios b ON p.beneficiario_id = b.id
            JOIN hermanos h ON p.hermano_solicitante_id = h.id
            LEFT JOIN logias l ON h.logia_id = l.id
            WHERE p.estado = 'activo'
            ORDER BY p.fecha_devolucion_estimada ASC
        """, conn)
        
        if not prestamos_activos.empty:
            st.markdown("#### 🔍 Vista Resumen de Préstamos Activos")
            
            # Aplicar colores según estado de vencimiento
            def highlight_vencimiento(row):
                if row['estado_vencimiento'] == 'VENCIDO':
                    return ['background-color: #ffebee'] * len(row)
                elif row['estado_vencimiento'] == 'POR VENCER':
                    return ['background-color: #fff3e0'] * len(row)
                else:
                    return ['background-color: #e8f5e8'] * len(row)
            
            # Mostrar solo las columnas más importantes para el monitoreo
            df_display = prestamos_activos[['codigo', 'elemento', 'beneficiario', 'hermano_solicitante', 
                                          'logia', 'fecha_prestamo', 'fecha_devolucion_estimada', 
                                          'estado_vencimiento', 'dias_restantes']].copy()
            
            styled_df = df_display.style.apply(highlight_vencimiento, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            
            # Resumen de estados
            st.markdown("#### 📊 Resumen de Estados")
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
            
            # Enlace a devoluciones
            st.markdown("---")
            st.markdown("### 🔄 ¿Necesitas registrar una devolución?")
            st.markdown("**Dirígete a la pestaña '🔄 DEVOLVER ELEMENTOS' para un proceso completo y fácil de usar.**")
                
        else:
            st.info("ℹ️ No hay préstamos activos en este momento")
            st.markdown("Para registrar un nuevo préstamo, ir a la pestaña **'Nuevo Préstamo'**")
        
        conn.close()
    
    with tab3:
        st.header("🔄 DEVOLVER ELEMENTOS")
        st.markdown("**En esta sección puedes devolver cualquier elemento prestado, sin importar si está vencido o no.**")
        
        conn = db.get_connection()
        
        # Obtener préstamos activos con más información
        prestamos_activos = pd.read_sql_query("""
            SELECT p.id, p.fecha_prestamo, p.fecha_devolucion_estimada, p.duracion_dias,
                   e.id as elemento_id, e.codigo, e.nombre as elemento, e.descripcion,
                   c.nombre as categoria,
                   d_origen.nombre as deposito_origen,
                   b.nombre as beneficiario, b.tipo, b.telefono, b.direccion,
                   hr.nombre as hermano_responsable,
                   hs.nombre as hermano_solicitante,
                   l.nombre as logia,
                   p.entregado_por, p.observaciones_prestamo,
                   CASE 
                       WHEN DATE('now') > p.fecha_devolucion_estimada THEN 'VENCIDO'
                       WHEN DATE(p.fecha_devolucion_estimada, '-7 days') <= DATE('now') THEN 'POR VENCER'
                       ELSE 'VIGENTE'
                   END as estado_vencimiento,
                   CAST((JULIANDAY(p.fecha_devolucion_estimada) - JULIANDAY('now')) AS INTEGER) as dias_restantes
            FROM prestamos p
            JOIN elementos e ON p.elemento_id = e.id
            JOIN categorias c ON e.categoria_id = c.id
            JOIN depositos d_origen ON e.deposito_id = d_origen.id
            JOIN beneficiarios b ON p.beneficiario_id = b.id
            LEFT JOIN hermanos hr ON b.hermano_responsable_id = hr.id
            JOIN hermanos hs ON p.hermano_solicitante_id = hs.id
            LEFT JOIN logias l ON hs.logia_id = l.id
            WHERE p.estado = 'activo'
            ORDER BY p.fecha_devolucion_estimada ASC
        """, conn)
        
        if not prestamos_activos.empty:
            st.markdown("### 📋 Elementos Actualmente Prestados")
            st.info("💡 **Tip:** Puedes devolver cualquier elemento en cualquier momento, no es necesario esperar la fecha de vencimiento.")
            
            # Filtros y búsqueda
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_estado = st.selectbox(
                    "Filtrar por Estado:",
                    options=["Todos", "VIGENTE", "POR VENCER", "VENCIDO"],
                    help="Filtra los préstamos según su estado de vencimiento"
                )
            with col2:
                busqueda_elemento = st.text_input(
                    "Buscar Elemento:",
                    placeholder="Código o nombre del elemento",
                    help="Busca por código (ej: SR-001) o nombre del elemento"
                )
            with col3:
                busqueda_beneficiario = st.text_input(
                    "Buscar Beneficiario:",
                    placeholder="Nombre del beneficiario",
                    help="Busca por nombre del beneficiario"
                )
            
            # Aplicar filtros
            prestamos_filtrados = prestamos_activos.copy()
            
            if filtro_estado != "Todos":
                prestamos_filtrados = prestamos_filtrados[prestamos_filtrados['estado_vencimiento'] == filtro_estado]
            
            if busqueda_elemento:
                prestamos_filtrados = prestamos_filtrados[
                    prestamos_filtrados['codigo'].str.contains(busqueda_elemento, case=False, na=False) |
                    prestamos_filtrados['elemento'].str.contains(busqueda_elemento, case=False, na=False)
                ]
            
            if busqueda_beneficiario:
                prestamos_filtrados = prestamos_filtrados[
                    prestamos_filtrados['beneficiario'].str.contains(busqueda_beneficiario, case=False, na=False)
                ]
            
            if not prestamos_filtrados.empty:
                st.markdown(f"#### 🔍 Mostrando {len(prestamos_filtrados)} de {len(prestamos_activos)} préstamos")
                
                # Mostrar cada préstamo como una tarjeta
                for idx, prestamo in prestamos_filtrados.iterrows():
                    # Determinar color y estilo del estado
                    if prestamo['estado_vencimiento'] == 'VENCIDO':
                        estado_emoji = "🔴"
                        estado_color = "#ffebee"
                        estado_texto = f"VENCIDO hace {abs(prestamo['dias_restantes'])} días"
                    elif prestamo['estado_vencimiento'] == 'POR VENCER':
                        estado_emoji = "🟡"
                        estado_color = "#fff3e0"
                        estado_texto = f"Vence en {prestamo['dias_restantes']} días"
                    else:
                        estado_emoji = "🟢"
                        estado_color = "#e8f5e8"
                        estado_texto = f"Vigente - {prestamo['dias_restantes']} días restantes"
                    
                    # Tarjeta del préstamo
                    with st.container():
                        st.markdown(f"""
                        <div style="background-color: {estado_color}; padding: 15px; border-radius: 10px; margin: 10px 0;">
                        <h4>{estado_emoji} {prestamo['codigo']} - {prestamo['elemento']}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Información del préstamo en columnas
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown(f"""
                            **📦 ELEMENTO:**  
                            Código: {prestamo['codigo']}  
                            Nombre: {prestamo['elemento']}  
                            Categoría: {prestamo['categoria']}  
                            Depósito Origen: {prestamo['deposito_origen']}
                            """)
                        
                        with col2:
                            st.markdown(f"""
                            **👤 BENEFICIARIO:**  
                            Nombre: {prestamo['beneficiario']}  
                            Tipo: {prestamo['tipo']}  
                            Teléfono: {prestamo['telefono'] or 'No disponible'}  
                            """)
                        
                        with col3:
                            st.markdown(f"""
                            **🏛️ HERMANO/LOGIA:**  
                            Solicitante: {prestamo['hermano_solicitante']}  
                            Logia: {prestamo['logia'] or 'No disponible'}  
                            Entregado por: {prestamo['entregado_por']}
                            """)
                        
                        with col4:
                            st.markdown(f"""
                            **📅 FECHAS:**  
                            Préstamo: {prestamo['fecha_prestamo']}  
                            Devolución: {prestamo['fecha_devolucion_estimada']}  
                            Estado: {estado_texto}
                            """)
                        
                        # Botón de devolución prominente
                        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
                        with col_btn2:
                            if st.button(
                                f"🔄 DEVOLVER AHORA", 
                                key=f"devolver_main_{prestamo['id']}", 
                                type="primary",
                                use_container_width=True,
                                help="Registrar la devolución de este elemento"
                            ):
                                st.session_state[f'mostrar_devolucion_{prestamo["id"]}'] = True
                        
                        # Formulario de devolución expandible
                        if st.session_state.get(f'mostrar_devolucion_{prestamo["id"]}', False):
                            st.markdown("---")
                            st.markdown("### 📝 Registrar Devolución")
                            
                            with st.form(f"form_devolucion_{prestamo['id']}"):
                                # Obtener lista de depósitos para selección
                                depositos_disponibles = pd.read_sql_query("SELECT id, nombre, direccion FROM depositos ORDER BY nombre", conn)
                                
                                col_form1, col_form2 = st.columns(2)
                                
                                with col_form1:
                                    st.markdown("#### 📅 Información de Devolución")
                                    fecha_devolucion = st.date_input(
                                        "Fecha de Devolución*", 
                                        value=date.today(),
                                        help="Fecha en que se recibe el elemento"
                                    )
                                    
                                    recibido_por = st.text_input(
                                        "Recibido por*", 
                                        placeholder="Nombre de quien recibe el elemento",
                                        help="Persona responsable que recibe la devolución"
                                    )
                                    
                                    # SELECCIÓN DE DEPÓSITO - NUEVA FUNCIONALIDAD
                                    if not depositos_disponibles.empty:
                                        deposito_devolucion_id = st.selectbox(
                                            "Depósito de Devolución*",
                                            options=depositos_disponibles['id'].tolist(),
                                            format_func=lambda x: f"{depositos_disponibles[depositos_disponibles['id'] == x]['nombre'].iloc[0]}",
                                            index=depositos_disponibles[depositos_disponibles['id'] == prestamo['elemento_id']].index[0] if len(depositos_disponibles[depositos_disponibles['id'] == prestamo['elemento_id']]) > 0 else 0,
                                            help="Selecciona a qué depósito se devuelve el elemento"
                                        )
                                        
                                        # Mostrar información del depósito seleccionado
                                        deposito_info = depositos_disponibles[depositos_disponibles['id'] == deposito_devolucion_id].iloc[0]
                                        st.info(f"📍 **Depósito:** {deposito_info['nombre']}\n📧 **Dirección:** {deposito_info['direccion'] or 'No especificada'}")
                                    else:
                                        st.error("⚠️ No hay depósitos disponibles")
                                        deposito_devolucion_id = None
                                
                                with col_form2:
                                    st.markdown("#### 📝 Estado y Observaciones")
                                    
                                    # Estado del elemento al devolverse
                                    estado_devolucion = st.selectbox(
                                        "Estado del Elemento",
                                        options=["Bueno", "Regular", "Necesita Mantenimiento", "Dañado"],
                                        help="Estado en que se encuentra el elemento al ser devuelto"
                                    )
                                    
                                    observaciones_devolucion = st.text_area(
                                        "Observaciones de Devolución",
                                        placeholder="Describe el estado del elemento, reparaciones necesarias, etc.",
                                        help="Cualquier observación sobre el estado del elemento o la devolución"
                                    )
                                    
                                    # Mostrar información del préstamo original
                                    st.markdown("#### 📋 Información del Préstamo Original")
                                    st.text(f"Prestado el: {prestamo['fecha_prestamo']}")
                                    st.text(f"Duración: {prestamo['duracion_dias']} días")
                                    st.text(f"Devuelve: {prestamo['beneficiario']}")
                                    if prestamo['observaciones_prestamo']:
                                        st.text(f"Obs. Préstamo: {prestamo['observaciones_prestamo']}")
                                
                                # Botones de acción
                                col_action1, col_action2, col_action3 = st.columns(3)
                                
                                with col_action1:
                                    submitted = st.form_submit_button(
                                        "✅ CONFIRMAR DEVOLUCIÓN", 
                                        type="primary",
                                        use_container_width=True
                                    )
                                
                                with col_action2:
                                    if st.form_submit_button(
                                        "❌ Cancelar", 
                                        use_container_width=True
                                    ):
                                        del st.session_state[f'mostrar_devolucion_{prestamo["id"]}']
                                        st.rerun()
                                
                                with col_action3:
                                    # Botón para marcar como mantenimiento si es necesario
                                    if estado_devolucion in ["Necesita Mantenimiento", "Dañado"]:
                                        mantenimiento = st.form_submit_button(
                                            "🔧 Devolver a Mantenimiento",
                                            use_container_width=True,
                                            help="El elemento se marcará como 'en mantenimiento' en lugar de 'disponible'"
                                        )
                                    else:
                                        mantenimiento = False
                                
                                # Procesar la devolución
                                if submitted or mantenimiento:
                                    if recibido_por and deposito_devolucion_id:
                                        try:
                                            cursor = conn.cursor()
                                            
                                            # Determinar estado final del elemento
                                            if mantenimiento or estado_devolucion in ["Necesita Mantenimiento", "Dañado"]:
                                                estado_final = "mantenimiento"
                                                mensaje_estado = "marcado para mantenimiento"
                                            else:
                                                estado_final = "disponible"
                                                mensaje_estado = "disponible para préstamo"
                                            
                                            # Actualizar préstamo
                                            observaciones_completas = f"Estado al devolver: {estado_devolucion}. {observaciones_devolucion}".strip()
                                            cursor.execute("""
                                                UPDATE prestamos 
                                                SET fecha_devolucion_real = ?, estado = 'devuelto',
                                                    observaciones_devolucion = ?, recibido_por = ?
                                                WHERE id = ?
                                            """, (fecha_devolucion, observaciones_completas, recibido_por, prestamo['id']))
                                            
                                            # Actualizar elemento (estado y depósito)
                                            cursor.execute("""
                                                UPDATE elementos 
                                                SET estado = ?, deposito_id = ?
                                                WHERE id = ?
                                            """, (estado_final, deposito_devolucion_id, prestamo['elemento_id']))
                                            
                                            conn.commit()
                                            
                                            # Mensaje de éxito
                                            st.success(f"""
                                            ✅ **Devolución Registrada Exitosamente**
                                            
                                            📦 **Elemento:** {prestamo['codigo']} - {prestamo['elemento']}  
                                            📍 **Depósito:** {deposito_info['nombre']}  
                                            📊 **Estado:** {mensaje_estado}  
                                            👤 **Recibido por:** {recibido_por}  
                                            📅 **Fecha:** {fecha_devolucion}
                                            """)
                                            
                                            # Limpiar estado y recargar
                                            del st.session_state[f'mostrar_devolucion_{prestamo["id"]}']
                                            st.balloons()
                                            
                                            # Pequeña pausa para mostrar el mensaje
                                            time.sleep(2)
                                            st.rerun()
                                            
                                        except Exception as e:
                                            st.error(f"❌ Error al registrar devolución: {e}")
                                    else:
                                        st.error("❌ Todos los campos marcados con * son obligatorios")
                        
                        st.markdown("---")
            else:
                st.warning("❌ No se encontraron préstamos que coincidan con los filtros aplicados.")
                st.markdown("**Sugerencias:**")
                st.markdown("- Verifica los filtros de búsqueda")
                st.markdown("- Cambia el filtro de estado a 'Todos'")
                st.markdown("- Revisa la ortografía en las búsquedas")
        
        else:
            st.info("ℹ️ **No hay elementos prestados actualmente**")
            st.markdown("Para registrar un nuevo préstamo, ve a la pestaña **'Nuevo Préstamo'**")
        
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
