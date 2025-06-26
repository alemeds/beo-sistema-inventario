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
    page_title="BEO - Sistema de Inventario Corregido",
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
        """Inicializar base de datos con estructura corregida"""
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
    st.title("📊 Dashboard BEO - Sistema Corregido")
    
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
            fig = px.bar(x=prestamos_logia.index, y=prestamos_logia.values,
                        title="Préstamos Activos por Logia")
            st.plotly_chart(fig, use_container_width=True)
    
    # Debug mejorado
    with st.expander("🔍 Información de Debug Detallada"):
        st.write("**Conteos Directos:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("📦 **Elementos por Estado:**")
            if not df_elementos.empty:
                for estado in df_elementos['estado'].unique():
                    count = len(df_elementos[df_elementos['estado'] == estado])
                    st.write(f"- {estado}: {count}")
        
        with col2:
            st.write("📋 **Préstamos por Estado:**")
            if not df_prestamos.empty:
                for estado in df_prestamos['estado'].unique():
                    count = len(df_prestamos[df_prestamos['estado'] == estado])
                    st.write(f"- {estado}: {count}")
        
        # Mostrar elementos prestados
        if elementos_prestados > 0:
            st.write("**Elementos Actualmente Prestados:**")
            elementos_prestados_df = df_elementos[df_elementos['estado'] == 'prestado'][['codigo', 'nombre', 'categoria']]
            st.dataframe(elementos_prestados_df)
        
        # Mostrar préstamos activos
        if prestamos_activos > 0:
            st.write("**Préstamos Activos:**")
            prestamos_activos_df = df_prestamos[df_prestamos['estado'] == 'activo'][['elemento_codigo', 'elemento_nombre', 'hermano_nombre', 'fecha_prestamo', 'fecha_vencimiento']]
            st.dataframe(prestamos_activos_df)

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
    prestamos_display = prestamos_activos[['elemento_codigo', 'elemento_nombre', 'hermano_nombre', 'fecha_prestamo', 'fecha_vencimiento']].copy()
    prestamos_display.columns = ['Código', 'Elemento', 'Hermano', 'Fecha Préstamo', 'Fecha Vencimiento']
    st.dataframe(prestamos_display, use_container_width=True)
    
    # Formulario de devolución
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
        
        with col2:
            # Información adicional
            responsable_recepcion = st.text_input("Responsable de recepción")
            observaciones = st.text_area("Observaciones de devolución")
        
        submitted = st.form_submit_button("🔄 Procesar Devolución")
        
        if submitted and prestamo_seleccionado:
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
                    
                    # El trigger se encargará de actualizar el estado del elemento
                    conn.commit()
                    
                    st.success("✅ Devolución procesada correctamente")
                    st.balloons()
                    
                    # Recargar página
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error al procesar devolución: {e}")
                logger.error(f"Error en devolución: {e}")

def gestión_elementos():
    """Gestión de elementos mejorada"""
    st.title("🦽 Gestión de Elementos")
    
    tab1, tab2, tab3 = st.tabs(["📋 Ver Elementos", "➕ Agregar", "🔧 Mantenimiento"])
    
    df_logias, df_hermanos, df_depositos, df_elementos, df_prestamos = cargar_datos()
    
    with tab1:
        st.subheader("📦 Inventario de Elementos")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_estado = st.selectbox("Filtrar por estado:", 
                                       ["Todos"] + list(df_elementos['estado'].unique()))
        with col2:
            filtro_categoria = st.selectbox("Filtrar por categoría:", 
                                          ["Todas"] + list(df_elementos['categoria'].unique()))
        with col3:
            filtro_deposito = st.selectbox("Filtrar por depósito:", 
                                         ["Todos"] + list(df_elementos['deposito_nombre'].dropna().unique()))
        
        # Aplicar filtros
        df_filtrado = df_elementos.copy()
        if filtro_estado != "Todos":
            df_filtrado = df_filtrado[df_filtrado['estado'] == filtro_estado]
        if filtro_categoria != "Todas":
            df_filtrado = df_filtrado[df_filtrado['categoria'] == filtro_categoria]
        if filtro_deposito != "Todos":
            df_filtrado = df_filtrado[df_filtrado['deposito_nombre'] == filtro_deposito]
        
        # Mostrar elementos
        if not df_filtrado.empty:
            st.dataframe(df_filtrado[['codigo', 'nombre', 'categoria', 'marca', 'modelo', 'estado', 'deposito_nombre']], 
                        use_container_width=True)
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
            
            with col2:
                deposito_id = st.selectbox("Depósito", 
                                         options=df_depositos['id'].tolist(),
                                         format_func=lambda x: df_depositos[df_depositos['id'] == x]['nombre'].iloc[0] if not df_depositos.empty else "")
                precio_compra = st.number_input("Precio de compra", min_value=0.0, step=100.0)
                fecha_compra = st.date_input("Fecha de compra")
                descripcion = st.text_area("Descripción")
                observaciones = st.text_area("Observaciones")
            
            submitted = st.form_submit_button("💾 Guardar Elemento")
            
            if submitted:
                if codigo and nombre and categoria:
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
        st.subheader("🔧 Cambio Manual de Estados")
        st.warning("⚠️ Use esta función solo para correcciones administrativas")
        
        if not df_elementos.empty:
            elemento_seleccionado = st.selectbox("Seleccionar elemento:",
                                                options=df_elementos['id'].tolist(),
                                                format_func=lambda x: f"{df_elementos[df_elementos['id'] == x]['codigo'].iloc[0]} - {df_elementos[df_elementos['id'] == x]['nombre'].iloc[0]} (Estado: {df_elementos[df_elementos['id'] == x]['estado'].iloc[0]})")
            
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

def main():
    """Función principal"""
    if not autenticar_usuario():
        return
    
    # Sidebar
    st.sidebar.title("🏛️ BEO Sistema")
    st.sidebar.write(f"👤 Usuario: {st.session_state.get('usuario', 'Anónimo')}")
    
    # Menú principal
    pagina = st.sidebar.selectbox("Seleccionar sección:", [
        "📊 Dashboard",
        "🔄 Devolución Simple", 
        "🦽 Gestión de Elementos",
        "🔍 Verificar Integridad"
    ])
    
    # Navegación
    if pagina == "📊 Dashboard":
        dashboard()
    elif pagina == "🔄 Devolución Simple":
        devolucion_simple()
    elif pagina == "🦽 Gestión de Elementos":
        gestión_elementos()
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
            
            if st.button("🔧 Corregir Automáticamente"):
                resultado = db.corregir_inconsistencias()
                st.success(f"✅ Correcciones: {resultado}")
                st.rerun()
        else:
            st.success("✅ No se detectaron inconsistencias")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Sistema BEO v2.0 Corregido**")
    st.sidebar.markdown("*Gestión de Inventario Ortopédico*")

if __name__ == "__main__":
    main()
