import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import hashlib
import logging
from contextlib import contextmanager

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la página
st.set_page_config(
    page_title="BEO - Sistema de Inventario Completo",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

class BEODatabase:
    def __init__(self, db_name="beo_sistema.db"):
        self.db_name = db_name
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager para manejo seguro de conexiones"""
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON")  # Habilitar foreign keys
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Error en transacción: {e}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Inicializar base de datos con estructura completa"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de logias
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    venerable_maestro TEXT,
                    hospitalario TEXT,
                    telefono TEXT,
                    email TEXT,
                    direccion TEXT,
                    activa BOOLEAN DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de hermanos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hermanos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_completo TEXT NOT NULL,
                    documento TEXT UNIQUE,
                    logia_id INTEGER,
                    grado TEXT,
                    telefono TEXT,
                    email TEXT,
                    direccion TEXT,
                    activo BOOLEAN DEFAULT 1,
                    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (logia_id) REFERENCES logias (id)
                )
            """)
            
            # Tabla de depósitos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS depositos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    ubicacion TEXT,
                    responsable TEXT,
                    telefono TEXT,
                    activo BOOLEAN DEFAULT 1,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de elementos - CORREGIDA con constraints
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS elementos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT NOT NULL UNIQUE,
                    nombre TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    marca TEXT,
                    modelo TEXT,
                    descripcion TEXT,
                    deposito_id INTEGER,
                    estado TEXT NOT NULL DEFAULT 'disponible' 
                        CHECK (estado IN ('disponible', 'prestado', 'mantenimiento', 'dado_baja')),
                    precio_compra REAL,
                    fecha_compra DATE,
                    observaciones TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (deposito_id) REFERENCES depositos (id)
                )
            """)
            
            # Tabla de préstamos - CORREGIDA con constraints
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prestamos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    elemento_id INTEGER NOT NULL,
                    hermano_id INTEGER NOT NULL,
                    beneficiario_tipo TEXT DEFAULT 'hermano' CHECK (beneficiario_tipo IN ('hermano', 'familiar')),
                    beneficiario_nombre TEXT,
                    beneficiario_parentesco TEXT,
                    beneficiario_documento TEXT,
                    direccion_entrega TEXT,
                    duracion_dias INTEGER DEFAULT 30,
                    fecha_prestamo DATE NOT NULL DEFAULT (date('now')),
                    fecha_vencimiento DATE NOT NULL,
                    fecha_devolucion DATE,
                    estado TEXT NOT NULL DEFAULT 'activo' 
                        CHECK (estado IN ('activo', 'devuelto', 'vencido', 'perdido')),
                    observaciones_prestamo TEXT,
                    observaciones_devolucion TEXT,
                    responsable_entrega TEXT,
                    responsable_recepcion TEXT,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (elemento_id) REFERENCES elementos (id),
                    FOREIGN KEY (hermano_id) REFERENCES hermanos (id)
                )
            """)
            
            # Tabla de historial de estados (para auditoría)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historial_estados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    elemento_id INTEGER NOT NULL,
                    estado_anterior TEXT,
                    estado_nuevo TEXT NOT NULL,
                    motivo TEXT,
                    usuario TEXT,
                    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (elemento_id) REFERENCES elementos (id)
                )
            """)
            
            # Triggers para mantener integridad - CLAVE PARA SOLUCIONAR EL PROBLEMA
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS actualizar_elemento_prestado
                AFTER INSERT ON prestamos
                WHEN NEW.estado = 'activo'
                BEGIN
                    UPDATE elementos 
                    SET estado = 'prestado', fecha_actualizacion = CURRENT_TIMESTAMP
                    WHERE id = NEW.elemento_id;
                    
                    INSERT INTO historial_estados (elemento_id, estado_anterior, estado_nuevo, motivo)
                    SELECT NEW.elemento_id, 'disponible', 'prestado', 'Préstamo ID: ' || NEW.id;
                END;
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS actualizar_elemento_devuelto
                AFTER UPDATE ON prestamos
                WHEN NEW.estado = 'devuelto' AND OLD.estado = 'activo'
                BEGIN
                    UPDATE elementos 
                    SET estado = 'disponible', fecha_actualizacion = CURRENT_TIMESTAMP
                    WHERE id = NEW.elemento_id;
                    
                    INSERT INTO historial_estados (elemento_id, estado_anterior, estado_nuevo, motivo)
                    VALUES (NEW.elemento_id, 'prestado', 'disponible', 'Devolución de préstamo ID: ' || NEW.id);
                END;
            """)
            
            # Trigger para prevenir préstamos múltiples del mismo elemento
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS prevenir_prestamo_duplicado
                BEFORE INSERT ON prestamos
                WHEN NEW.estado = 'activo'
                BEGIN
                    SELECT CASE
                        WHEN EXISTS (
                            SELECT 1 FROM prestamos 
                            WHERE elemento_id = NEW.elemento_id 
                            AND estado = 'activo'
                        ) THEN
                            RAISE(ABORT, 'El elemento ya está prestado')
                    END;
                END;
            """)
            
            conn.commit()
            logger.info("Base de datos inicializada correctamente")
    
    def verificar_integridad(self):
        """Verificar y corregir inconsistencias en la base de datos"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar elementos prestados vs préstamos activos
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM elementos WHERE estado = 'prestado') as elementos_prestados,
                    (SELECT COUNT(*) FROM prestamos WHERE estado = 'activo') as prestamos_activos
            """)
            elementos_prestados, prestamos_activos = cursor.fetchone()
            
            inconsistencias = []
            
            if elementos_prestados != prestamos_activos:
                inconsistencias.append({
                    'tipo': 'Conteo inconsistente',
                    'descripcion': f'Elementos prestados: {elementos_prestados}, Préstamos activos: {prestamos_activos}'
                })
            
            # Encontrar elementos prestados sin préstamo activo
            cursor.execute("""
                SELECT e.id, e.codigo, e.nombre
                FROM elementos e
                LEFT JOIN prestamos p ON e.id = p.elemento_id AND p.estado = 'activo'
                WHERE e.estado = 'prestado' AND p.id IS NULL
            """)
            elementos_huerfanos = cursor.fetchall()
            
            if elementos_huerfanos:
                inconsistencias.append({
                    'tipo': 'Elementos huérfanos',
                    'descripcion': f'{len(elementos_huerfanos)} elementos marcados como prestados sin préstamo activo'
                })
            
            # Encontrar préstamos activos sin elemento prestado
            cursor.execute("""
                SELECT p.id, p.elemento_id, e.codigo, e.nombre, e.estado
                FROM prestamos p
                JOIN elementos e ON p.elemento_id = e.id
                WHERE p.estado = 'activo' AND e.estado != 'prestado'
            """)
            prestamos_inconsistentes = cursor.fetchall()
            
            if prestamos_inconsistentes:
                inconsistencias.append({
                    'tipo': 'Préstamos inconsistentes',
                    'descripcion': f'{len(prestamos_inconsistentes)} préstamos activos con elementos no prestados'
                })
            
            return {
                'elementos_prestados': elementos_prestados,
                'prestamos_activos': prestamos_activos,
                'inconsistencias': inconsistencias,
                'elementos_huerfanos': elementos_huerfanos,
                'prestamos_inconsistentes': prestamos_inconsistentes
            }
    
    def corregir_inconsistencias(self):
        """Corregir automáticamente las inconsistencias encontradas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Corregir elementos huérfanos (prestados sin préstamo activo)
            cursor.execute("""
                UPDATE elementos 
                SET estado = 'disponible', fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE estado = 'prestado' 
                AND id NOT IN (
                    SELECT elemento_id FROM prestamos WHERE estado = 'activo'
                )
            """)
            huerfanos_corregidos = cursor.rowcount
            
            # Corregir préstamos activos con elementos no prestados
            cursor.execute("""
                UPDATE elementos 
                SET estado = 'prestado', fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE id IN (
                    SELECT p.elemento_id 
                    FROM prestamos p 
                    WHERE p.estado = 'activo' AND p.elemento_id = elementos.id
                ) AND estado != 'prestado'
            """)
            elementos_corregidos = cursor.rowcount
            
            conn.commit()
            
            return {
                'huerfanos_corregidos': huerfanos_corregidos,
                'elementos_corregidos': elementos_corregidos
            }

# Instancia global de la base de datos
db = BEODatabase()

def autenticar_usuario():
    """Sistema de autenticación simple"""
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    if not st.session_state.autenticado:
        st.title("🏛️ Sistema BEO - Autenticación")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login"):
                usuario = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                submitted = st.form_submit_button("Ingresar")
                
                if submitted:
                    # Credenciales por defecto
                    if usuario == "beo_admin" and password == "beo2025":
                        st.session_state.autenticado = True
                        st.session_state.usuario = usuario
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
        return False
    
    return True

def cargar_datos():
    """Cargar datos de la base de datos de forma segura"""
    try:
        with db.get_connection() as conn:
            # Cargar logias
            df_logias = pd.read_sql_query("SELECT * FROM logias WHERE activa = 1", conn)
            
            # Cargar hermanos
            df_hermanos = pd.read_sql_query("""
                SELECT h.*, l.nombre as logia_nombre
                FROM hermanos h
                LEFT JOIN logias l ON h.logia_id = l.id
                WHERE h.activo = 1
            """, conn)
            
            # Cargar depósitos
            df_depositos = pd.read_sql_query("SELECT * FROM depositos WHERE activo = 1", conn)
            
            # Cargar elementos
            df_elementos = pd.read_sql_query("""
                SELECT e.*, d.nombre as deposito_nombre
                FROM elementos e
                LEFT JOIN depositos d ON e.deposito_id = d.id
            """, conn)
            
            # Cargar préstamos con información completa
            df_prestamos = pd.read_sql_query("""
                SELECT p.*, 
                       e.codigo as elemento_codigo, e.nombre as elemento_nombre,
                       h.nombre_completo as hermano_nombre, h.documento as hermano_documento,
                       l.nombre as logia_nombre
                FROM prestamos p
                JOIN elementos e ON p.elemento_id = e.id
                JOIN hermanos h ON p.hermano_id = h.id
                LEFT JOIN logias l ON h.logia_id = l.id
                ORDER BY p.fecha_creacion DESC
            """, conn)
            
            return df_logias, df_hermanos, df_depositos, df_elementos, df_prestamos
    
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        logger.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def dashboard():
    """Dashboard principal con diagnósticos mejorados"""
    st.title("📊 Dashboard BEO - Sistema Completo")
    
    # Verificar integridad
    integridad = db.verificar_integridad()
    
    # Alert de estado del sistema
    if integridad['inconsistencias']:
        st.error("⚠️ Se detectaron inconsistencias en el sistema")
        with st.expander("Ver detalles de inconsistencias"):
            for inc in integridad['inconsistencias']:
                st.write(f"**{inc['tipo']}**: {inc['descripcion']}")
        
        if st.button("🔧 Corregir Automáticamente"):
            correccion = db.corregir_inconsistencias()
            st.success(f"✅ Correcciones aplicadas: {correccion['huerfanos_corregidos']} elementos huérfanos, {correccion['elementos_corregidos']} elementos corregidos")
            st.rerun()
    else:
        st.success("✅ Sistema íntegro - No se detectaron inconsistencias")
    
    # Cargar datos
    df_logias, df_hermanos, df_depositos, df_elementos, df_prestamos = cargar_datos()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        elementos_disponibles = len(df_elementos[df_elementos['estado'] == 'disponible'])
        st.metric("🟢 Elementos Disponibles", elementos_disponibles)
    
    with col2:
        elementos_prestados = len(df_elementos[df_elementos['estado'] == 'prestado'])
        st.metric("🔴 Elementos Prestados", elementos_prestados)
    
    with col3:
        prestamos_activos = len(df_prestamos[df_prestamos['estado'] == 'activo'])
        st.metric("📋 Préstamos Activos", prestamos_activos)
    
    with col4:
        elementos_mantenimiento = len(df_elementos[df_elementos['estado'] == 'mantenimiento'])
        st.metric("🔧 En Mantenimiento", elementos_mantenimiento)
    
    # Verificación visual de consistencia
    if elementos_prestados == prestamos_activos:
        st.success(f"✅ Consistencia verificada: {elementos_prestados} elementos prestados = {prestamos_activos} préstamos activos")
    else:
        st.error(f"❌ Inconsistencia: {elementos_prestados} elementos prestados ≠ {prestamos_activos} préstamos activos")
    
    # Métricas secundarias
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏛️ Logias Activas", len(df_logias))
    
    with col2:
        st.metric("👨‍🤝‍👨 Hermanos Registrados", len(df_hermanos))
    
    with col3:
        st.metric("🏢 Depósitos Activos", len(df_depositos))
    
    with col4:
        total_elementos = len(df_elementos)
        st.metric("📦 Total Elementos", total_elementos)
    
    # Alertas de vencimiento
    if not df_prestamos.empty:
        hoy = datetime.now().date()
        prestamos_activos_df = df_prestamos[df_prestamos['estado'] == 'activo'].copy()
        
        if not prestamos_activos_df.empty:
            prestamos_activos_df['fecha_vencimiento'] = pd.to_datetime(prestamos_activos_df['fecha_vencimiento']).dt.date
            
            # Préstamos vencidos
            vencidos = prestamos_activos_df[prestamos_activos_df['fecha_vencimiento'] < hoy]
            
            # Préstamos por vencer (próximos 7 días)
            por_vencer = prestamos_activos_df[
                (prestamos_activos_df['fecha_vencimiento'] >= hoy) & 
                (prestamos_activos_df['fecha_vencimiento'] <= hoy + timedelta(days=7))
            ]
            
            if len(vencidos) > 0:
                st.error(f"🔴 **Alertas de Vencimiento:** {len(vencidos)} préstamos vencidos")
            elif len(por_vencer) > 0:
                st.warning(f"🟡 **Próximos a Vencer:** {len(por_vencer)} préstamos vencen en los próximos 7 días")
            else:
                st.success("✅ No hay préstamos próximos a vencer en los próximos 7 días")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribución por Estados")
        if not df_elementos.empty:
            estado_counts = df_elementos['estado'].value_counts()
            fig = px.pie(values=estado_counts.values, names=estado_counts.index, 
                        title="Estados de Elementos")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Préstamos por Logia")
        if not df_prestamos.empty:
            prestamos_logia = df_prestamos[df_prestamos['estado'] == 'activo']['logia_nombre'].value_counts()
            if len(prestamos_logia) > 0:
                fig = px.bar(x=prestamos_logia.index, y=prestamos_logia.values,
                            title="Préstamos Activos por Logia")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay préstamos activos para mostrar")
    
    # Gráficos adicionales
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🦽 Elementos por Categoría")
        if not df_elementos.empty:
            categoria_counts = df_elementos['categoria'].value_counts()
            fig = px.bar(x=categoria_counts.index, y=categoria_counts.values,
                        title="Inventario por Categoría")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏢 Elementos por Depósito")
        if not df_elementos.empty:
            deposito_counts = df_elementos['deposito_nombre'].value_counts()
            fig = px.bar(x=deposito_counts.index, y=deposito_counts.values,
                        title="Distribución por Depósito")
            st.plotly_chart(fig, use_container_width=True)

def gestion_logias():
    """Gestión completa de logias"""
    st.title("🏛️ Gestión de Logias")
    
    tab1, tab2, tab3 = st.tabs(["📋 Ver Logias", "➕ Agregar Logia", "✏️ Editar Logia"])
    
    df_logias, df_hermanos, df_depositos, df_elementos, df_prestamos = cargar_datos()
    
    with tab1:
        st.subheader("📜 Lista de Logias")
        
        if not df_logias.empty:
            # Agregar estadísticas por logia
            logias_con_stats = df_logias.copy()
            logias_con_stats['hermanos_count'] = 0
            logias_con_stats['prestamos_activos'] = 0
            
            for idx, logia in logias_con_stats.iterrows():
                hermanos_count = len(df_hermanos[df_hermanos['logia_id'] == logia['id']])
                prestamos_count = len(df_prestamos[
                    (df_prestamos['estado'] == 'activo') & 
                    (df_prestamos['hermano_id'].isin(df_hermanos[df_hermanos['logia_id'] == logia['id']]['id']))
                ])
                logias_con_stats.loc[idx, 'hermanos_count'] = hermanos_count
                logias_con_stats.loc[idx, 'prestamos_activos'] = prestamos_count
            
            # Mostrar tabla con información completa
            st.dataframe(
                logias_con_stats[['nombre', 'venerable_maestro', 'hospitalario', 'telefono', 'email', 'hermanos_count', 'prestamos_activos']],
                column_config={
                    'nombre': 'Nombre de la Logia',
                    'venerable_maestro': 'Venerable Maestro',
                    'hospitalario': 'Hospitalario',
                    'telefono': 'Teléfono',
                    'email': 'Email',
                    'hermanos_count': 'Hermanos',
                    'prestamos_activos': 'Préstamos Activos'
                },
                use_container_width=True
            )
        else:
            st.info("No hay logias registradas")
    
    with tab2:
        st.subheader("➕ Registrar Nueva Logia")
        
        with st.form("agregar_logia"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre de la Logia*", help="Nombre completo de la logia masónica")
                venerable_maestro = st.text_input("Venerable Maestro*")
                hospitalario = st.text_input("Hospitalario*")
            
            with col2:
                telefono = st.text_input("Teléfono de Contacto")
                email = st.text_input("Email de Contacto")
                direccion = st.text_area("Dirección de la Logia")
            
            submitted = st.form_submit_button("💾 Registrar Logia")
            
            if submitted:
                if nombre and venerable_maestro and hospitalario:
                    try:
                        with db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO logias (nombre, venerable_maestro, hospitalario, telefono, email, direccion)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (nombre, venerable_maestro, hospitalario, telefono, email, direccion))
                            conn.commit()
                            st.success("✅ Logia registrada correctamente")
                            st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Error: Ya existe una logia con ese nombre")
                    except Exception as e:
                        st.error(f"Error al registrar logia: {e}")
                else:
                    st.error("❌ Por favor complete los campos obligatorios (*)")
    
    with tab3:
        st.subheader("✏️ Editar Logia Existente")
        
        if not df_logias.empty:
            logia_seleccionada = st.selectbox(
                "Seleccionar logia a editar:",
                options=df_logias['id'].tolist(),
                format_func=lambda x: df_logias[df_logias['id'] == x]['nombre'].iloc[0]
            )
            
            if logia_seleccionada:
                logia_data = df_logias[df_logias['id'] == logia_seleccionada].iloc[0]
                
                with st.form("editar_logia"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        nombre = st.text_input("Nombre de la Logia*", value=logia_data['nombre'])
                        venerable_maestro = st.text_input("Venerable Maestro*", value=logia_data['venerable_maestro'] or "")
                        hospitalario = st.text_input("Hospitalario*", value=logia_data['hospitalario'] or "")
                    
                    with col2:
                        telefono = st.text_input("Teléfono", value=logia_data['telefono'] or "")
                        email = st.text_input("Email", value=logia_data['email'] or "")
                        direccion = st.text_area("Dirección", value=logia_data['direccion'] or "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Actualizar Logia")
                    with col2:
                        desactivar = st.form_submit_button("🗑️ Desactivar Logia", type="secondary")
                    
                    if submitted:
                        if nombre and venerable_maestro and hospitalario:
                            try:
                                with db.get_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("""
                                        UPDATE logias 
                                        SET nombre = ?, venerable_maestro = ?, hospitalario = ?, 
                                            telefono = ?, email = ?, direccion = ?
                                        WHERE id = ?
                                    """, (nombre, venerable_maestro, hospitalario, telefono, email, direccion, logia_seleccionada))
                                    conn.commit()
                                    st.success("✅ Logia actualizada correctamente")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error al actualizar logia: {e}")
                        else:
                            st.error("❌ Por favor complete los campos obligatorios (*)")
                    
                    if desactivar:
                        try:
                            with db.get_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("UPDATE logias SET activa = 0 WHERE id = ?", (logia_seleccionada,))
                                conn.commit()
                                st.success("✅ Logia desactivada correctamente")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error al desactivar logia: {e}")
        else:
            st.info("No hay logias registradas para editar")

def gestion_hermanos():
    """Gestión completa de hermanos"""
    st.title("👨‍🤝‍👨 Gestión de Hermanos")
    
    tab1, tab2, tab3 = st.tabs(["📋 Ver Hermanos", "➕ Agregar Hermano", "✏️ Editar Hermano"])
    
    df_logias, df_hermanos, df_depositos, df_elementos, df_prestamos = cargar_datos()
    
    with tab1:
        st.subheader("👥 Lista de Hermanos")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_logia = st.selectbox("Filtrar por Logia:", 
                                      ["Todas"] + list(df_hermanos['logia_nombre'].dropna().unique()))
        with col2:
            filtro_grado = st.selectbox("Filtrar por Grado:", 
                                      ["Todos"] + list(df_hermanos['grado'].dropna().unique()))
        with col3:
            buscar_nombre = st.text_input("Buscar por nombre:")
        
        # Aplicar filtros
        df_filtrado = df_hermanos.copy()
        if filtro_logia != "Todas":
            df_filtrado = df_filtrado[df_filtrado['logia_nombre'] == filtro_logia]
        if filtro_grado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['grado'] == filtro_grado]
        if buscar_nombre:
            df_filtrado = df_filtrado[df_filtrado['nombre_completo'].str.contains(buscar_nombre, case=False, na=False)]
        
        if not df_filtrado.empty:
            # Agregar estadísticas de préstamos
            hermanos_con_stats = df_filtrado.copy()
            hermanos_con_stats['prestamos_activos'] = 0
            hermanos_con_stats['total_prestamos'] = 0
            
            for idx, hermano in hermanos_con_stats.iterrows():
                activos = len(df_prestamos[
                    (df_prestamos['hermano_id'] == hermano['id']) & 
                    (df_prestamos['estado'] == 'activo')
                ])
                total = len(df_prestamos[df_prestamos['hermano_id'] == hermano['id']])
                hermanos_con_stats.loc[idx, 'prestamos_activos'] = activos
                hermanos_con_stats.loc[idx, 'total_prestamos'] = total
            
            st.dataframe(
                hermanos_con_stats[['nombre_completo', 'documento', 'logia_nombre', 'grado', 'telefono', 'email', 'prestamos_activos', 'total_prestamos']],
                column_config={
                    'nombre_completo': 'Nombre Completo',
                    'documento': 'Documento',
                    'logia_nombre': 'Logia',
                    'grado': 'Grado',
                    'telefono': 'Teléfono',
                    'email': 'Email',
                    'prestamos_activos': 'Préstamos Activos',
                    'total_prestamos': 'Total Préstamos'
                },
                use_container_width=True
            )
        else:
            st.info("No se encontraron hermanos con los filtros aplicados")
    
    with tab2:
        st.subheader("➕ Registrar Nuevo Hermano")
        
        with st.form("agregar_hermano"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre_completo = st.text_input("Nombre Completo*")
                documento = st.text_input("Documento de Identidad*")
                if not df_logias.empty:
                    logia_id = st.selectbox("Logia*", 
                                          options=[None] + df_logias['id'].tolist(),
                                          format_func=lambda x: "Seleccionar logia..." if x is None else df_logias[df_logias['id'] == x]['nombre'].iloc[0])
                else:
                    st.warning("⚠️ Primero debe registrar al menos una logia")
                    logia_id = None
                grado = st.selectbox("Grado Masónico*", 
                                   ["Aprendiz", "Compañero", "Maestro Masón", "Grado Superior"])
            
            with col2:
                telefono = st.text_input("Teléfono de Contacto")
                email = st.text_input("Email")
                direccion = st.text_area("Dirección de Residencia")
            
            submitted = st.form_submit_button("💾 Registrar Hermano")
            
            if submitted:
                if nombre_completo and documento and logia_id and grado:
                    try:
                        with db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO hermanos (nombre_completo, documento, logia_id, grado, telefono, email, direccion)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (nombre_completo, documento, logia_id, grado, telefono, email, direccion))
                            conn.commit()
                            st.success("✅ Hermano registrado correctamente")
                            st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Error: Ya existe un hermano con ese documento")
                    except Exception as e:
                        st.error(f"Error al registrar hermano: {e}")
                else:
                    st.error("❌ Por favor complete los campos obligatorios (*)")
    
    with tab3:
        st.subheader("✏️ Editar Hermano Existente")
        
        if not df_hermanos.empty:
            hermano_seleccionado = st.selectbox(
                "Seleccionar hermano a editar:",
                options=df_hermanos['id'].tolist(),
                format_func=lambda x: f"{df_hermanos[df_hermanos['id'] == x]['nombre_completo'].iloc[0]} ({df_hermanos[df_hermanos['id'] == x]['documento'].iloc[0]})"
            )
            
            if hermano_seleccionado:
                hermano_data = df_hermanos[df_hermanos['id'] == hermano_seleccionado].iloc[0]
                
                with st.form("editar_hermano"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        nombre_completo = st.text_input("Nombre Completo*", value=hermano_data['nombre_completo'])
                        documento = st.text_input("Documento*", value=hermano_data['documento'] or "")
                        if not df_logias.empty:
                            logia_actual_index = df_logias['id'].tolist().index(hermano_data['logia_id']) if hermano_data['logia_id'] in df_logias['id'].tolist() else 0
                            logia_id = st.selectbox("Logia*", 
                                                  options=df_logias['id'].tolist(),
                                                  index=logia_actual_index,
                                                  format_func=lambda x: df_logias[df_logias['id'] == x]['nombre'].iloc[0])
                        grado = st.selectbox("Grado Masónico*", 
                                           ["Aprendiz", "Compañero", "Maestro Masón", "Grado Superior"],
                                           index=["Aprendiz", "Compañero", "Maestro Masón", "Grado Superior"].index(hermano_data['grado']) if hermano_data['grado'] in ["Aprendiz", "Compañero", "Maestro Masón", "Grado Superior"] else 0)
                    
                    with col2:
                        telefono = st.text_input("Teléfono", value=hermano_data['telefono'] or "")
                        email = st.text_input("Email", value=hermano_data['email'] or "")
                        direccion = st.text_area("Dirección", value=hermano_data['direccion'] or "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Actualizar Hermano")
                    with col2:
                        desactivar = st.form_submit_button("🗑️ Desactivar Hermano", type="secondary")
                    
                    if submitted:
                        if nombre_completo and documento and logia_id and grado:
                            try:
                                with db.get_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("""
                                        UPDATE hermanos 
                                        SET nombre_completo = ?, documento = ?, logia_id = ?, grado = ?, 
                                            telefono = ?, email = ?, direccion = ?
                                        WHERE id = ?
                                    """, (nombre_completo, documento, logia_id, grado, telefono, email, direccion, hermano_seleccionado))
                                    conn.commit()
                                    st.success("✅ Hermano actualizado correctamente")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error al actualizar hermano: {e}")
                        else:
                            st.error("❌ Por favor complete los campos obligatorios (*)")
                    
                    if desactivar:
                        # Verificar si tiene préstamos activos
                        prestamos_activos = len(df_prestamos[
                            (df_prestamos['hermano_id'] == hermano_seleccionado) & 
                            (df_prestamos['estado'] == 'activo')
                        ])
                        
                        if prestamos_activos > 0:
                            st.error(f"❌ No se puede desactivar: el hermano tiene {prestamos_activos} préstamos activos")
                        else:
                            try:
                                with db.get_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("UPDATE hermanos SET activo = 0 WHERE id = ?", (hermano_seleccionado,))
                                    conn.commit()
                                    st.success("✅ Hermano desactivado correctamente")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error al desactivar hermano: {e}")
        else:
            st.info("No hay hermanos registrados para editar")

def gestion_depositos():
    """Gestión completa de depósitos"""
    st.title("🏢 Gestión de Depósitos")
    
    tab1, tab2, tab3 = st.tabs(["📋 Ver Depósitos", "➕ Agregar Depósito", "✏️ Editar Depósito"])
    
    df_logias, df_hermanos, df_depositos, df_elementos, df_prestamos = cargar_datos()
    
    with tab1:
        st.subheader("🏪 Lista de Depósitos")
        
        if not df_depositos.empty:
            # Agregar estadísticas por depósito
            depositos_con_stats = df_depositos.copy()
            depositos_con_stats['elementos_total'] = 0
            depositos_con_stats['elementos_disponibles'] = 0
            depositos_con_stats['elementos_prestados'] = 0
            
            for idx, deposito in depositos_con_stats.iterrows():
                elementos_deposito = df_elementos[df_elementos['deposito_id'] == deposito['id']]
                total = len(elementos_deposito)
                disponibles = len(elementos_deposito[elementos_deposito['estado'] == 'disponible'])
                prestados = len(elementos_deposito[elementos_deposito['estado'] == 'prestado'])
                
                depositos_con_stats.loc[idx, 'elementos_total'] = total
                depositos_con_stats.loc[idx, 'elementos_disponibles'] = disponibles
                depositos_con_stats.loc[idx, 'elementos_prestados'] = prestados
            
            st.dataframe(
                depositos_con_stats[['nombre', 'ubicacion', 'responsable', 'telefono', 'elementos_total', 'elementos_disponibles', 'elementos_prestados']],
                column_config={
                    'nombre': 'Nombre del Depósito',
                    'ubicacion': 'Ubicación',
                    'responsable': 'Responsable',
                    'telefono': 'Teléfono',
                    'elementos_total': 'Total Elementos',
                    'elementos_disponibles': 'Disponibles',
                    'elementos_prestados': 'Prestados'
                },
                use_container_width=True
            )
        else:
            st.info("No hay depósitos registrados")
    
    with tab2:
        st.subheader("➕ Registrar Nuevo Depósito")
        
        with st.form("agregar_deposito"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre del Depósito*", help="Nombre identificatorio del depósito")
                ubicacion = st.text_input("Ubicación*", help="Dirección o ubicación física")
                responsable = st.text_input("Responsable*", help="Persona encargada del depósito")
            
            with col2:
                telefono = st.text_input("Teléfono de Contacto")
                observaciones = st.text_area("Observaciones", help="Información adicional sobre el depósito")
            
            submitted = st.form_submit_button("💾 Registrar Depósito")
            
            if submitted:
                if nombre and ubicacion and responsable:
                    try:
                        with db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO depositos (nombre, ubicacion, responsable, telefono)
                                VALUES (?, ?, ?, ?)
                            """, (nombre, ubicacion, responsable, telefono))
                            conn.commit()
                            st.success("✅ Depósito registrado correctamente")
                            st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Error: Ya existe un depósito con ese nombre")
                    except Exception as e:
                        st.error(f"Error al registrar depósito: {e}")
                else:
                    st.error("❌ Por favor complete los campos obligatorios (*)")
    
    with tab3:
        st.subheader("✏️ Editar Depósito Existente")
        
        if not df_depositos.empty:
            deposito_seleccionado = st.selectbox(
                "Seleccionar depósito a editar:",
                options=df_depositos['id'].tolist(),
                format_func=lambda x: df_depositos[df_depositos['id'] == x]['nombre'].iloc[0]
            )
            
            if deposito_seleccionado:
                deposito_data = df_depositos[df_depositos['id'] == deposito_seleccionado].iloc[0]
                
                with st.form("editar_deposito"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        nombre = st.text_input("Nombre del Depósito*", value=deposito_data['nombre'])
                        ubicacion = st.text_input("Ubicación*", value=deposito_data['ubicacion'] or "")
                        responsable = st.text_input("Responsable*", value=deposito_data['responsable'] or "")
                    
                    with col2:
                        telefono = st.text_input("Teléfono", value=deposito_data['telefono'] or "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("💾 Actualizar Depósito")
                    with col2:
                        desactivar = st.form_submit_button("🗑️ Desactivar Depósito", type="secondary")
                    
                    if submitted:
                        if nombre and ubicacion and responsable:
                            try:
                                with db.get_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("""
                                        UPDATE depositos 
                                        SET nombre = ?, ubicacion = ?, responsable = ?, telefono = ?
                                        WHERE id = ?
                                    """, (nombre, ubicacion, responsable, telefono, deposito_seleccionado))
                                    conn.commit()
                                    st.success("✅ Depósito actualizado correctamente")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error al actualizar depósito: {e}")
                        else:
                            st.error("❌ Por favor complete los campos obligatorios (*)")
                    
                    if desactivar:
                        # Verificar si tiene elementos
                        elementos_en_deposito = len(df_elementos[df_elementos['deposito_id'] == deposito_seleccionado])
                        
                        if elementos_en_deposito > 0:
                            st.error(f"❌ No se puede desactivar: el depósito tiene {elementos_en_deposito} elementos asignados")
                        else:
                            try:
                                with db.get_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("UPDATE depositos SET activo = 0 WHERE id = ?", (deposito_seleccionado,))
                                    conn.commit()
                                    st.success("✅ Depósito desactivado correctamente")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error al desactivar depósito: {e}")
        else:
            st.info("No hay depósitos registrados para editar")

def gestion_elementos():
    """Gestión completa de elementos"""
    st.title("🦽 Gestión de Elementos")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Ver Elementos", "➕ Agregar", "✏️ Editar", "🔧 Mantenimiento"])
    
    df_logias, df_hermanos, df_depositos, df_elementos, df_prestamos = cargar_datos()
    
    with tab1:
        st.subheader("📦 Inventario de Elementos")
        
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            filtro_estado = st.selectbox("Filtrar por estado:", 
                                       ["Todos"] + list(df_elementos['estado'].unique()))
        with col2:
            filtro_categoria = st.selectbox("Filtrar por categoría:", 
                                          ["Todas"] + list(df_elementos['categoria'].unique()))
        with col3:
            filtro_deposito = st.selectbox("Filtrar por depósito:", 
                                         ["Todos"] + list(df_elementos['deposito_nombre'].dropna().unique()))
        with col4:
            buscar_codigo = st.text_input("Buscar por código/nombre:")
        
        # Aplicar filtros
        df_filtrado = df_elementos.copy()
        if filtro_estado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['estado'] == filtro_estado]
        if filtro_categoria != "Todas":
            df_filtrado = df_filtrado[df_filtrado['categoria'] == filtro_categoria]
        if filtro_deposito != "Todos":
            df_filtrado = df_filtrado[df_filtrado['deposito_nombre'] == filtro_deposito]
        if buscar_codigo:
            df_filtrado = df_filtrado[
                df_filtrado['codigo'].str.contains(buscar_codigo, case=False, na=False) |
                df_filtrado['nombre'].str.contains(buscar_codigo, case=False, na=False)
            ]
        
        # Mostrar elementos
        if not df_filtrado.empty:
            st.dataframe(
                df_filtrado[['codigo', 'nombre', 'categoria', 'marca', 'modelo', 'estado', 'deposito_nombre', 'precio_compra']],
                column_config={
                    'codigo': 'Código',
                    'nombre': 'Nombre',
                    'categoria': 'Categoría', 
                    'marca': 'Marca',
                    'modelo': 'Modelo',
                    'estado': 'Estado',
                    'deposito_nombre': 'Depósito',
                    'precio_compra': st.column_config.NumberColumn('Precio', format="$%.2f")
                },
                use_container_width=True
            )
        else:
            st.info("No se encontraron elementos con los filtros aplicados")
    
    with tab2:
        st.subheader("➕ Agregar Nuevo Elemento")
        
        with st.form("agregar_elemento"):
            col1, col2 = st.columns(2)
            
            with col1:
                codigo = st.text_input("Código único*", help="Código identificador único del elemento")
                nombre = st.text_input("Nombre del elemento*")
                categoria = st.selectbox("Categoría*", 
                                       ["Bastones", "Sillas de Ruedas", "Andadores", "Camas Ortopédicas", 
                                        "Equipos de Rehabilitación", "Muletas", "Otros"])
                marca = st.text_input("Marca")
                modelo = st.text_input("Modelo")
                descripcion = st.text_area("Descripción")
            
            with col2:
                if not df_depositos.empty:
                    deposito_id = st.selectbox("Depósito*", 
                                             options=[None] + df_depositos['id'].tolist(),
                                             format_func=lambda x: "Seleccionar depósito..." if x is None else df_depositos[df_depositos['id'] == x]['nombre'].iloc[0])
                else:
                    st.warning("⚠️ Primero debe registrar al menos un depósito")
                    deposito_id = None
                
                precio_compra = st.number_input("Precio de compra", min_value=0.0, step=100.0)
                fecha_compra = st.date_input("Fecha de compra")
                observaciones = st.text_area("Observaciones")
            
            submitted = st.form_submit_button("💾 Guardar Elemento")
            
            if submitted:
                if codigo and nombre and categoria and deposito_id:
                    try:
                        with db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO elementos (codigo, nombre, categoria, marca, modelo, descripcion,
                                                     deposito_id, precio_compra, fecha_compra, observaciones)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (codigo, nombre, categoria, marca, modelo, descripcion,
                                 deposito_id, precio_compra, fecha_compra, observaciones))
                            conn.commit()
                            st.success("✅ Elemento agregado correctamente")
                            st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Error: El código ya existe. Use un código único.")
                    except Exception as e:
                        st.error(f"Error al agregar elemento: {e}")
                else:
                    st.error("❌ Por favor complete los campos obligatorios (*)")
    
    with tab3:
        st.subheader("✏️ Editar Elemento Existente")
        
        if not df_elementos.empty:
            elemento_seleccionado = st.selectbox(
                "Seleccionar elemento a editar:",
                options=df_elementos['id'].tolist(),
                format_func=lambda x: f"{df_elementos[df_elementos['id'] == x]['codigo'].iloc[0]} - {df_elementos[df_elementos['id'] == x]['nombre'].iloc[0]}"
            )
            
            if elemento_seleccionado:
                elemento_data = df_elementos[df_elementos['id'] == elemento_seleccionado].iloc[0]
                
                with st.form("editar_elemento"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        codigo = st.text_input("Código único*", value=elemento_data['codigo'])
                        nombre = st.text_input("Nombre*", value=elemento_data['nombre'])
                        categoria = st.selectbox("Categoría*", 
                                               ["Bastones", "Sillas de Ruedas", "Andadores", "Camas Ortopédicas", 
                                                "Equipos de Rehabilitación", "Muletas", "Otros"],
                                               index=["Bastones", "Sillas de Ruedas", "Andadores", "Camas Ortopédicas", 
                                                     "Equipos de Rehabilitación", "Muletas", "Otros"].index(elemento_data['categoria']) if elemento_data['categoria'] in ["Bastones", "Sillas de Ruedas", "Andadores", "Camas Ortopédicas", "Equipos de Rehabilitación", "Muletas", "Otros"] else 0)
                        marca = st.text_input("Marca", value=elemento_data['marca'] or "")
                        modelo = st.text_input("Modelo", value=elemento_data['modelo'] or "")
                        descripcion = st.text_area("Descripción", value=elemento_data['descripcion'] or "")
                    
                    with col2:
                        if not df_depositos.empty:
                            deposito_actual_index = df_depositos['id'].tolist().index(elemento_data['deposito_id']) if elemento_data['deposito_id'] in df_depositos['id'].tolist() else 0
                            deposito_id = st.selectbox("Depósito*", 
                                                     options=df_depositos['id'].tolist(),
                                                     index=deposito_actual_index,
                                                     format_func=lambda x: df_depositos[df_depositos['id'] == x]['nombre'].iloc[0])
                        
                        precio_compra = st.number_input("Precio de compra", min_value=0.0, step=100.0, value=float(elemento_data['precio_compra'] or 0))
                        fecha_compra = st.date_input("Fecha de compra", value=pd.to_datetime(elemento_data['fecha_compra']).date() if elemento_data['fecha_compra'] else datetime.now().date())
                        observaciones = st.text_area("Observaciones", value=elemento_data['observaciones'] or "")
                    
                    submitted = st.form_submit_button("💾 Actualizar Elemento")
                    
                    if submitted:
                        if codigo and nombre and categoria and deposito_id:
                            try:
                                with db.get_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("""
                                        UPDATE elementos 
                                        SET codigo = ?, nombre = ?, categoria = ?, marca = ?, modelo = ?, 
                                            descripcion = ?, deposito_id = ?, precio_compra = ?, 
                                            fecha_compra = ?, observaciones = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                                        WHERE id = ?
                                    """, (codigo, nombre, categoria, marca, modelo, descripcion,
                                         deposito_id, precio_compra, fecha_compra, observaciones, elemento_seleccionado))
                                    conn.commit()
                                    st.success("✅ Elemento actualizado correctamente")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error al actualizar elemento: {e}")
                        else:
                            st.error("❌ Por favor complete los campos obligatorios (*)")
        else:
            st.info("No hay elementos registrados para editar")
    
    with tab4:
        st.subheader("🔧 Cambio Manual de Estados")
        st.warning("⚠️ Use esta función solo para correcciones administrativas")
        
        if not df_elementos.empty:
            elemento_seleccionado = st.selectbox("Seleccionar elemento:",
                                                options=df_elementos['id'].tolist(),
                                                format_func=lambda x: f"{df_elementos[df_elementos['id'] == x]['codigo'].iloc[0]} - {df_elementos[df_elementos['id'] == x]['nombre'].iloc[0]} (Estado: {df_elementos[df_elementos['id'] == x]['estado'].iloc[0]})")
            
            if elemento_seleccionado:
                elemento_actual = df_elementos[df_elementos['id'] == elemento_seleccionado].iloc[0]
                st.info(f"Estado actual: **{elemento_actual['estado']}**")
                
                nuevo_estado = st.selectbox("Nuevo estado:", 
                                          ["disponible", "prestado", "mantenimiento", "dado_baja"])
                motivo = st.text_input("Motivo del cambio*")
                
                if st.button("🔄 Cambiar Estado"):
                    if motivo:
                        try:
                            with db.get_connection() as conn:
                                cursor = conn.cursor()
                                
                                # Obtener estado actual
                                cursor.execute("SELECT estado FROM elementos WHERE id = ?", (elemento_seleccionado,))
                                estado_actual = cursor.fetchone()[0]
                                
                                # Actualizar estado
                                cursor.execute("""
                                    UPDATE elementos 
                                    SET estado = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                """, (nuevo_estado, elemento_seleccionado))
                                
                                # Registrar en historial
                                cursor.execute("""
                                    INSERT INTO historial_estados (elemento_id, estado_anterior, estado_nuevo, motivo, usuario)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (elemento_seleccionado, estado_actual, nuevo_estado, motivo, st.session_state.get('usuario', 'Sistema')))
                                
                                conn.commit()
                                st.success("✅ Estado cambiado correctamente")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error al cambiar estado: {e}")
                    else:
                        st.error("❌ El motivo es obligatorio")
        else:
            st.info("No hay elementos registrados")

def formulario_prestamo():
    """Formulario completo de préstamo BEO"""
    st.title("📋 Formulario de Préstamo BEO")
    
    df_logias, df_hermanos, df_depositos, df_elementos, df_prestamos = cargar_datos()
    
    # Verificar datos necesarios
    if df_hermanos.empty:
        st.error("❌ No hay hermanos registrados. Primero debe registrar hermanos.")
        return
    
    elementos_disponibles = df_elementos[df_elementos['estado'] == 'disponible']
    if elementos_disponibles.empty:
        st.error("❌ No hay elementos disponibles para préstamo.")
        return
    
    st.info("📝 **Proceso simplificado para recibir elementos devueltos**")
    st.write("**Tip:** Solo completa lo esencial - fecha, quién recibe y qué depósito va")
    
    with st.form("formulario_prestamo"):
        st.subheader("👨‍🤝‍👨 Información del Hermano Solicitante")
        
        col1, col2 = st.columns(2)
        
        with col1:
            hermano_id = st.selectbox("Hermano Solicitante*",
                                    options=df_hermanos['id'].tolist(),
                                    format_func=lambda x: f"{df_hermanos[df_hermanos['id'] == x]['nombre_completo'].iloc[0]} - {df_hermanos[df_hermanos['id'] == x]['logia_nombre'].iloc[0]}")
        
        with col2:
            if hermano_id:
                hermano_data = df_hermanos[df_hermanos['id'] == hermano_id].iloc[0]
                st.text_input("Logia", value=hermano_data['logia_nombre'], disabled=True)
        
        st.subheader("👥 Información del Beneficiario")
        
        col1, col2 = st.columns(2)
        
        with col1:
            beneficiario_tipo = st.radio("El elemento es para:", ["hermano", "familiar"])
        
        with col2:
            if beneficiario_tipo == "familiar":
                beneficiario_nombre = st.text_input("Nombre del Familiar*")
                beneficiario_parentesco = st.selectbox("Parentesco", 
                                                     ["Cónyuge", "Hijo/a", "Padre/Madre", "Hermano/a", "Otro"])
                beneficiario_documento = st.text_input("Documento del Familiar")
            else:
                beneficiario_nombre = hermano_data['nombre_completo'] if hermano_id else ""
                beneficiario_parentesco = None
                beneficiario_documento = hermano_data['documento'] if hermano_id else ""
        
        st.subheader("🦽 Selección de Elemento")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtros para elementos
            categoria_filtro = st.selectbox("Filtrar por categoría:", 
                                          ["Todas"] + list(elementos_disponibles['categoria'].unique()))
            
            if categoria_filtro != "Todas":
                elementos_filtrados = elementos_disponibles[elementos_disponibles['categoria'] == categoria_filtro]
            else:
                elementos_filtrados = elementos_disponibles
                
            elemento_id = st.selectbox("Elemento a prestar*",
                                     options=elementos_filtrados['id'].tolist(),
                                     format_func=lambda x: f"{elementos_filtrados[elementos_filtrados['id'] == x]['codigo'].iloc[0]} - {elementos_filtrados[elementos_filtrados['id'] == x]['nombre'].iloc[0]} ({elementos_filtrados[elementos_filtrados['id'] == x]['deposito_nombre'].iloc[0]})")
        
        with col2:
            if elemento_id:
                elemento_data = elementos_filtrados[elementos_filtrados['id'] == elemento_id].iloc[0]
                st.text_input("Marca/Modelo", value=f"{elemento_data['marca'] or 'N/A'} / {elemento_data['modelo'] or 'N/A'}", disabled=True)
                st.text_input("Depósito Actual", value=elemento_data['deposito_nombre'], disabled=True)
        
        st.subheader("📅 Duración del Préstamo")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            duracion_dias = st.number_input("Duración (días)*", min_value=1, max_value=365, value=30)
        
        with col2:
            fecha_prestamo = st.date_input("Fecha de préstamo*", value=datetime.now().date())
        
        with col3:
            fecha_vencimiento = fecha_prestamo + timedelta(days=duracion_dias)
            st.date_input("Fecha de vencimiento", value=fecha_vencimiento, disabled=True)
        
        st.subheader("📍 Información de Entrega")
        
        col1, col2 = st.columns(2)
        
        with col1:
            direccion_entrega = st.text_area("Dirección de entrega*", 
                                           value=hermano_data['direccion'] if hermano_id and hermano_data['direccion'] else "")
        
        with col2:
            responsable_entrega = st.text_input("Responsable de entrega*", 
                                              value=st.session_state.get('usuario', ''))
            observaciones = st.text_area("Observaciones del préstamo")
        
        submitted = st.form_submit_button("📋 Registrar Préstamo")
        
        if submitted:
            # Validaciones
            errores = []
            if not hermano_id:
                errores.append("Debe seleccionar un hermano")
            if beneficiario_tipo == "familiar" and not beneficiario_nombre:
                errores.append("Debe completar el nombre del familiar")
            if not elemento_id:
                errores.append("Debe seleccionar un elemento")
            if not direccion_entrega:
                errores.append("Debe completar la dirección de entrega")
            if not responsable_entrega:
                errores.append("Debe completar el responsable de entrega")
            
            if errores:
                st.error("❌ Por favor corrija los siguientes errores:")
                for error in errores:
                    st.write(f"- {error}")
            else:
                try:
                    with db.get_connection() as conn:
                        cursor = conn.cursor()
                        
                        # Verificar que el elemento sigue disponible
                        cursor.execute("SELECT estado FROM elementos WHERE id = ?", (elemento_id,))
                        estado_actual = cursor.fetchone()[0]
                        
                        if estado_actual != 'disponible':
                            st.error(f"❌ Error: El elemento ya no está disponible (Estado: {estado_actual})")
                            return
                        
                        # Insertar préstamo
                        cursor.execute("""
                            INSERT INTO prestamos (
                                elemento_id, hermano_id, beneficiario_tipo, beneficiario_nombre,
                                beneficiario_parentesco, beneficiario_documento, direccion_entrega,
                                duracion_dias, fecha_prestamo, fecha_vencimiento,
                                observaciones_prestamo, responsable_entrega
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            elemento_id, hermano_id, beneficiario_tipo, beneficiario_nombre,
                            beneficiario_parentesco, beneficiario_documento, direccion_entrega,
                            duracion_dias, fecha_prestamo, fecha_vencimiento,
                            observaciones, responsable_entrega
                        ))
                        
                        prestamo_id = cursor.lastrowid
                        
                        # El trigger se encargará de actualizar el estado del elemento
                        conn.commit()
                        
                        st.success(f"✅ Préstamo registrado correctamente (ID: {prestamo_id})")
                        st.balloons()
                        
                        # Mostrar resumen
                        with st.expander("📄 Resumen del Préstamo"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Hermano:** {hermano_data['nombre_completo']}")
                                st.write(f"**Logia:** {hermano_data['logia_nombre']}")
                                st.write(f"**Beneficiario:** {beneficiario_nombre}")
                                st.write(f"**Tipo:** {beneficiario_tipo}")
                            with col2:
                                st.write(f"**Elemento:** {elemento_data['codigo']} - {elemento_data['nombre']}")
                                st.write(f"**Fecha préstamo:** {fecha_prestamo}")
                                st.write(f"**Fecha vencimiento:** {fecha_vencimiento}")
                                st.write(f"**Responsable:** {responsable_entrega}")
                        
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error al registrar préstamo: {e}")
                    logger.error(f"Error en préstamo: {e}")

def devolucion_simple():
    """Módulo de devolución simple corregido"""
    st.title("🔄 Devolución Simple de Elementos")
    
    # Cargar datos
    df_logias, df_hermanos, df_depositos, df_elementos, df_prestamos = cargar_datos()
    
    # Filtrar préstamos activos (CORREGIDO)
    prestamos_activos = df_prestamos[df_prestamos['estado'] == 'activo'].copy()
    
    st.write(f"🔍 **Debug - Préstamos encontrados:** {len(prestamos_activos)}")
    
    if prestamos_activos.empty:
        st.info("ℹ️ No hay elementos prestados actualmente para devolver.")
        
        # Mostrar información de debug
        with st.expander("🔍 Información de Debug"):
            st.write(f"Total de préstamos en BD: {len(df_prestamos)}")
            if not df_prestamos.empty:
                st.write("Estados de préstamos existentes:")
                estados = df_prestamos['estado'].value_counts()
                st.write(estados)
        return
    
    st.success(f"✅ Elementos encontrados para devolución: {len(prestamos_activos)}")
    
    # Mostrar tabla de préstamos activos
    st.subheader("📋 Préstamos Activos")
    
    # Calcular estado de vencimiento
    hoy = datetime.now().date()
    prestamos_display = prestamos_activos.copy()
    prestamos_display['fecha_vencimiento'] = pd.to_datetime(prestamos_display['fecha_vencimiento']).dt.date
    prestamos_display['dias_restantes'] = (prestamos_display['fecha_vencimiento'] - hoy).dt.days
    prestamos_display['estado_vencimiento'] = prestamos_display['dias_restantes'].apply(
        lambda x: "🔴 Vencido" if x < 0 else "🟡 Por vencer" if x <= 7 else "🟢 Vigente"
    )
    
    # Mostrar tabla
    st.dataframe(
        prestamos_display[['elemento_codigo', 'elemento_nombre', 'hermano_nombre', 'fecha_prestamo', 'fecha_vencimiento', 'estado_vencimiento']],
        column_config={
            'elemento_codigo': 'Código',
            'elemento_nombre': 'Elemento', 
            'hermano_nombre': 'Hermano',
            'fecha_prestamo': 'Fecha Préstamo',
            'fecha_vencimiento': 'Fecha Vencimiento',
            'estado_vencimiento': 'Estado'
        },
        use_container_width=True
    )
    
    # Formulario de devolución
    st.subheader("🔄 Procesar Devolución")
    
    with st.form("devolucion_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Seleccionar préstamo
            opciones_prestamo = [f"{row['elemento_codigo']} - {row['elemento_nombre']} (Prestado a: {row['hermano_nombre']})" 
                               for _, row in prestamos_activos.iterrows()]
            prestamo_seleccionado = st.selectbox("Seleccionar préstamo a devolver:", opciones_prestamo)
            
            # Obtener ID del préstamo seleccionado
            if prestamo_seleccionado:
                indice_seleccionado = opciones_prestamo.index(prestamo_seleccionado)
                prestamo_id = prestamos_activos.iloc[indice_seleccionado]['id']
                prestamo_data = prestamos_activos.iloc[indice_seleccionado]
                
                # Información del préstamo seleccionado
                st.info(f"**Elemento:** {prestamo_data['elemento_nombre']}\n**Hermano:** {prestamo_data['hermano_nombre']}\n**Vence:** {prestamo_data['fecha_vencimiento']}")
        
        with col2:
            # Información adicional
            responsable_recepcion = st.text_input("Responsable de recepción*", 
                                                value=st.session_state.get('usuario', ''))
            
            # Seleccionar depósito de devolución
            if not df_depositos.empty:
                deposito_devolucion = st.selectbox("Depósito de devolución*",
                                                 options=df_depositos['id'].tolist(),
                                                 format_func=lambda x: df_depositos[df_depositos['id'] == x]['nombre'].iloc[0])
            else:
                st.warning("⚠️ No hay depósitos registrados")
                deposito_devolucion = None
            
            estado_elemento = st.selectbox("Estado del elemento al devolverse*",
                                         ["disponible", "mantenimiento"],
                                         help="Seleccione 'mantenimiento' si el elemento está dañado")
            
            observaciones = st.text_area("Observaciones de devolución")
        
        submitted = st.form_submit_button("🔄 Procesar Devolución")
        
        if submitted and prestamo_seleccionado:
            if not responsable_recepcion:
                st.error("❌ Debe completar el responsable de recepción")
            elif not deposito_devolucion:
                st.error("❌ Debe seleccionar un depósito")
            else:
                try:
                    with db.get_connection() as conn:
                        cursor = conn.cursor()
                        
                        # Actualizar préstamo como devuelto
                        cursor.execute("""
                            UPDATE prestamos 
                            SET estado = 'devuelto',
                                fecha_devolucion = date('now'),
                                responsable_recepcion = ?,
                                observaciones_devolucion = ?
                            WHERE id = ?
                        """, (responsable_recepcion, observaciones, prestamo_id))
                        
                        # Actualizar elemento con nuevo depósito y estado
                        cursor.execute("""
                            UPDATE elementos 
                            SET estado = ?, deposito_id = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (estado_elemento, deposito_devolucion, prestamo_data['elemento_id']))
                        
                        # Registrar en historial
                        cursor.execute("""
                            INSERT INTO historial_estados (elemento_id, estado_anterior, estado_nuevo, motivo, usuario)
                            VALUES (?, ?, ?, ?, ?)
                        """, (prestamo_data['elemento_id'], 'prestado', estado_elemento, 
                             f"Devolución de préstamo ID: {prestamo_id}", responsable_recepcion))
                        
                        conn.commit()
                        
                        st.success("✅ Devolución procesada correctamente")
                        if estado_elemento == "mantenimiento":
                            st.warning("⚠️ Elemento marcado para mantenimiento")
                        st.balloons()
                        
                        # Recargar página
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error al procesar devolución: {e}")
                    logger.error(f"Error en devolución: {e}")

def alertas_vencimiento():
    """Módulo de alertas de vencimiento"""
    st.title("⚠️ Alertas de Vencimiento")
    
    df_logias, df_hermanos, df_depositos, df_elementos, df_prestamos = cargar_datos()
    
    if df_prestamos.empty:
        st.info("No hay préstamos registrados")
        return
    
    # Filtrar préstamos activos
    prestamos_activos = df_prestamos[df_prestamos['estado'] == 'activo'].copy()
    
    if prestamos_activos.empty:
        st.success("✅ No hay préstamos próximos a vencer en los próximos 7 días")
        return
    
    # Calcular días para vencimiento
    hoy = datetime.now().date()
    prestamos_activos['fecha_vencimiento'] = pd.to_datetime(prestamos_activos['fecha_vencimiento']).dt.date
    prestamos_activos['dias_restantes'] = (prestamos_activos['fecha_vencimiento'] - hoy).dt.days
    
    # Clasificar préstamos
    vencidos = prestamos_activos[prestamos_activos['dias_restantes'] < 0]
    por_vencer = prestamos_activos[(prestamos_activos['dias_restantes'] >= 0) & (prestamos_activos['dias_restantes'] <= 7)]
    vigentes = prestamos_activos[prestamos_activos['dias_restantes'] > 7]
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🔴 Préstamos Vencidos", len(vencidos))
    
    with col2:
        st.metric("🟡 Por Vencer (7 días)", len(por_vencer))
    
    with col3:
        st.metric("🟢 Vigentes", len(vigentes))
    
    # Mostrar préstamos vencidos
    if not vencidos.empty:
        st.subheader("🔴 Préstamos Vencidos")
        vencidos_display = vencidos.copy()
        vencidos_display['dias_vencido'] = abs(vencidos_display['dias_restantes'])
        
        st.dataframe(
            vencidos_display[['elemento_codigo', 'elemento_nombre', 'hermano_nombre', 'fecha_vencimiento', 'dias_vencido']],
            column_config={
                'elemento_codigo': 'Código',
                'elemento_nombre': 'Elemento',
                'hermano_nombre': 'Hermano',
                'fecha_vencimiento': 'Fecha Vencimiento',
                'dias_vencido': 'Días Vencido'
            },
            use_container_width=True
        )
    
    # Mostrar préstamos por vencer
    if not por_vencer.empty:
        st.subheader("🟡 Préstamos por Vencer (Próximos 7 días)")
        
        st.dataframe(
            por_vencer[['elemento_codigo', 'elemento_nombre', 'hermano_nombre', 'fecha_vencimiento', 'dias_restantes']],
            column_config={
                'elemento_codigo': 'Código',
                'elemento_nombre': 'Elemento',
                'hermano_nombre': 'Hermano',
                'fecha_vencimiento': 'Fecha Vencimiento',
                'dias_restantes': 'Días Restantes'
            },
            use_container_width=True
        )
    
    # Información de contacto para seguimiento
    if not vencidos.empty or not por_vencer.empty:
        st.subheader("📞 Información de Contacto para Seguimiento")
        
        # Combinar vencidos y por vencer
        alertas = pd.concat([vencidos, por_vencer])
        
        contactos = []
        for _, prestamo in alertas.iterrows():
            hermano = df_hermanos[df_hermanos['id'] == prestamo['hermano_id']].iloc[0]
            contactos.append({
                'hermano': hermano['nombre_completo'],
                'telefono': hermano['telefono'] or 'No registrado',
                'email': hermano['email'] or 'No registrado',
                'elemento': f"{prestamo['elemento_codigo']} - {prestamo['elemento_nombre']}",
                'vencimiento': prestamo['fecha_vencimiento'],
                'estado': "🔴 Vencido" if prestamo['dias_restantes'] < 0 else "🟡 Por vencer"
            })
        
        contactos_df = pd.DataFrame(contactos)
        st.dataframe(contactos_df, use_container_width=True)

def reportes():
    """Módulo de reportes y estadísticas"""
    st.title("📊 Reportes y Estadísticas")
    
    df_logias, df_hermanos, df_depositos, df_elementos, df_prestamos = cargar_datos()
    
    tab1, tab2, tab3 = st.tabs(["📈 Estadísticas Generales", "🏛️ Por Logia", "📅 Temporales"])
    
    with tab1:
        st.subheader("📊 Estadísticas Generales del BEO")
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Elementos", len(df_elementos))
            st.metric("Elementos Disponibles", len(df_elementos[df_elementos['estado'] == 'disponible']))
        
        with col2:
            st.metric("Elementos Prestados", len(df_elementos[df_elementos['estado'] == 'prestado']))
            st.metric("En Mantenimiento", len(df_elementos[df_elementos['estado'] == 'mantenimiento']))
        
        with col3:
            st.metric("Total Hermanos", len(df_hermanos))
            st.metric("Total Logias", len(df_logias))
        
        with col4:
            prestamos_totales = len(df_prestamos)
            prestamos_activos = len(df_prestamos[df_prestamos['estado'] == 'activo'])
            st.metric("Total Préstamos", prestamos_totales)
            st.metric("Préstamos Activos", prestamos_activos)
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            if not df_elementos.empty:
                st.subheader("Estados de Elementos")
                estado_counts = df_elementos['estado'].value_counts()
                fig = px.pie(values=estado_counts.values, names=estado_counts.index)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if not df_elementos.empty:
                st.subheader("Elementos por Categoría")
                categoria_counts = df_elementos['categoria'].value_counts()
                fig = px.bar(x=categoria_counts.values, y=categoria_counts.index, orientation='h')
                st.plotly_chart(fig, use_container_width=True)
        
        # Eficiencia del sistema
        if prestamos_totales > 0:
            devueltos = len(df_prestamos[df_prestamos['estado'] == 'devuelto'])
            tasa_devolucion = (devueltos / prestamos_totales) * 100
            
            st.subheader("📈 Eficiencia del Sistema")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Tasa de Devolución", f"{tasa_devolucion:.1f}%")
            
            with col2:
                elementos_en_uso = (len(df_elementos[df_elementos['estado'] == 'prestado']) / len(df_elementos)) * 100
                st.metric("Elementos en Uso", f"{elementos_en_uso:.1f}%")
            
            with col3:
                if not df_prestamos.empty:
                    # Calcular préstamos promedio por mes
                    df_prestamos['fecha_prestamo'] = pd.to_datetime(df_prestamos['fecha_prestamo'])
                    prestamos_por_mes = df_prestamos.groupby(df_prestamos['fecha_prestamo'].dt.to_period('M')).size()
                    promedio_mensual = prestamos_por_mes.mean() if len(prestamos_por_mes) > 0 else 0
                    st.metric("Promedio Mensual", f"{promedio_mensual:.1f}")
    
    with tab2:
        st.subheader("🏛️ Estadísticas por Logia")
        
        if not df_logias.empty and not df_hermanos.empty:
            # Crear tabla de estadísticas por logia
            stats_logia = []
            
            for _, logia in df_logias.iterrows():
                hermanos_logia = df_hermanos[df_hermanos['logia_id'] == logia['id']]
                hermanos_ids = hermanos_logia['id'].tolist()
                
                prestamos_logia = df_prestamos[df_prestamos['hermano_id'].isin(hermanos_ids)]
                prestamos_activos_logia = prestamos_logia[prestamos_logia['estado'] == 'activo']
                
                stats_logia.append({
                    'logia': logia['nombre'],
                    'hermanos': len(hermanos_logia),
                    'prestamos_totales': len(prestamos_logia),
                    'prestamos_activos': len(prestamos_activos_logia),
                    'devueltos': len(prestamos_logia[prestamos_logia['estado'] == 'devuelto'])
                })
            
            stats_df = pd.DataFrame(stats_logia)
            
            if not stats_df.empty:
                # Tabla de estadísticas
                st.dataframe(
                    stats_df,
                    column_config={
                        'logia': 'Logia',
                        'hermanos': 'Hermanos',
                        'prestamos_totales': 'Total Préstamos',
                        'prestamos_activos': 'Préstamos Activos',
                        'devueltos': 'Devueltos'
                    },
                    use_container_width=True
                )
                
                # Gráfico de préstamos por logia
                fig = px.bar(stats_df, x='logia', y='prestamos_totales', 
                           title="Total de Préstamos por Logia")
                fig.update_xaxis(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos suficientes para mostrar estadísticas por logia")
    
    with tab3:
        st.subheader("📅 Estadísticas Temporales")
        
        if not df_prestamos.empty:
            df_prestamos['fecha_prestamo'] = pd.to_datetime(df_prestamos['fecha_prestamo'])
            
            # Préstamos por mes
            prestamos_por_mes = df_prestamos.groupby(df_prestamos['fecha_prestamo'].dt.to_period('M')).size()
            
            if len(prestamos_por_mes) > 0:
                st.subheader("📈 Préstamos por Mes")
                
                # Convertir a DataFrame para plotly
                prestamos_mes_df = prestamos_por_mes.reset_index()
                prestamos_mes_df['fecha_prestamo'] = prestamos_mes_df['fecha_prestamo'].astype(str)
                
                fig = px.line(prestamos_mes_df, x='fecha_prestamo', y=0,
                            title="Evolución de Préstamos por Mes")
                fig.update_xaxis(title="Mes")
                fig.update_yaxis(title="Cantidad de Préstamos")
                st.plotly_chart(fig, use_container_width=True)
                
                # Estadísticas de duración
                if 'fecha_devolucion' in df_prestamos.columns:
                    prestamos_devueltos = df_prestamos[df_prestamos['estado'] == 'devuelto'].copy()
                    
                    if not prestamos_devueltos.empty:
                        prestamos_devueltos['fecha_devolucion'] = pd.to_datetime(prestamos_devueltos['fecha_devolucion'])
                        prestamos_devueltos['duracion_real'] = (prestamos_devueltos['fecha_devolucion'] - prestamos_devueltos['fecha_prestamo']).dt.days
                        
                        st.subheader("📊 Análisis de Duración de Préstamos")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            duracion_promedio = prestamos_devueltos['duracion_real'].mean()
                            st.metric("Duración Promedio", f"{duracion_promedio:.1f} días")
                        
                        with col2:
                            duracion_mediana = prestamos_devueltos['duracion_real'].median()
                            st.metric("Duración Mediana", f"{duracion_mediana:.1f} días")
                        
                        with col3:
                            max_duracion = prestamos_devueltos['duracion_real'].max()
                            st.metric("Duración Máxima", f"{max_duracion} días")
                        
                        # Histograma de duraciones
                        fig = px.histogram(prestamos_devueltos, x='duracion_real', 
                                         title="Distribución de Duración de Préstamos",
                                         labels={'duracion_real': 'Días', 'count': 'Cantidad'})
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay préstamos registrados para mostrar estadísticas temporales")

def manual_usuario():
    """Manual de usuario del sistema"""
    st.title("📚 Manual de Usuario - Sistema BEO")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Introducción", "📋 Guías Rápidas", "🔧 Funcionalidades", "❓ FAQ"])
    
    with tab1:
        st.header("🏛️ Bienvenido al Sistema BEO")
        
        st.markdown("""
        El **Sistema BEO (Banco de Elementos Ortopédicos)** es una solución integral diseñada 
        específicamente para organizaciones masónicas filantrópicas que administran préstamos 
        de elementos ortopédicos a hermanos y sus familias.
        
        ### 🎯 Objetivos del Sistema
        - **Eficiencia**: Reducir 80% el tiempo de gestión de préstamos
        - **Transparencia**: Trazabilidad completa de todos los movimientos
        - **Control**: Eliminación de pérdidas y seguimiento efectivo
        - **Profesionalismo**: Imagen moderna y organizada
        
        ### 🔧 Características Principales
        - ✅ **Gestión Completa**: Logias, hermanos, depósitos y elementos
        - ✅ **Préstamos Seguros**: Con verificación de integridad automática
        - ✅ **Alertas Inteligentes**: Notificaciones de vencimientos
        - ✅ **Reportes Detallados**: Estadísticas en tiempo real
        - ✅ **Auditoría Completa**: Historial de todos los cambios
        
        ### 🏛️ Valores Masónicos Integrados
        - **Fraternidad**: Sistema diseñado para la ayuda mutua
        - **Beneficencia**: Facilitando la labor social organizada
        - **Organización**: Estructura que respeta la jerarquía masónica
        - **Transparencia**: Registro completo y trazabilidad total
        """)
    
    with tab2:
        st.header("📋 Guías Rápidas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚀 Inicio Rápido")
            st.markdown("""
            **Para empezar a usar el sistema:**
            
            1. **Registrar Logias** 🏛️
               - Ve a "Gestión de Logias" → "Agregar Logia"
               - Completa: Nombre, Venerable Maestro, Hospitalario
            
            2. **Registrar Depósitos** 🏢
               - Ve a "Gestión de Depósitos" → "Agregar Depósito"
               - Completa: Nombre, Ubicación, Responsable
            
            3. **Registrar Hermanos** 👥
               - Ve a "Gestión de Hermanos" → "Agregar Hermano"
               - Asigna a una logia existente
            
            4. **Agregar Elementos** 🦽
               - Ve a "Gestión de Elementos" → "Agregar"
               - Asigna a un depósito existente
            
            5. **¡Listo para préstamos!** 📋
            """)
        
        with col2:
            st.subheader("⚡ Flujo de Préstamo")
            st.markdown("""
            **Proceso simplificado:**
            
            1. **Crear Préstamo** 📋
               - "Formulario de Préstamo BEO"
               - Seleccionar hermano y elemento
               - Completar datos del beneficiario
            
            2. **Sistema Automático** 🤖
               - Elemento pasa a "prestado"
               - Se registra en historial
               - Se calcula fecha de vencimiento
            
            3. **Devolución Simple** 🔄
               - "Devolución Simple"
               - Seleccionar préstamo
               - Elegir depósito de destino
               - Elemento vuelve a "disponible"
            
            4. **Control Automático** ✅
               - Verificación de integridad
               - Alertas de vencimiento
               - Estadísticas actualizadas
            """)
    
    with tab3:
        st.header("🔧 Funcionalidades Detalladas")
        
        funcionalidad = st.selectbox("Seleccionar funcionalidad:", [
            "🏛️ Gestión de Logias",
            "👥 Gestión de Hermanos", 
            "🏢 Gestión de Depósitos",
            "🦽 Gestión de Elementos",
            "📋 Formulario de Préstamo",
            "🔄 Devolución Simple",
            "⚠️ Alertas de Vencimiento",
            "📊 Reportes y Estadísticas",
            "🔍 Verificación de Integridad"
        ])
        
        if funcionalidad == "🏛️ Gestión de Logias":
            st.markdown("""
            ### Gestión de Logias
            
            **Propósito**: Administrar las logias masónicas que participan en el BEO.
            
            **Funciones disponibles:**
            - **Ver Logias**: Lista completa con estadísticas de hermanos y préstamos
            - **Agregar Logia**: Registro de nueva logia con datos completos
            - **Editar Logia**: Modificación de datos existentes
            - **Desactivar Logia**: Para logias que ya no participan
            
            **Campos obligatorios:**
            - Nombre de la Logia
            - Venerable Maestro
            - Hospitalario
            
            **Campos opcionales:**
            - Teléfono, Email, Dirección
            """)
        
        elif funcionalidad == "👥 Gestión de Hermanos":
            st.markdown("""
            ### Gestión de Hermanos
            
            **Propósito**: Administrar la base de datos de hermanos masones.
            
            **Funciones disponibles:**
            - **Ver Hermanos**: Lista con filtros por logia y grado
            - **Agregar Hermano**: Registro completo con datos masónicos
            - **Editar Hermano**: Actualización de información
            - **Desactivar Hermano**: (Solo si no tiene préstamos activos)
            
            **Campos obligatorios:**
            - Nombre Completo
            - Documento de Identidad
            - Logia (debe existir previamente)
            - Grado Masónico
            
            **Grados disponibles:**
            - Aprendiz
            - Compañero  
            - Maestro Masón
            - Grado Superior
            """)
        
        elif funcionalidad == "🏢 Gestión de Depósitos":
            st.markdown("""
            ### Gestión de Depósitos
            
            **Propósito**: Administrar ubicaciones donde se almacenan los elementos.
            
            **Funciones disponibles:**
            - **Ver Depósitos**: Lista con estadísticas de elementos
            - **Agregar Depósito**: Registro de nueva ubicación
            - **Editar Depósito**: Modificación de datos
            - **Desactivar Depósito**: (Solo si no tiene elementos)
            
            **Campos obligatorios:**
            - Nombre del Depósito
            - Ubicación
            - Responsable
            
            **Estadísticas mostradas:**
            - Total de elementos
            - Elementos disponibles
            - Elementos prestados
            """)
        
        elif funcionalidad == "🦽 Gestión de Elementos":
            st.markdown("""
            ### Gestión de Elementos
            
            **Propósito**: Administrar el inventario completo de elementos ortopédicos.
            
            **Funciones disponibles:**
            - **Ver Elementos**: Inventario con filtros múltiples
            - **Agregar Elemento**: Registro con código único
            - **Editar Elemento**: Modificación de datos
            - **Cambio Manual de Estados**: Para correcciones administrativas
            
            **Estados posibles:**
            - **Disponible**: Listo para préstamo
            - **Prestado**: Actualmente en préstamo
            - **Mantenimiento**: Requiere reparación
            - **Dado de Baja**: Fuera de servicio
            
            **Categorías disponibles:**
            - Bastones, Sillas de Ruedas, Andadores
            - Camas Ortopédicas, Equipos de Rehabilitación
            - Muletas, Otros
            """)
        
        elif funcionalidad == "📋 Formulario de Préstamo":
            st.markdown("""
            ### Formulario de Préstamo BEO
            
            **Propósito**: Registrar nuevos préstamos de elementos ortopédicos.
            
            **Proceso paso a paso:**
            1. **Seleccionar Hermano**: De la lista de hermanos activos
            2. **Beneficiario**: Puede ser el hermano o un familiar
            3. **Elemento**: Solo elementos disponibles
            4. **Duración**: Días de préstamo (default: 30)
            5. **Entrega**: Dirección y responsable
            
            **Validaciones automáticas:**
            - Elemento debe estar disponible
            - Hermano debe estar activo
            - No puede haber préstamos duplicados del mismo elemento
            
            **Resultado:**
            - Elemento pasa automáticamente a "prestado"
            - Se registra en historial
            - Se calcula fecha de vencimiento
            """)
        
        elif funcionalidad == "🔄 Devolución Simple":
            st.markdown("""
            ### Devolución Simple
            
            **Propósito**: Procesar devoluciones de elementos de forma rápida y segura.
            
            **Características:**
            - **Lista automática**: Solo préstamos activos
            - **Estados visuales**: Vigente, Por vencer, Vencido
            - **Información completa**: Elemento, hermano, fechas
            
            **Proceso:**
            1. Seleccionar préstamo de la lista
            2. Indicar responsable de recepción
            3. Elegir depósito de destino
            4. Evaluar estado del elemento
            5. Agregar observaciones
            
            **Resultado automático:**
            - Préstamo marcado como "devuelto"
            - Elemento actualizado a estado seleccionado
            - Registro en historial de auditoría
            """)
        
        elif funcionalidad == "⚠️ Alertas de Vencimiento":
            st.markdown("""
            ### Alertas de Vencimiento
            
            **Propósito**: Monitorear préstamos próximos a vencer y vencidos.
            
            **Clasificaciones:**
            - **🔴 Vencidos**: Préstamos que superaron la fecha límite
            - **🟡 Por Vencer**: Próximos 7 días
            - **🟢 Vigentes**: Dentro del plazo normal
            
            **Información de contacto:**
            - Datos del hermano responsable
            - Teléfono y email para seguimiento
            - Detalles del elemento prestado
            
            **Uso recomendado:**
            - Revisión diaria de alertas
            - Contacto proactivo con hermanos
            - Seguimiento de elementos vencidos
            """)
        
        elif funcionalidad == "📊 Reportes y Estadísticas":
            st.markdown("""
            ### Reportes y Estadísticas
            
            **Propósito**: Análisis completo del funcionamiento del BEO.
            
            **Estadísticas Generales:**
            - Métricas de elementos y préstamos
            - Gráficos de distribución
            - Indicadores de eficiencia
            
            **Por Logia:**
            - Comparativo entre logias
            - Actividad de préstamos
            - Tasas de devolución
            
            **Temporales:**
            - Evolución mensual
            - Análisis de duración
            - Tendencias de uso
            
            **Beneficios:**
            - Toma de decisiones informada
            - Identificación de patrones
            - Planificación de recursos
            """)
        
        elif funcionalidad == "🔍 Verificación de Integridad":
            st.markdown("""
            ### Verificación de Integridad
            
            **Propósito**: Mantener la consistencia de datos en el sistema.
            
            **Verificaciones automáticas:**
            - Elementos prestados = Préstamos activos
            - No hay elementos "huérfanos"
            - Estados consistentes en toda la BD
            
            **Detección de problemas:**
            - Elementos prestados sin préstamo activo
            - Préstamos activos con elemento disponible
            - Inconsistencias en conteos
            
            **Corrección automática:**
            - Un clic para solucionar problemas
            - Backup automático antes de cambios
            - Registro de todas las correcciones
            
            **Cuándo usar:**
            - Si hay datos inconsistentes
            - Después de migraciones
            - Verificación periódica preventiva
            """)
    
    with tab4:
        st.header("❓ Preguntas Frecuentes (FAQ)")
        
        faq_items = [
            {
                "pregunta": "¿Qué hacer si aparece 'No hay préstamos' pero el dashboard muestra préstamos activos?",
                "respuesta": """
                Este era un problema común en versiones anteriores que **ya está solucionado** en esta versión corregida.
                
                **Si aún ocurre:**
                1. Ve a "🔍 Verificar Integridad"
                2. Haz clic en "🔧 Corregir Automáticamente"
                3. El sistema sincronizará automáticamente los datos
                
                **Prevención:** El nuevo sistema tiene triggers automáticos que mantienen la consistencia.
                """
            },
            {
                "pregunta": "¿Cómo registrar un préstamo para un familiar?",
                "respuesta": """
                **Proceso:**
                1. Ve a "📋 Formulario de Préstamo BEO"
                2. Selecciona el hermano solicitante
                3. En "Beneficiario" elige "familiar"
                4. Completa nombre del familiar y parentesco
                5. Continúa normalmente con el resto del formulario
                
                **Nota:** El hermano sigue siendo responsable del préstamo.
                """
            },
            {
                "pregunta": "¿Un elemento puede estar en préstamo múltiple?",
                "respuesta": """
                **No.** El sistema previene automáticamente préstamos duplicados del mismo elemento.
                
                **Si intentas prestar un elemento ya prestado:**
                - El sistema mostrará error
                - No permitirá completar el préstamo
                - Debes primero procesar la devolución del préstamo actual
                """
            },
            {
                "pregunta": "¿Cómo devolver un elemento a un depósito diferente?",
                "respuesta": """
                **En la devolución:**
                1. Ve a "🔄 Devolución Simple"
                2. Selecciona el préstamo a devolver
                3. En "Depósito de devolución" elige el depósito destino
                4. Completa el proceso normalmente
                
                **El elemento quedará en el nuevo depósito seleccionado.**
                """
            },
            {
                "pregunta": "¿Qué hacer si un elemento se daña durante el préstamo?",
                "respuesta": """
                **Durante la devolución:**
                1. En "Estado del elemento" selecciona "mantenimiento"
                2. Agrega observaciones sobre el daño
                3. Procesa la devolución normalmente
                
                **Resultado:**
                - El elemento queda marcado como "mantenimiento"
                - No aparecerá disponible para nuevos préstamos
                - Cuando se repare, cambia manualmente el estado a "disponible"
                """
            },
            {
                "pregunta": "¿Cómo extender la duración de un préstamo?",
                "respuesta": """
                **Proceso:**
                1. Procesa la devolución normal del elemento
                2. Inmediatamente crea un nuevo préstamo
                3. O usa "🔧 Cambio Manual de Estados" si es necesario
                
                **Nota:** En futuras versiones se agregará extensión directa de préstamos.
                """
            },
            {
                "pregunta": "¿Puedo eliminar elementos, hermanos o logias?",
                "respuesta": """
                **El sistema usa "desactivación" en lugar de eliminación** para mantener la integridad histórica.
                
                **Limitaciones:**
                - No puedes desactivar hermanos con préstamos activos
                - No puedes desactivar depósitos con elementos asignados
                - No puedes desactivar logias con hermanos activos
                
                **Primero debes resolver las dependencias.**
                """
            },
            {
                "pregunta": "¿Cómo hacer backup de los datos?",
                "respuesta": """
                **Backup manual:**
                1. Localiza el archivo "beo_sistema.db" 
                2. Cópialo a una ubicación segura
                3. Renómbralo con fecha (ej: beo_sistema_backup_20250626.db)
                
                **Backup automático:**
                - El script de migración crea backups automáticamente
                - Cada corrección de integridad hace backup preventivo
                """
            },
            {
                "pregunta": "¿El sistema funciona offline?",
                "respuesta": """
                **Sí, completamente offline.**
                
                **Características:**
                - Base de datos local SQLite
                - No requiere internet para funcionar
                - Todos los datos se almacenan localmente
                
                **Para acceso remoto:** Puedes deployar en Streamlit Cloud o similar para acceso web.
                """
            },
            {
                "pregunta": "¿Cómo interpretar las estadísticas del dashboard?",
                "respuesta": """
                **Métricas principales:**
                - **Elementos Disponibles**: Listos para préstamo
                - **Elementos Prestados**: Actualmente en préstamo
                - **Préstamos Activos**: Debe coincidir con elementos prestados
                
                **Estados de alerta:**
                - ✅ Verde: Consistencia verificada
                - ❌ Rojo: Inconsistencia detectada (usar corrección automática)
                
                **Gráficos:** Muestran distribución y tendencias para toma de decisiones.
                """
            }
        ]
        
        for i, item in enumerate(faq_items):
            with st.expander(f"❓ {item['pregunta']}"):
                st.markdown(item['respuesta'])

def main():
    """Función principal del sistema BEO completo"""
    if not autenticar_usuario():
        return
    
    # Sidebar
    st.sidebar.title("🏛️ Sistema BEO")
    st.sidebar.write(f"👤 Usuario: {st.session_state.get('usuario', 'Anónimo')}")
    
    # Verificación rápida de integridad para mostrar en sidebar
    try:
        integridad = db.verificar_integridad()
        if integridad['inconsistencias']:
            st.sidebar.error(f"⚠️ {len(integridad['inconsistencias'])} inconsistencias detectadas")
            if st.sidebar.button("🔧 Corregir Ahora"):
                db.corregir_inconsistencias()
                st.rerun()
        else:
            st.sidebar.success("✅ Sistema íntegro")
    except:
        st.sidebar.warning("⚠️ Error verificando integridad")
    
    # Menú principal
    pagina = st.sidebar.selectbox("Seleccionar sección:", [
        "📊 Dashboard",
        "🏛️ Gestión de Logias",
        "👨‍🤝‍👨 Gestión de Hermanos", 
        "🏢 Gestión de Depósitos",
        "🦽 Gestión de Elementos",
        "📋 Formulario de Préstamo BEO",
        "🔄 Devolución Simple", 
        "⚠️ Alertas de Vencimiento",
        "📊 Reportes y Estadísticas",
        "🔍 Verificar Integridad",
        "📚 Manual de Usuario"
    ])
    
    # Navegación
    if pagina == "📊 Dashboard":
        dashboard()
    elif pagina == "🏛️ Gestión de Logias":
        gestion_logias()
    elif pagina == "👨‍🤝‍👨 Gestión de Hermanos":
        gestion_hermanos()
    elif pagina == "🏢 Gestión de Depósitos":
        gestion_depositos()
    elif pagina == "🦽 Gestión de Elementos":
        gestion_elementos()
    elif pagina == "📋 Formulario de Préstamo BEO":
        formulario_prestamo()
    elif pagina == "🔄 Devolución Simple":
        devolucion_simple()
    elif pagina == "⚠️ Alertas de Vencimiento":
        alertas_vencimiento()
    elif pagina == "📊 Reportes y Estadísticas":
        reportes()
    elif pagina == "🔍 Verificar Integridad":
        st.title("🔍 Verificación de Integridad del Sistema")
        
        integridad = db.verificar_integridad()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Elementos Prestados", integridad['elementos_prestados'])
        with col2:
            st.metric("Préstamos Activos", integridad['prestamos_activos'])
        
        if integridad['inconsistencias']:
            st.error("❌ Inconsistencias detectadas:")
            for inc in integridad['inconsistencias']:
                st.write(f"- **{inc['tipo']}**: {inc['descripcion']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔧 Corregir Automáticamente"):
                    resultado = db.corregir_inconsistencias()
                    st.success(f"✅ Correcciones aplicadas: {resultado}")
                    st.rerun()
            
            with col2:
                if st.button("🔄 Verificar Nuevamente"):
                    st.rerun()
            
            # Mostrar detalles de inconsistencias
            if integridad['elementos_huerfanos']:
                with st.expander("🔍 Elementos Huérfanos Detectados"):
                    for elemento in integridad['elementos_huerfanos']:
                        st.write(f"- **{elemento[1]}** ({elemento[2]})")
            
            if integridad['prestamos_inconsistentes']:
                with st.expander("🔍 Préstamos Inconsistentes Detectados"):
                    for prestamo in integridad['prestamos_inconsistentes']:
                        st.write(f"- **Préstamo ID {prestamo[0]}**: {prestamo[2]} ({prestamo[3]}) - Estado: {prestamo[4]}")
        else:
            st.success("✅ No se detectaron inconsistencias")
            st.info("🎉 El sistema está funcionando correctamente")
            
            # Mostrar estadísticas adicionales
            with st.expander("📊 Estadísticas del Sistema"):
                df_logias, df_hermanos, df_depositos, df_elementos, df_prestamos = cargar_datos()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Logias", len(df_logias))
                    st.metric("Total Hermanos", len(df_hermanos))
                
                with col2:
                    st.metric("Total Depósitos", len(df_depositos))
                    st.metric("Total Elementos", len(df_elementos))
                
                with col3:
                    st.metric("Total Préstamos", len(df_prestamos))
                    prestamos_activos = len(df_prestamos[df_prestamos['estado'] == 'activo'])
                    st.metric("Préstamos Activos", prestamos_activos)
    
    elif pagina == "📚 Manual de Usuario":
        manual_usuario()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Sistema BEO v2.0 Completo**")
    st.sidebar.markdown("*Gestión Integral de Inventario Ortopédico*")
    st.sidebar.markdown("*Desarrollado para organizaciones masónicas filantrópicas*")
    
    # Información adicional en sidebar
    with st.sidebar.expander("ℹ️ Información del Sistema"):
        st.write("**Versión:** 2.0 Corregida")
        st.write("**Base de Datos:** SQLite")
        st.write("**Integridad:** Verificación automática")
        st.write("**Backup:** Automático en cambios")
        st.write("**Soporte:** Manual integrado")
    
    # Botón de cerrar sesión
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

if __name__ == "__main__":
    main()
