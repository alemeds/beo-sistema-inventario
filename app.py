import streamlit as st
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
        conn = sqlite3.connect(self.db_path)
        # Habilitar foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def init_database(self):
        """Inicializa las tablas de la base de datos con mejor integridad"""
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
                activo BOOLEAN DEFAULT 1,
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
                activo BOOLEAN DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de categorías de elementos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                activo BOOLEAN DEFAULT 1
            )
        """)
        
        # Tabla de elementos ortopédicos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS elementos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                categoria_id INTEGER NOT NULL,
                deposito_id INTEGER NOT NULL,
                estado TEXT DEFAULT 'disponible' CHECK (estado IN ('disponible', 'prestado', 'mantenimiento', 'dado_de_baja')),
                descripcion TEXT,
                marca TEXT,
                modelo TEXT,
                numero_serie TEXT,
                fecha_ingreso DATE NOT NULL,
                observaciones TEXT,
                activo BOOLEAN DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                logia_id INTEGER NOT NULL,
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
                tipo TEXT NOT NULL CHECK (tipo IN ('hermano', 'familiar')),
                hermano_id INTEGER,
                hermano_responsable_id INTEGER,
                parentesco TEXT,
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
                elemento_id INTEGER NOT NULL,
                beneficiario_id INTEGER NOT NULL,
                hermano_solicitante_id INTEGER NOT NULL,
                duracion_dias INTEGER NOT NULL,
                fecha_devolucion_estimada DATE NOT NULL,
                fecha_devolucion_real DATE,
                estado TEXT DEFAULT 'activo' CHECK (estado IN ('activo', 'devuelto', 'vencido')),
                observaciones_prestamo TEXT,
                observaciones_devolucion TEXT,
                autorizado_por TEXT,
                entregado_por TEXT NOT NULL,
                recibido_por TEXT,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                elemento_id INTEGER NOT NULL,
                estado_anterior TEXT,
                estado_nuevo TEXT NOT NULL,
                razon TEXT,
                observaciones TEXT,
                responsable TEXT,
                fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (elemento_id) REFERENCES elementos (id)
            )
        """)
        
        # Insertar datos básicos si no existen
        self.insertar_datos_basicos(cursor)
        
        conn.commit()
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
            cursor.execute("INSERT OR IGNORE INTO categorias (nombre, descripcion) VALUES (?, ?)", 
                         (categoria, descripcion))
        
        # Depósito por defecto
        cursor.execute("INSERT OR IGNORE INTO depositos (nombre, direccion) VALUES (?, ?)", 
                      ("Depósito Principal", "Dirección no especificada"))

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
        st.caption("Sistema de Gestión del Banco de Elementos Ortopédicos")
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
    
    elif seccion == "🏛️ Gestión de Logias":
        st.markdown("""
        ## 🏛️ Gestión de Logias
        
        ### ¿Para qué sirve?
        Registrar y administrar las logias masónicas que participan en el programa BEO.
        
        ### 📝 Cómo Registrar una Nueva Logia
        
        1. **Ir a:** Menú Principal → Gestión de Logias
        2. **Completar los campos:**
           - **Nombre de la Logia*** (obligatorio)
           - **Número** de la logia
           - **Oriente** (ciudad/ubicación)
           - **Venerable Maestro** y su teléfono
           - **Hospitalario** y su teléfono
           - **Dirección** de la logia
        
        3. **Hacer clic en:** "Guardar Logia"
        
        ### 📋 Información Importante
        - El **Hospitalario** es clave para la gestión del BEO
        - Los **teléfonos** son importantes para coordinación
        - El **nombre** debe ser único en el sistema
        
        ### 💡 Consejos
        - Registrar primero las logias antes que los hermanos
        - Mantener actualizada la información de contacto
        - El Hospitalario suele ser el responsable del BEO en cada logia
        """)
    
    elif seccion == "👨‍🤝‍👨 Gestión de Hermanos":
        st.markdown("""
        ## 👨‍🤝‍👨 Gestión de Hermanos
        
        ### ¿Para qué sirve?
        Registrar hermanos masones que pueden solicitar préstamos del BEO.
        
        ### 📝 Cómo Registrar un Nuevo Hermano
        
        1. **Ir a:** Menú Principal → Gestión de Hermanos → "Nuevo Hermano"
        2. **Completar información básica:**
           - **Nombre Completo*** (obligatorio)
           - **Teléfono**
           - **Logia*** (seleccionar de la lista)
           - **Grado masónico** (Apr:., Comp:., M:.M:., etc.)
        
        3. **Completar información adicional:**
           - **Dirección**
           - **Email**
           - **Fecha de Iniciación**
           - **Observaciones**
        
        4. **Hacer clic en:** "✅ Guardar Hermano"
        
        ### 🎭 Grados Masónicos Disponibles
        - **Apr:.** - Aprendiz
        - **Comp:.** - Compañero  
        - **M:.M:.** - Maestro Masón
        - **Gr:. 4°** al **Gr:. 33°** - Grados superiores
        - **Otro** - Para grados especiales
        
        ### 📊 Ver Lista de Hermanos
        - **Ir a:** Gestión de Hermanos → "Lista de Hermanos"
        - Ver todos los hermanos activos registrados
        - Información incluye: nombre, teléfono, grado, logia
        
        ### 📚 Historial por Hermano
        - **Ir a:** Gestión de Hermanos → "📚 Historial por Hermano"
        - Ver todos los préstamos de cada hermano
        - Estadísticas de cumplimiento individual
        
        ### 💡 Consejos
        - Asegurarse de que la logia esté registrada primero
        - El teléfono es importante para contactar al hermano
        - Los hermanos inactivos no aparecen en listas de préstamos
        """)
    
    elif seccion == "🦽 Gestión de Elementos":
        st.markdown("""
        ## 🦽 Gestión de Elementos Ortopédicos
        
        ### ¿Para qué sirve?
        Administrar el inventario completo de elementos ortopédicos del BEO.
        
        ### 📝 Cómo Registrar un Nuevo Elemento
        
        1. **Ir a:** Menú Principal → Gestión de Elementos → "Nuevo Elemento"
        2. **Información básica:**
           - **Código del Elemento*** (único, ej: SR-001)
           - **Nombre del Elemento*** (ej: Silla de Ruedas Manual)
           - **Categoría*** (seleccionar de la lista)
           - **Depósito*** (donde se almacena)
        
        3. **Información detallada:**
           - **Descripción** (características específicas)
           - **Marca** y **Modelo**
           - **Número de Serie**
           - **Fecha de Ingreso**
           - **Observaciones**
        
        4. **Hacer clic en:** "🦽 Guardar Elemento"
        
        ### 📦 Categorías de Elementos
        - **Sillas de Ruedas** - Manuales y eléctricas
        - **Bastones** - Simples y ortopédicos
        - **Muletas** - Axilares y de antebrazo
        - **Andadores** - Con y sin ruedas
        - **Camas Ortopédicas** - Articuladas y colchones
        - **Equipos de Rehabilitación** - Diversos equipos
        - **Otros** - Elementos no categorizados
        
        ### 📊 Ver Inventario
        - **Ir a:** Gestión de Elementos → "Inventario"
        - **Filtrar por:** Categoría, Depósito, Estado
        - **Estados posibles:** Disponible, Prestado, Mantenimiento
        
        ### 📚 Historial por Elemento
        - **Ir a:** Gestión de Elementos → "📚 Historial por Elemento"
        - Ver por qué manos pasó cada elemento
        - Estadísticas de uso y frecuencia
        
        ### 🔧 Cambiar Estado de Elementos
        - **Ir a:** Gestión de Elementos → "🔧 Cambiar Estado"
        - **Buscar** el elemento por código o nombre
        - **Hacer clic** en "🔄 Cambiar Estado"
        - **Seleccionar** nuevo estado y razón del cambio
        - **Confirmar** el cambio
        
        ### 💡 Consejos para Códigos
        - Usar formato consistente: **SR-001** (Silla Ruedas)
        - **BA-001** (Bastón), **MU-001** (Muletas)
        - **AN-001** (Andador), **CA-001** (Cama)
        - Los códigos deben ser únicos en todo el sistema
        """)
    
    elif seccion == "📋 Sistema de Préstamos":
        st.markdown("""
        ## 📋 Sistema de Préstamos
        
        ### ¿Para qué sirve?
        Gestionar el ciclo completo de préstamos de elementos ortopédicos según el formulario oficial BEO.
        
        ### 📝 Cómo Registrar un Nuevo Préstamo
        
        1. **Ir a:** Menú Principal → Formulario de Préstamo → "Nuevo Préstamo"
        
        2. **Información General:**
           - **Fecha** del préstamo
           - **Duración:** Especificar en días o meses
           - El sistema calcula automáticamente la fecha de devolución
        
        3. **Hermano Solicitante:**
           - **Seleccionar** hermano de la lista
           - Se muestra automáticamente: logia, grado, hospitalario, venerable
        
        4. **Beneficiario del Préstamo:**
           - **Tipo:** Hermano o Familiar
           - **Si es Hermano:** Seleccionar de la lista
           - **Si es Familiar:** 
             - Especificar parentesco (Madre, Padre, Esposa/o, etc.)
             - Indicar de qué hermano es familiar
             - Completar nombre y teléfono
        
        5. **Información del Elemento:**
           - **Dirección de entrega**
           - **Elemento a prestar** (solo aparecen disponibles)
           - **Observaciones del préstamo**
           - **Autorizado por**
           - **Entregado por**
        
        6. **Hacer clic en:** "📋 Registrar Préstamo BEO"
        
        ### 📊 Monitorear Préstamos Activos
        - **Ir a:** Formulario de Préstamo → "Préstamos Activos"
        - **Estados visuales:**
          - 🟢 **Vigente** - Dentro del plazo
          - 🟡 **Por Vencer** - Próximo a vencer (7 días)
          - 🔴 **Vencido** - Pasado la fecha límite
        
        ### 💡 Consejos
        - Verificar que el elemento esté "disponible"
        - La duración típica es 90 días o 3 meses
        - Completar siempre las observaciones importantes
        - El hermano solicitante puede ser diferente al beneficiario
        """)
    
    elif seccion == "🔄 Devolución de Elementos":
        st.markdown("""
        ## 🔄 Devolución de Elementos
        
        ### ¿Para qué sirve?
        Registrar la devolución de elementos prestados de manera completa y organizada.
        
        ### 📝 Cómo Registrar una Devolución
        
        1. **Ir a:** Formulario de Préstamo → "🔄 Devolución"
        
        2. **Encontrar el Elemento:**
           - **Filtrar por estado:** Todos, Vigente, Por vencer, Vencido
           - **Buscar por código:** Ej: SR-001
           - **Buscar por beneficiario:** Nombre de quien tiene el elemento
        
        3. **Iniciar Devolución:**
           - **Hacer clic** en "🔄 DEVOLVER AHORA"
           - Se abre el formulario completo de devolución
        
        4. **Completar Información de Devolución:**
           - **Fecha de Devolución**
           - **Recibido por** (quien recibe el elemento)
           - **Depósito de Devolución** (a dónde va el elemento)
           - **Estado del Elemento:**
             - Bueno
             - Regular  
             - Necesita Mantenimiento
             - Dañado
           - **Observaciones** detalladas
        
        5. **Confirmar Devolución:**
           - **Revisar** la información mostrada
           - **Hacer clic** en "✅ CONFIRMAR DEVOLUCIÓN"
        
        ### 🏢 Selección de Depósito
        - Puedes elegir a qué depósito devolver cada elemento
        - No necesariamente debe ser el depósito original
        - Útil para redistribuir elementos según necesidades
        
        ### ⏰ Devoluciones Anticipadas
        - **SÍ puedes devolver** antes de la fecha límite
        - No hay restricciones de tiempo
        - Útil para elementos que ya no se necesitan
        
        ### 📚 Historial de Devoluciones
        - **Ir a:** Formulario de Préstamo → "Historial"
        - **Ver todas** las devoluciones realizadas
        - **Filtrar por fechas** y cumplimiento
        - **Estadísticas** de cumplimiento (a tiempo, con retraso, anticipadas)
        
        ### 💡 Consejos
        - Describir bien el estado del elemento al devolverlo
        - Si hay daños, usar estado "Necesita Mantenimiento"
        - Las devoluciones anticipadas son válidas y recomendadas
        - El historial ayuda a evaluar el cumplimiento por logia
        """)
    
    elif seccion == "🔧 Cambio de Estados":
        st.markdown("""
        ## 🔧 Cambio Manual de Estados
        
        ### ¿Para qué sirve?
        Cambiar manualmente el estado de elementos para correcciones, mantenimiento o casos especiales.
        
        ### 📝 Cómo Cambiar el Estado de un Elemento
        
        1. **Ir a:** Gestión de Elementos → "🔧 Cambiar Estado"
        
        2. **Encontrar el Elemento:**
           - **Buscar por código:** Ej: SR-001
           - **Buscar por nombre:** Ej: Silla de ruedas
        
        3. **Iniciar Cambio:**
           - **Hacer clic** en "🔄 Cambiar Estado"
           - Se muestra advertencia si está prestado
        
        4. **Completar Cambio:**
           - **Nuevo Estado:**
             - ✅ **Disponible** - Puede ser prestado
             - 📋 **Prestado** - Marcado como prestado
             - 🔧 **Mantenimiento** - Necesita reparación
           - **Razón del Cambio:**
             - Corrección administrativa
             - Devolución no registrada
             - Elemento perdido/dañado
             - Mantenimiento preventivo
             - Error en registro anterior
             - Otro (personalizable)
           - **Observaciones** detalladas
           - **Responsable** que autoriza el cambio
        
        5. **Confirmar Cambio:**
           - **Revisar** el resumen del cambio
           - **Hacer clic** en "✅ CONFIRMAR CAMBIO"
        
        ### ⚠️ Casos Especiales
        
        #### Elementos Prestados
        - **Advertencia automática** si tiene préstamo activo
        - **Cierre automático** del préstamo al cambiar estado
        - **Recomendación** de usar devolución formal cuando sea apropiado
        
        #### Registro de Cambios
        - **Historial automático** en base de datos
        - **Fecha y hora** del cambio
        - **Responsable** que autorizó
        - **Razón detallada** del cambio
        
        ### 💡 Consejos
        - Usar esta función solo para casos especiales
        - Para devoluciones normales, usar "🔄 Devolución"
        - Siempre especificar la razón del cambio
        - El historial queda registrado permanentemente
        """)
    
    elif seccion == "📊 Dashboard y Reportes":
        st.markdown("""
        ## 📊 Dashboard y Reportes
        
        ### ¿Para qué sirve?
        Obtener una vista general del estado del BEO con estadísticas y gráficos.
        
        ### 📈 Métricas Principales
        - **🦽 Total Elementos** - Inventario completo
        - **✅ Disponibles** - Elementos listos para préstamo  
        - **📋 Préstamos Activos** - Elementos actualmente prestados
        - **👨‍🤝‍👨 Hermanos Activos** - Hermanos registrados
        
        ### 📊 Gráficos Disponibles
        
        #### Elementos por Categoría
        - **Gráfico de pastel** mostrando distribución del inventario
        - Útil para ver qué tipo de elementos son más comunes
        
        #### Estado de Elementos
        - **Gráfico de barras** con estados actuales
        - Colores: Verde (disponible), Naranja (prestado), Rojo (mantenimiento)
        
        #### Préstamos por Logia
        - **Gráfico de barras** mostrando préstamos activos por logia
        - Identifica qué logias usan más el BEO
        
        ### 🚨 Alertas de Vencimiento
        - **Lista automática** de préstamos próximos a vencer o vencidos
        - **Información de contacto** para realizar seguimiento
        - **Estado de alerta** claramente identificado
        
        ### 📍 Ubicaciones Actuales
        - **Dónde está cada elemento** prestado
        - **Direcciones completas** de beneficiarios
        - **Información de contacto** para seguimiento
        
        ### 📋 Información Mostrada en Alertas
        - **Código y nombre** del elemento
        - **Beneficiario** y teléfono de contacto
        - **Hermano solicitante** y su logia
        - **Fecha de devolución estimada**
        - **Estado de alerta** (Por vencer / Vencido)
        
        ### 💡 Uso del Dashboard
        - **Revisar diariamente** las alertas de vencimiento
        - **Monitorear** el uso por logia para planificación
        - **Identificar** necesidades de más elementos en ciertas categorías
        - **Evaluar** la efectividad del programa BEO
        """)
    
    elif seccion == "❓ Preguntas Frecuentes":
        st.markdown("""
        ## ❓ Preguntas Frecuentes
        
        ### 🔐 Acceso y Seguridad
        
        **P: ¿Cuáles son las credenciales de acceso?**
        R: Usuario: `beo_admin`, Contraseña: `beo2025`
        
        **P: ¿Se pueden cambiar las credenciales?**
        R: Sí, contactar al administrador del sistema para modificarlas.
        
        **P: ¿El sistema guarda automáticamente?**
        R: Sí, todos los cambios se guardan automáticamente al confirmar.
        
        ### 📋 Gestión de Préstamos
        
        **P: ¿Puede un hermano solicitar para un familiar?**
        R: Sí, al crear el préstamo selecciona "Familiar" y especifica el parentesco.
        
        **P: ¿Puedo devolver un elemento antes de la fecha límite?**
        R: Sí, puedes devolver elementos en cualquier momento desde "🔄 Devolución".
        
        **P: ¿Qué pasa si no devuelven a tiempo?**
        R: El sistema marca como "VENCIDO" y aparece en alertas del Dashboard.
        
        **P: ¿Puedo cambiar la duración de un préstamo ya registrado?**
        R: No directamente, pero puedes registrar la devolución y crear un nuevo préstamo.
        
        ### 🦽 Gestión de Elementos
        
        **P: ¿Cómo marco un elemento como dañado?**
        R: Ve a "🔧 Cambiar Estado" y cambia a "Mantenimiento".
        
        **P: ¿Puedo mover un elemento a otro depósito?**
        R: Sí, durante la devolución puedes elegir el depósito de destino.
        
        **P: ¿Qué pasa si registro un código duplicado?**
        R: El sistema mostrará error. Cada código debe ser único.
        
        ### 📊 Reportes y Seguimiento
        
        **P: ¿Cómo veo qué logia usa más el BEO?**
        R: En el Dashboard, revisa el gráfico "Préstamos por Logia".
        
        **P: ¿Puedo ver el historial de un elemento específico?**
        R: Sí, ve a Gestión de Elementos → "📚 Historial por Elemento".
        
        **P: ¿Puedo ver el historial de un hermano específico?**
        R: Sí, ve a Gestión de Hermanos → "📚 Historial por Hermano".
        
        ### 🔧 Problemas Técnicos
        
        **P: ¿Qué hago si el sistema no carga?**
        R: Verificar conexión a internet y recargar la página.
        
        **P: ¿Los datos se pierden al cerrar la aplicación?**
        R: No, todos los datos se guardan en la base de datos permanentemente.
        
        **P: ¿Puedo usar el sistema desde el celular?**
        R: Sí, el sistema es responsive y funciona en dispositivos móviles.
        
        ### 🏛️ Aspectos Masónicos
        
        **P: ¿Es obligatorio registrar la logia primero?**
        R: Sí, debes registrar la logia antes de registrar hermanos.
        
        **P: ¿Qué información de la logia es más importante?**
        R: El Hospitalario y su teléfono, ya que suele gestionar el BEO.
        
        **P: ¿Puedo registrar hermanos de logias no masónicas?**
        R: El sistema está diseñado para logias masónicas, pero se puede adaptar.
        
        ### 📞 Soporte
        
        **P: ¿A quién contacto para soporte técnico?**
        R: Contactar al administrador del sistema o al responsable técnico del BEO.
        
        **P: ¿Se pueden agregar nuevas funcionalidades?**
        R: Sí, el sistema puede expandirse según las necesidades de la organización.
        
        **P: ¿Hay backup de los datos?**
        R: El archivo de base de datos (.db) se puede respaldar regularmente.
        """)

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
                    except Exception as e:
                        st.error(f"Error al guardar logia: {e}")
                else:
                    st.error("El nombre de la logia es obligatorio")
    
    with col2:
        st.subheader("Logias Registradas")
        try:
            conn = db.get_connection()
            logias_df = pd.read_sql_query("""
                SELECT nombre, numero, oriente, venerable_maestro, hospitalario
                FROM logias 
                WHERE activo = 1
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
    
    tab1, tab2, tab3 = st.tabs(["Nuevo Hermano", "Lista de Hermanos", "📚 Historial por Hermano"])
    
    with tab1:
        try:
            conn = db.get_connection()
            logias_df = pd.read_sql_query("SELECT id, nombre, numero FROM logias WHERE activo = 1 ORDER BY numero, nombre", conn)
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
                WHERE h.activo = 1
                ORDER BY h.nombre
            """, conn)
            conn.close()
            
            if not hermanos_df.empty:
                st.dataframe(hermanos_df, use_container_width=True)
            else:
                st.info("No hay hermanos registrados")
        except Exception as e:
            st.error(f"Error al cargar hermanos: {e}")
    
    with tab3:
        st.subheader("📚 Historial de Préstamos por Hermano")
        st.markdown("**Ver todos los préstamos históricos de un hermano específico**")
        
        try:
            conn = db.get_connection()
            hermanos_df = pd.read_sql_query("""
                SELECT h.id, h.nombre, l.nombre as logia
                FROM hermanos h
                LEFT JOIN logias l ON h.logia_id = l.id
                WHERE h.activo = 1
                ORDER BY h.nombre
            """, conn)
            
            if not hermanos_df.empty:
                hermano_id = st.selectbox(
                    "Seleccionar Hermano:",
                    options=hermanos_df['id'].tolist(),
                    format_func=lambda x: f"{hermanos_df[hermanos_df['id'] == x]['nombre'].iloc[0]} - {hermanos_df[hermanos_df['id'] == x]['logia'].iloc[0]}"
                )
                
                # Obtener historial completo del hermano
                historial_hermano = pd.read_sql_query("""
                    SELECT 
                        p.id,
                        e.codigo as codigo_elemento,
                        e.nombre as elemento,
                        b.nombre as beneficiario,
                        b.tipo as tipo_beneficiario,
                        p.fecha_prestamo,
                        p.fecha_devolucion_estimada,
                        p.fecha_devolucion_real,
                        p.estado,
                        CASE 
                            WHEN p.fecha_devolucion_real IS NULL AND DATE('now') > p.fecha_devolucion_estimada THEN 'VENCIDO'
                            WHEN p.fecha_devolucion_real IS NULL THEN 'ACTIVO'
                            WHEN p.fecha_devolucion_real <= p.fecha_devolucion_estimada THEN 'DEVUELTO A TIEMPO'
                            ELSE 'DEVUELTO CON RETRASO'
                        END as estado_cumplimiento,
                        CASE 
                            WHEN p.fecha_devolucion_real IS NOT NULL 
                            THEN CAST((JULIANDAY(p.fecha_devolucion_real) - JULIANDAY(p.fecha_devolucion_estimada)) AS INTEGER)
                            ELSE NULL
                        END as dias_diferencia,
                        p.observaciones_prestamo,
                        p.observaciones_devolucion
                    FROM prestamos p
                    JOIN elementos e ON p.elemento_id = e.id
                    JOIN beneficiarios b ON p.beneficiario_id = b.id
                    WHERE p.hermano_solicitante_id = ?
                    ORDER BY p.fecha_prestamo DESC
                """, conn, params=[hermano_id])
                
                if not historial_hermano.empty:
                    st.markdown(f"#### 📊 Resumen de {hermanos_df[hermanos_df['id'] == hermano_id]['nombre'].iloc[0]}")
                    
                    # Estadísticas del hermano
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        total_prestamos = len(historial_hermano)
                        st.metric("Total Préstamos", total_prestamos)
                    with col2:
                        activos = len(historial_hermano[historial_hermano['estado'] == 'activo'])
                        st.metric("Activos", activos)
                    with col3:
                        a_tiempo = len(historial_hermano[historial_hermano['estado_cumplimiento'] == 'DEVUELTO A TIEMPO'])
                        st.metric("Devueltos a Tiempo", a_tiempo)
                    with col4:
                        vencidos = len(historial_hermano[historial_hermano['estado_cumplimiento'].isin(['VENCIDO', 'DEVUELTO CON RETRASO'])])
                        st.metric("Vencidos/Retraso", vencidos)
                    
                    # Tabla detallada
                    st.markdown("#### 📋 Historial Detallado")
                    st.dataframe(historial_hermano, use_container_width=True)
                    
                    # Gráfico de cumplimiento
                    cumplimiento_counts = historial_hermano['estado_cumplimiento'].value_counts()
                    if len(cumplimiento_counts) > 0:
                        fig = px.pie(
                            values=cumplimiento_counts.values, 
                            names=cumplimiento_counts.index,
                            title="Distribución de Cumplimiento"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                else:
                    st.info("Este hermano no tiene préstamos registrados")
            
            else:
                st.warning("No hay hermanos registrados")
            
            conn.close()
        except Exception as e:
            st.error(f"Error al cargar historial: {e}")

def gestionar_elementos():
    """Gestión de elementos ortopédicos"""
    st.header("🦽 Gestión de Elementos Ortopédicos")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Nuevo Elemento", "Inventario", "🔧 Cambiar Estado", "📚 Historial por Elemento"])
    
    with tab1:
        try:
            conn = db.get_connection()
            depositos_df = pd.read_sql_query("SELECT id, nombre FROM depositos WHERE activo = 1", conn)
            categorias_df = pd.read_sql_query("SELECT id, nombre FROM categorias WHERE activo = 1", conn)
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
                            cursor.execute("""
                                INSERT INTO elementos 
                                (codigo, nombre, categoria_id, deposito_id, descripcion, marca, 
                                 modelo, numero_serie, fecha_ingreso, observaciones)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (codigo, nombre, categoria_id, deposito_id, descripcion, 
                                 marca, modelo, numero_serie, fecha_ingreso, observaciones))
                            
                            elemento_id = cursor.lastrowid
                            
                            # Registrar en historial de estados
                            cursor.execute("""
                                INSERT INTO historial_estados 
                                (elemento_id, estado_anterior, estado_nuevo, razon, responsable)
                                VALUES (?, ?, ?, ?, ?)
                            """, (elemento_id, None, 'disponible', 'Ingreso inicial', 'Sistema'))
                            
                            conn.commit()
                            conn.close()
                            st.success("✅ Elemento guardado exitosamente")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("❌ Ya existe un elemento con ese código")
                        except Exception as e:
                            st.error(f"❌ Error al guardar elemento: {e}")
                    else:
                        st.error("❌ Todos los campos marcados con * son obligatorios")
        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
    
    with tab2:
        st.subheader("📦 Inventario de Elementos")
        
        try:
            col1, col2, col3 = st.columns(3)
            
            conn = db.get_connection()
            
            with col1:
                categorias_df = pd.read_sql_query("SELECT id, nombre FROM categorias WHERE activo = 1", conn)
                categoria_filtro = st.selectbox(
                    "Filtrar por Categoría",
                    options=[None] + categorias_df['id'].tolist(),
                    format_func=lambda x: "Todas las categorías" if x is None else categorias_df[categorias_df['id'] == x]['nombre'].iloc[0]
                )
            
            with col2:
                depositos_df = pd.read_sql_query("SELECT id, nombre FROM depositos WHERE activo = 1", conn)
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
            
            # Query mejorado con ubicación actual de prestados
            query = """
                SELECT e.id, e.codigo, e.nombre, c.nombre as categoria, d.nombre as deposito, 
                       e.estado, e.marca, e.modelo,
                       CASE 
                           WHEN e.estado = 'prestado' THEN 
                               COALESCE((SELECT 'Prestado a: ' || b.nombre || ' (' || b.direccion || ')'
                                FROM prestamos p 
                                JOIN beneficiarios b ON p.beneficiario_id = b.id
                                WHERE p.elemento_id = e.id AND p.estado = 'activo'
                                LIMIT 1), 'En ' || d.nombre)
                           ELSE 'En ' || d.nombre
                       END as ubicacion_actual
                FROM elementos e
                JOIN categorias c ON e.categoria_id = c.id
                JOIN depositos d ON e.deposito_id = d.id
                WHERE e.activo = 1
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
        except Exception as e:
            st.error(f"Error al cargar inventario: {e}")
    
    with tab3:
        st.header("🔧 Cambiar Estado de Elementos")
        st.markdown("**Gestión manual de estados para casos especiales**")
        st.info("💡 Para devoluciones normales, usar 'Formulario de Préstamo' → 'Devolución'")
        
        try:
            conn = db.get_connection()
            
            # Filtros para buscar elementos
            col1, col2 = st.columns(2)
            with col1:
                busqueda = st.text_input("🔍 Buscar por código o nombre:")
            with col2:
                estado_actual = st.selectbox("Estado actual:", ["Todos", "disponible", "prestado", "mantenimiento"])
            
            # Query para buscar elementos
            query = """
                SELECT e.id, e.codigo, e.nombre, c.nombre as categoria, d.nombre as deposito, 
                       e.estado, e.marca, e.modelo
                FROM elementos e
                JOIN categorias c ON e.categoria_id = c.id
                JOIN depositos d ON e.deposito_id = d.id
                WHERE e.activo = 1
            """
            params = []
            
            if busqueda:
                query += " AND (e.codigo LIKE ? OR e.nombre LIKE ?)"
                params.extend([f"%{busqueda}%", f"%{busqueda}%"])
            
            if estado_actual != "Todos":
                query += " AND e.estado = ?"
                params.append(estado_actual)
            
            query += " ORDER BY e.codigo"
            
            elementos_encontrados = pd.read_sql_query(query, conn, params=params)
            
            if not elementos_encontrados.empty:
                st.markdown(f"#### Elementos encontrados: {len(elementos_encontrados)}")
                
                for idx, elemento in elementos_encontrados.iterrows():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**{elemento['codigo']}** - {elemento['nombre']}")
                        st.caption(f"Estado: {elemento['estado']} | Depósito: {elemento['deposito']}")
                    
                    with col2:
                        # Verificar si tiene préstamo activo
                        prestamo_activo = pd.read_sql_query("""
                            SELECT p.id, b.nombre as beneficiario
                            FROM prestamos p
                            JOIN beneficiarios b ON p.beneficiario_id = b.id
                            WHERE p.elemento_id = ? AND p.estado = 'activo'
                        """, conn, params=[elemento['id']])
                        
                        if not prestamo_activo.empty:
                            st.warning(f"⚠️ Prestado a: {prestamo_activo.iloc[0]['beneficiario']}")
                        else:
                            st.success("✅ Sin préstamos activos")
                    
                    with col3:
                        if st.button(f"🔄 Cambiar Estado", key=f"cambiar_{elemento['id']}"):
                            st.session_state[f"cambiar_estado_{elemento['id']}"] = True
                    
                    # Formulario de cambio de estado
                    if st.session_state.get(f"cambiar_estado_{elemento['id']}", False):
                        with st.expander(f"Cambiar Estado: {elemento['codigo']}", expanded=True):
                            with st.form(f"cambio_estado_{elemento['id']}"):
                                col_form1, col_form2 = st.columns(2)
                                
                                with col_form1:
                                    nuevo_estado = st.selectbox(
                                        "Nuevo Estado:",
                                        options=["disponible", "prestado", "mantenimiento"],
                                        index=["disponible", "prestado", "mantenimiento"].index(elemento['estado'])
                                    )
                                    
                                    razon = st.selectbox(
                                        "Razón del cambio:",
                                        options=[
                                            "Corrección administrativa",
                                            "Devolución no registrada",
                                            "Elemento perdido/dañado",
                                            "Mantenimiento preventivo",
                                            "Error en registro anterior",
                                            "Otro"
                                        ]
                                    )
                                
                                with col_form2:
                                    if razon == "Otro":
                                        razon_personalizada = st.text_input("Especificar razón:")
                                        razon_final = razon_personalizada if razon_personalizada else razon
                                    else:
                                        razon_final = razon
                                    
                                    observaciones = st.text_area("Observaciones detalladas:")
                                    responsable = st.text_input("Responsable que autoriza:", value="Administrador BEO")
                                
                                # Advertencia si tiene préstamo activo
                                if not prestamo_activo.empty and nuevo_estado != "prestado":
                                    st.warning("⚠️ **ATENCIÓN**: Este elemento tiene un préstamo activo. Al cambiar el estado se cerrará automáticamente el préstamo.")
                                
                                col_btn1, col_btn2 = st.columns(2)
                                with col_btn1:
                                    if st.form_submit_button("✅ CONFIRMAR CAMBIO", type="primary"):
                                        try:
                                            cursor = conn.cursor()
                                            
                                            # Registrar en historial
                                            cursor.execute("""
                                                INSERT INTO historial_estados 
                                                (elemento_id, estado_anterior, estado_nuevo, razon, observaciones, responsable)
                                                VALUES (?, ?, ?, ?, ?, ?)
                                            """, (elemento['id'], elemento['estado'], nuevo_estado, razon_final, observaciones, responsable))
                                            
                                            # Actualizar estado del elemento
                                            cursor.execute("""
                                                UPDATE elementos 
                                                SET estado = ?, observaciones = COALESCE(observaciones, '') || char(10) || ?
                                                WHERE id = ?
                                            """, (nuevo_estado, f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Estado cambiado a {nuevo_estado}. Razón: {razon_final}. Por: {responsable}", elemento['id']))
                                            
                                            # Si tiene préstamo activo y se cambia a disponible/mantenimiento, cerrar préstamo
                                            if not prestamo_activo.empty and nuevo_estado in ["disponible", "mantenimiento"]:
                                                cursor.execute("""
                                                    UPDATE prestamos 
                                                    SET estado = 'devuelto', fecha_devolucion_real = DATE('now'),
                                                        observaciones_devolucion = ?
                                                    WHERE elemento_id = ? AND estado = 'activo'
                                                """, (f"Préstamo cerrado automáticamente por cambio de estado. Razón: {razon_final}", elemento['id']))
                                            
                                            conn.commit()
                                            
                                            st.success(f"✅ Estado cambiado exitosamente a: {nuevo_estado}")
                                            del st.session_state[f"cambiar_estado_{elemento['id']}"]
                                            time.sleep(1)
                                            st.rerun()
                                            
                                        except Exception as e:
                                            st.error(f"❌ Error al cambiar estado: {e}")
                                
                                with col_btn2:
                                    if st.form_submit_button("❌ Cancelar"):
                                        del st.session_state[f"cambiar_estado_{elemento['id']}"]
                                        st.rerun()
                    
                    st.markdown("---")
            
            else:
                st.info("No se encontraron elementos con los criterios especificados")
            
            conn.close()
        except Exception as e:
            st.error(f"Error en cambio de estado: {e}")
    
    with tab4:
        st.subheader("📚 Historial de Préstamos por Elemento")
        st.markdown("**Ver por qué manos pasó cada elemento ortopédico**")
        
        try:
            conn = db.get_connection()
            
            # Selección de elemento
            elementos_df = pd.read_sql_query("""
                SELECT e.id, e.codigo, e.nombre, c.nombre as categoria
                FROM elementos e
                JOIN categorias c ON e.categoria_id = c.id
                WHERE e.activo = 1
                ORDER BY e.codigo
            """, conn)
            
            if not elementos_df.empty:
                elemento_id = st.selectbox(
                    "Seleccionar Elemento:",
                    options=elementos_df['id'].tolist(),
                    format_func=lambda x: f"{elementos_df[elementos_df['id'] == x]['codigo'].iloc[0]} - {elementos_df[elementos_df['id'] == x]['nombre'].iloc[0]}"
                )
                
                # Obtener información completa del elemento
                elemento_info = elementos_df[elementos_df['id'] == elemento_id].iloc[0]
                
                # Obtener historial completo de préstamos
                historial_elemento = pd.read_sql_query("""
                    SELECT 
                        p.id,
                        p.fecha_prestamo,
                        p.fecha_devolucion_estimada,
                        p.fecha_devolucion_real,
                        p.estado,
                        b.nombre as beneficiario,
                        b.tipo as tipo_beneficiario,
                        b.direccion as direccion_beneficiario,
                        h.nombre as hermano_solicitante,
                        l.nombre as logia,
                        p.duracion_dias,
                        p.entregado_por,
                        p.recibido_por,
                        p.observaciones_prestamo,
                        p.observaciones_devolucion,
                        CASE 
                            WHEN p.fecha_devolucion_real IS NULL AND DATE('now') > p.fecha_devolucion_estimada THEN 'VENCIDO'
                            WHEN p.fecha_devolucion_real IS NULL THEN 'ACTIVO'
                            WHEN p.fecha_devolucion_real <= p.fecha_devolucion_estimada THEN 'DEVUELTO A TIEMPO'
                            ELSE 'DEVUELTO CON RETRASO'
                        END as estado_cumplimiento,
                        CASE 
                            WHEN p.fecha_devolucion_real IS NOT NULL 
                            THEN CAST((JULIANDAY(p.fecha_devolucion_real) - JULIANDAY(p.fecha_devolucion_estimada)) AS INTEGER)
                            ELSE CAST((JULIANDAY('now') - JULIANDAY(p.fecha_devolucion_estimada)) AS INTEGER)
                        END as dias_diferencia
                    FROM prestamos p
                    JOIN beneficiarios b ON p.beneficiario_id = b.id
                    JOIN hermanos h ON p.hermano_solicitante_id = h.id
                    LEFT JOIN logias l ON h.logia_id = l.id
                    WHERE p.elemento_id = ?
                    ORDER BY p.fecha_prestamo DESC
                """, conn, params=[elemento_id])
                
                # Obtener historial de cambios de estado
                historial_estados = pd.read_sql_query("""
                    SELECT fecha_cambio, estado_anterior, estado_nuevo, razon, responsable, observaciones
                    FROM historial_estados
                    WHERE elemento_id = ?
                    ORDER BY fecha_cambio DESC
                """, conn, params=[elemento_id])
                
                st.markdown(f"#### 📊 Resumen de {elemento_info['codigo']} - {elemento_info['nombre']}")
                
                if not historial_elemento.empty:
                    # Estadísticas del elemento
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        total_prestamos = len(historial_elemento)
                        st.metric("Total Préstamos", total_prestamos)
                    with col2:
                        activos = len(historial_elemento[historial_elemento['estado'] == 'activo'])
                        st.metric("Actualmente Prestado", activos)
                    with col3:
                        diferentes_beneficiarios = historial_elemento['beneficiario'].nunique()
                        st.metric("Diferentes Beneficiarios", diferentes_beneficiarios)
                    with col4:
                        promedio_duracion = historial_elemento['duracion_dias'].mean()
                        st.metric("Duración Promedio", f"{promedio_duracion:.0f} días")
                    
                    # Tabla detallada
                    st.markdown("#### 📋 Historial Detallado de Préstamos")
                    st.dataframe(historial_elemento, use_container_width=True)
                    
                    # Gráfico de línea temporal si hay múltiples préstamos
                    if len(historial_elemento) > 1:
                        # Crear gráfico simple de barras con fechas
                        fig = px.bar(
                            historial_elemento,
                            x="fecha_prestamo",
                            y="duracion_dias",
                            color="estado_cumplimiento",
                            title="Historial de Préstamos",
                            hover_data=["beneficiario", "hermano_solicitante"]
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                else:
                    st.info("Este elemento no ha sido prestado aún")
                
                # Historial de cambios de estado
                if not historial_estados.empty:
                    st.markdown("#### 🔧 Historial de Cambios de Estado")
                    st.dataframe(historial_estados, use_container_width=True)
            
            else:
                st.warning("No hay elementos registrados")
            
            conn.close()
        except Exception as e:
            st.error(f"Error al cargar historial: {e}")

def gestionar_prestamos():
    """Gestión de préstamos según formulario BEO"""
    st.header("📋 Formulario de Préstamo BEO")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Nuevo Préstamo", "Préstamos Activos", "🔄 Devolución", "Historial"])
    
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
                    duracion_dias = duracion_cantidad * 30
                else:
                    duracion_dias = duracion_cantidad
                
                st.info(f"📅 **Duración del préstamo:** {duracion_dias} días ({duracion_cantidad} {duracion_tipo.lower()})")
                
                # HERMANO QUE SOLICITA EL PEDIDO
                st.markdown("#### 👨‍🤝‍👨 Hermano que solicita el pedido")
                
                try:
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
                        st.markdown("##### 📋 Información del Hermano Solicitante")
                        col_info1, col_info2 = st.columns(2)
                        with col_info1:
                            st.text(f"Hermano: {hermano_seleccionado['nombre']}")
                            st.text(f"Teléfono: {hermano_seleccionado['telefono'] or 'No disponible'}")
                            st.text(f"Logia: {hermano_seleccionado['logia']}")
                            st.text(f"Grado: {hermano_seleccionado['grado']}")
                        with col_info2:
                            st.text(f"Hospitalario: {hermano_seleccionado['hospitalario'] or 'No disponible'}")
                            st.text(f"Teléfono Hospitalario: {hermano_seleccionado['telefono_hospitalario'] or 'No disponible'}")
                            st.text(f"Venerable Maestro: {hermano_seleccionado['venerable_maestro'] or 'No disponible'}")
                            st.text(f"Teléfono Venerable: {hermano_seleccionado['telefono_venerable'] or 'No disponible'}")
                    else:
                        st.error("No hay hermanos registrados")
                        hermano_solicitante_id = None
                except Exception as e:
                    st.error(f"Error al cargar hermanos: {e}")
                    hermano_solicitante_id = None
            
            with col2:
                # A QUIEN VA DIRIGIDO EL PEDIDO
                st.markdown("#### 🎯 ¿A quién va dirigido el pedido de préstamo?, ¿Es Hermano o Familiar?")
                tipo_beneficiario = st.radio("Tipo de beneficiario:", ["Hermano", "Familiar"])
                
                if tipo_beneficiario == "Hermano":
                    if hermanos_df is not None and not hermanos_df.empty:
                        hermano_beneficiario_idx = st.selectbox(
                            "Seleccionar Hermano Beneficiario",
                            options=range(len(hermanos_df)),
                            format_func=lambda x: hermanos_df.iloc[x]['nombre']
                        )
                        beneficiario_nombre = hermanos_df.iloc[hermano_beneficiario_idx]['nombre']
                        beneficiario_telefono = hermanos_df.iloc[hermano_beneficiario_idx]['telefono']
                        parentesco = None
                        hermano_responsable_id = None
                        logia_beneficiario = hermanos_df.iloc[hermano_beneficiario_idx]['logia']
                    else:
                        beneficiario_nombre = ""
                        beneficiario_telefono = ""
                        parentesco = None
                        hermano_responsable_id = None
                        logia_beneficiario = ""
                
                else:  # Familiar
                    st.markdown("**Si es Familiar:**")
                    parentesco = st.selectbox(
                        "Que tipo de parentesco",
                        ["Madre", "Padre", "Esposa/o", "Hijo/a", "Hermano/a", "Abuelo/a", "Nieto/a", "Tío/a", "Sobrino/a", "Otro"]
                    )
                    
                    if parentesco == "Otro":
                        parentesco = st.text_input("Especificar parentesco")
                    
                    if hermanos_df is not None and not hermanos_df.empty:
                        hermano_resp_idx = st.selectbox(
                            "De que Hermano",
                            options=range(len(hermanos_df)),
                            format_func=lambda x: hermanos_df.iloc[x]['nombre'],
                            key="hermano_responsable"
                        )
                        hermano_responsable_id = hermanos_df.iloc[hermano_resp_idx]['id']
                        logia_beneficiario = hermanos_df.iloc[hermano_resp_idx]['logia']
                        st.info(f"Hermano responsable: {hermanos_df.iloc[hermano_resp_idx]['nombre']}")
                    else:
                        hermano_responsable_id = None
                        logia_beneficiario = ""
                    
                    beneficiario_nombre = st.text_input("Nombre del Familiar*")
                    beneficiario_telefono = st.text_input("Teléfono del Familiar")
                
                # DIRECCIÓN Y INFORMACIÓN DEL PRÉSTAMO
                st.markdown("#### 📍 Dirección de donde va dirigido el Elemento Ortopédico solicitado")
                direccion_entrega = st.text_area("Dirección completa*", help="Dirección donde se entregará el elemento")
                
                # Mostrar información
                st.text_input("Teléfono", value=beneficiario_telefono or "", disabled=True)
                st.text_input("Logia", value=logia_beneficiario, disabled=True)
                
                # ELEMENTO SOLICITADO
                st.markdown("#### 🦽 Elemento Ortopédico Solicitado")
                try:
                    elementos_disponibles = pd.read_sql_query("""
                        SELECT e.id, e.codigo, e.nombre, c.nombre as categoria, d.nombre as deposito
                        FROM elementos e
                        JOIN categorias c ON e.categoria_id = c.id
                        JOIN depositos d ON e.deposito_id = d.id
                        WHERE e.estado = 'disponible' AND e.activo = 1
                        ORDER BY e.codigo
                    """, conn)
                    
                    if not elementos_disponibles.empty:
                        elemento_id = st.selectbox(
                            "Elemento a Prestar*",
                            options=elementos_disponibles['id'].tolist(),
                            format_func=lambda x: f"{elementos_disponibles[elementos_disponibles['id'] == x]['codigo'].iloc[0]} - {elementos_disponibles[elementos_disponibles['id'] == x]['nombre'].iloc[0]} ({elementos_disponibles[elementos_disponibles['id'] == x]['deposito'].iloc[0]})"
                        )
                    else:
                        st.error("No hay elementos disponibles para préstamo")
                        elemento_id = None
                except Exception as e:
                    st.error(f"Error al cargar elementos: {e}")
                    elemento_id = None
                
                try:
                    conn.close()
                except:
                    pass
                
                # FECHA ESTIMADA DE DEVOLUCIÓN
                fecha_devolucion_estimada = fecha_prestamo + timedelta(days=duracion_dias)
                st.markdown("#### 📅 Fecha estimada de devolución del Elemento Ortopédico prestado")
                st.date_input(
                    "Fecha estimada de devolución", 
                    value=fecha_devolucion_estimada, 
                    disabled=True,
                    help=f"Calculada automáticamente: {fecha_prestamo.strftime('%d/%m/%Y')} + {duracion_dias} días = {fecha_devolucion_estimada.strftime('%d/%m/%Y')}"
                )
                
                # CAMPOS ADICIONALES
                st.markdown("#### 📝 Información Adicional")
                observaciones_prestamo = st.text_area("Observaciones del préstamo", help="Cualquier información relevante sobre el préstamo")
                
                col_resp1, col_resp2 = st.columns(2)
                with col_resp1:
                    autorizado_por = st.text_input("Autorizado por", help="Quien autoriza el préstamo")
                with col_resp2:
                    entregado_por = st.text_input("Entregado por*", help="Quien entrega físicamente el elemento")
            
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
                        
                        # Registrar cambio de estado
                        cursor.execute("""
                            INSERT INTO historial_estados 
                            (elemento_id, estado_anterior, estado_nuevo, razon, responsable)
                            VALUES (?, ?, ?, ?, ?)
                        """, (elemento_id, 'disponible', 'prestado', 'Préstamo registrado', entregado_por))
                        
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
        st.subheader("📋 Préstamos Activos - Monitoreo Completo")
        
        try:
            conn = db.get_connection()
            prestamos_activos = pd.read_sql_query("""
                SELECT p.id, e.codigo, e.nombre as elemento, 
                       b.nombre as beneficiario, b.tipo, b.telefono, b.direccion as ubicacion_actual,
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
    
    with tab3:
        st.header("🔄 Devolución de Elementos")
        st.markdown("**Proceso para registrar devoluciones de elementos prestados**")
        
        try:
            conn = db.get_connection()
            
            prestamos_activos = pd.read_sql_query("""
                SELECT p.id, p.fecha_prestamo, p.fecha_devolucion_estimada,
                       e.id as elemento_id, e.codigo, e.nombre as elemento,
                       b.nombre as beneficiario, b.telefono,
                       h.nombre as hermano_solicitante,
                       l.nombre as logia,
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
            
            if not prestamos_activos.empty:
                col1, col2 = st.columns(2)
                with col1:
                    busqueda = st.text_input("🔍 Buscar elemento o beneficiario:", placeholder="Código, nombre del elemento o beneficiario")
                with col2:
                    filtro_estado = st.selectbox("Estado:", ["Todos", "VIGENTE", "POR VENCER", "VENCIDO"])
                
                # Aplicar filtros
                prestamos_filtrados = prestamos_activos.copy()
                
                if filtro_estado != "Todos":
                    prestamos_filtrados = prestamos_filtrados[prestamos_filtrados['estado_vencimiento'] == filtro_estado]
                
                if busqueda:
                    prestamos_filtrados = prestamos_filtrados[
                        prestamos_filtrados['codigo'].str.contains(busqueda, case=False, na=False) |
                        prestamos_filtrados['elemento'].str.contains(busqueda, case=False, na=False) |
                        prestamos_filtrados['beneficiario'].str.contains(busqueda, case=False, na=False)
                    ]
                
                if not prestamos_filtrados.empty:
                    for idx, prestamo in prestamos_filtrados.iterrows():
                        # Color según estado
                        if prestamo['estado_vencimiento'] == 'VENCIDO':
                            estado_emoji = "🔴"
                            estado_color = "#ffebee"
                        elif prestamo['estado_vencimiento'] == 'POR VENCER':
                            estado_emoji = "🟡" 
                            estado_color = "#fff3e0"
                        else:
                            estado_emoji = "🟢"
                            estado_color = "#e8f5e8"
                        
                        with st.container():
                            st.markdown(f"""
                            <div style="background-color: {estado_color}; padding: 10px; border-radius: 8px; margin: 5px 0;">
                            <h5>{estado_emoji} {prestamo['codigo']} - {prestamo['elemento']}</h5>
                            <p><strong>Beneficiario:</strong> {prestamo['beneficiario']} | <strong>Hermano:</strong> {prestamo['hermano_solicitante']} ({prestamo['logia']})</p>
                            <p><strong>Prestado:</strong> {prestamo['fecha_prestamo']} | <strong>Debe devolver:</strong> {prestamo['fecha_devolucion_estimada']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button(f"🔄 DEVOLVER AHORA", key=f"dev_{prestamo['id']}", type="primary"):
                                st.session_state[f'devolver_{prestamo["id"]}'] = True
                            
                            if st.session_state.get(f'devolver_{prestamo["id"]}', False):
                                st.markdown("---")
                                st.markdown("#### 📝 Registrar Devolución")
                                
                                with st.form(f"devolucion_{prestamo['id']}"):
                                    col_dev1, col_dev2, col_dev3 = st.columns(3)
                                    
                                    with col_dev1:
                                        fecha_devolucion = st.date_input("Fecha de Devolución*", value=date.today())
                                        recibido_por = st.text_input("Recibido por*", placeholder="Nombre de quien recibe")
                                    
                                    with col_dev2:
                                        depositos_disponibles = pd.read_sql_query("SELECT id, nombre FROM depositos WHERE activo = 1 ORDER BY nombre", conn)
                                        
                                        if not depositos_disponibles.empty:
                                            deposito_devolucion_id = st.selectbox(
                                                "Depósito de Devolución*",
                                                options=depositos_disponibles['id'].tolist(),
                                                format_func=lambda x: depositos_disponibles[depositos_disponibles['id'] == x]['nombre'].iloc[0]
                                            )
                                        else:
                                            st.error("No hay depósitos disponibles")
                                            deposito_devolucion_id = None
                                        
                                        estado_elemento = st.selectbox("Estado del elemento:", ["Bueno", "Regular", "Necesita Mantenimiento", "Dañado"])
                                    
                                    with col_dev3:
                                        observaciones = st.text_area("Observaciones", placeholder="Estado del elemento, observaciones...")
                                    
                                    col_action1, col_action2 = st.columns(2)
                                    
                                    with col_action1:
                                        if st.form_submit_button("✅ CONFIRMAR DEVOLUCIÓN", type="primary", use_container_width=True):
                                            if recibido_por and deposito_devolucion_id:
                                                try:
                                                    cursor = conn.cursor()
                                                    
                                                    # Determinar estado final del elemento
                                                    if estado_elemento in ["Necesita Mantenimiento", "Dañado"]:
                                                        estado_final = "mantenimiento"
                                                    else:
                                                        estado_final = "disponible"
                                                    
                                                    # Actualizar préstamo
                                                    observaciones_completas = f"Estado del elemento: {estado_elemento}. {observaciones}".strip()
                                                    cursor.execute("""
                                                        UPDATE prestamos 
                                                        SET fecha_devolucion_real = ?, estado = 'devuelto',
                                                            observaciones_devolucion = ?, recibido_por = ?,
                                                            deposito_devolucion_id = ?
                                                        WHERE id = ?
                                                    """, (fecha_devolucion, observaciones_completas, recibido_por, deposito_devolucion_id, prestamo['id']))
                                                    
                                                    # Actualizar elemento (estado y depósito)
                                                    cursor.execute("""
                                                        UPDATE elementos 
                                                        SET estado = ?, deposito_id = ?
                                                        WHERE id = ?
                                                    """, (estado_final, deposito_devolucion_id, prestamo['elemento_id']))
                                                    
                                                    # Registrar cambio de estado
                                                    cursor.execute("""
                                                        INSERT INTO historial_estados 
                                                        (elemento_id, estado_anterior, estado_nuevo, razon, observaciones, responsable)
                                                        VALUES (?, ?, ?, ?, ?, ?)
                                                    """, (prestamo['elemento_id'], 'prestado', estado_final, 'Devolución registrada', observaciones_completas, recibido_por))
                                                    
                                                    conn.commit()
                                                    
                                                    st.success(f"""
                                                    ✅ **Devolución Registrada**
                                                    
                                                    📦 **Elemento:** {prestamo['codigo']} - {prestamo['elemento']}  
                                                    👤 **Recibido por:** {recibido_por}  
                                                    📅 **Fecha:** {fecha_devolucion}  
                                                    📊 **Estado:** {estado_final}
                                                    🏢 **Depósito:** {depositos_disponibles[depositos_disponibles['id'] == deposito_devolucion_id]['nombre'].iloc[0]}
                                                    """)
                                                    
                                                    del st.session_state[f'devolver_{prestamo["id"]}']
                                                    time.sleep(2)
                                                    st.rerun()
                                                    
                                                except Exception as e:
                                                    st.error(f"❌ Error: {e}")
                                            else:
                                                st.error("❌ Campos obligatorios faltantes")
                                    
                                    with col_action2:
                                        if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                            del st.session_state[f'devolver_{prestamo["id"]}']
                                            st.rerun()
                            
                            st.markdown("---")
                else:
                    st.warning("❌ No se encontraron elementos con los filtros aplicados")
            
            else:
                st.info("ℹ️ **No hay elementos prestados actualmente**")
            
            conn.close()
        except Exception as e:
            st.error(f"Error en devolución: {e}")
    
    with tab4:
        st.subheader("📚 Historial Completo de Devoluciones")
        
        try:
            conn = db.get_connection()
            
            historial_devoluciones = pd.read_sql_query("""
                SELECT e.codigo, e.nombre as elemento,
                       b.nombre as beneficiario,
                       h.nombre as hermano_solicitante,
                       l.nombre as logia,
                       p.fecha_prestamo, p.fecha_devolucion_estimada, p.fecha_devolucion_real,
                       p.recibido_por, p.observaciones_devolucion,
                       d.nombre as deposito_devolucion,
                       CAST((JULIANDAY(p.fecha_devolucion_real) - JULIANDAY(p.fecha_devolucion_estimada)) AS INTEGER) as dias_diferencia,
                       CASE 
                           WHEN p.fecha_devolucion_real <= p.fecha_devolucion_estimada THEN 'A TIEMPO'
                           ELSE 'CON RETRASO'
                       END as cumplimiento
                FROM prestamos p
                JOIN elementos e ON p.elemento_id = e.id
                JOIN beneficiarios b ON p.beneficiario_id = b.id
                JOIN hermanos h ON p.hermano_solicitante_id = h.id
                LEFT JOIN logias l ON h.logia_id = l.id
                LEFT JOIN depositos d ON p.deposito_devolucion_id = d.id
                WHERE p.estado = 'devuelto'
                ORDER BY p.fecha_devolucion_real DESC
            """, conn)
            
            if not historial_devoluciones.empty:
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    fecha_desde = st.date_input("Desde:", value=date.today() - timedelta(days=30))
                with col2:
                    fecha_hasta = st.date_input("Hasta:", value=date.today())
                
                # Aplicar filtro de fechas
                historial_filtrado = historial_devoluciones[
                    (pd.to_datetime(historial_devoluciones['fecha_devolucion_real']) >= pd.to_datetime(fecha_desde)) &
                    (pd.to_datetime(historial_devoluciones['fecha_devolucion_real']) <= pd.to_datetime(fecha_hasta))
                ]
                
                if not historial_filtrado.empty:
                    # Aplicar colores según cumplimiento
                    def highlight_cumplimiento_hist(row):
                        if row['cumplimiento'] == 'CON RETRASO':
                            return ['background-color: #ffebee'] * len(row)
                        else:
                            return ['background-color: #e8f5e8'] * len(row)
                    
                    styled_df = historial_filtrado.style.apply(highlight_cumplimiento_hist, axis=1)
                    st.dataframe(styled_df, use_container_width=True)
                    
                    # Estadísticas
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Devoluciones", len(historial_filtrado))
                    with col2:
                        a_tiempo = len(historial_filtrado[historial_filtrado['cumplimiento'] == 'A TIEMPO'])
                        st.metric("A Tiempo", a_tiempo)
                    with col3:
                        con_retraso = len(historial_filtrado[historial_filtrado['cumplimiento'] == 'CON RETRASO'])
                        st.metric("Con Retraso", con_retraso)
                    with col4:
                        if len(historial_filtrado) > 0:
                            porcentaje_cumplimiento = (a_tiempo / len(historial_filtrado)) * 100
                            st.metric("% Cumplimiento", f"{porcentaje_cumplimiento:.1f}%")
                    
                    # Gráfico de cumplimiento por logia
                    cumplimiento_por_logia = historial_filtrado.groupby(['logia', 'cumplimiento']).size().unstack(fill_value=0)
                    if not cumplimiento_por_logia.empty:
                        fig = px.bar(
                            cumplimiento_por_logia, 
                            title="Cumplimiento por Logia",
                            color_discrete_map={'A TIEMPO': 'green', 'CON RETRASO': 'red'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No hay devoluciones en el rango de fechas seleccionado")
            else:
                st.info("No hay devoluciones registradas aún")
            
            conn.close()
        except Exception as e:
            st.error(f"Error al cargar historial: {e}")

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
                    except Exception as e:
                        st.error(f"Error al guardar depósito: {e}")
                else:
                    st.error("El nombre del depósito es obligatorio")
    
    with col2:
        st.subheader("Depósitos Registrados")
        try:
            conn = db.get_connection()
            depositos_df = pd.read_sql_query("SELECT * FROM depositos WHERE activo = 1 ORDER BY nombre", conn)
            
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
                    LEFT JOIN elementos e ON d.id = e.deposito_id AND e.activo = 1
                    WHERE d.activo = 1
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
    """Dashboard con estadísticas y gráficos mejorado"""
    st.header("📊 Dashboard BEO - Control Integral")
    
    try:
        conn = db.get_connection()
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        total_elementos = pd.read_sql_query("SELECT COUNT(*) as total FROM elementos WHERE activo = 1", conn).iloc[0]['total']
        disponibles = pd.read_sql_query("SELECT COUNT(*) as total FROM elementos WHERE estado = 'disponible' AND activo = 1", conn).iloc[0]['total']
        prestamos_activos = pd.read_sql_query("SELECT COUNT(*) as total FROM prestamos WHERE estado = 'activo'", conn).iloc[0]['total']
        total_hermanos = pd.read_sql_query("SELECT COUNT(*) as total FROM hermanos WHERE activo = 1", conn).iloc[0]['total']
        
        with col1:
            st.metric("🦽 Total Elementos", total_elementos)
        with col2:
            st.metric("✅ Disponibles", disponibles)
        with col3:
            st.metric("📋 Préstamos Activos", prestamos_activos)
        with col4:
            st.metric("👨‍🤝‍👨 Hermanos Activos", total_hermanos)
        
        # Fila de gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🦽 Elementos por Categoría")
            elementos_categoria = pd.read_sql_query("""
                SELECT c.nombre, COUNT(e.id) as cantidad
                FROM categorias c
                LEFT JOIN elementos e ON c.id = e.categoria_id AND e.activo = 1
                WHERE c.activo = 1
                GROUP BY c.id, c.nombre
                HAVING COUNT(e.id) > 0
                ORDER BY cantidad DESC
            """, conn)
            
            if not elementos_categoria.empty:
                fig = px.pie(elementos_categoria, values='cantidad', names='nombre')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay elementos registrados por categoría")
        
        with col2:
            st.subheader("📊 Estado de Elementos")
            estado_elementos = pd.read_sql_query("""
                SELECT estado, COUNT(*) as cantidad
                FROM elementos
                WHERE activo = 1
                GROUP BY estado
            """, conn)
            
            if not estado_elementos.empty:
                colors = {'disponible': 'green', 'prestado': 'orange', 'mantenimiento': 'red'}
                fig = px.bar(
                    estado_elementos, 
                    x='estado', 
                    y='cantidad',
                    color='estado',
                    color_discrete_map=colors
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay elementos registrados")
        
        # Préstamos por logia
        st.subheader("🏛️ Préstamos Activos por Logia")
        prestamos_logia = pd.read_sql_query("""
            SELECT 
                COALESCE(l.nombre, 'Sin Logia') as logia, 
                COUNT(p.id) as prestamos_activos
            FROM logias l
            LEFT JOIN hermanos h ON l.id = h.logia_id
            LEFT JOIN prestamos p ON h.id = p.hermano_solicitante_id AND p.estado = 'activo'
            WHERE l.activo = 1
            GROUP BY l.id, l.nombre
            HAVING COUNT(p.id) > 0
            ORDER BY prestamos_activos DESC
        """, conn)
        
        if not prestamos_logia.empty:
            fig = px.bar(prestamos_logia, x='logia', y='prestamos_activos')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay préstamos activos por logia")
        
        # Alertas de vencimiento mejoradas
        st.subheader("🚨 Alertas de Vencimiento - Control Detallado")
        alertas_vencimiento = pd.read_sql_query("""
            SELECT e.codigo, e.nombre as elemento, 
                   b.nombre as beneficiario, b.telefono, b.direccion as ubicacion,
                   h.nombre as hermano_solicitante, h.telefono as telefono_hermano,
                   l.nombre as logia, l.hospitalario, l.telefono_hospitalario,
                   p.fecha_prestamo, p.fecha_devolucion_estimada,
                   CAST((JULIANDAY('now') - JULIANDAY(p.fecha_devolucion_estimada)) AS INTEGER) as dias_vencido,
                   CASE 
                       WHEN DATE('now') > p.fecha_devolucion_estimada THEN 'VENCIDO'
                       WHEN DATE(p.fecha_devolucion_estimada, '-7 days') <= DATE('now') THEN 'POR VENCER'
                       ELSE 'VIGENTE'
                   END as estado_alerta
            FROM prestamos p
            JOIN elementos e ON p.elemento_id = e.id
            JOIN beneficiarios b ON p.beneficiario_id = b.id
            JOIN hermanos h ON p.hermano_solicitante_id = h.id
            LEFT JOIN logias l ON h.logia_id = l.id
            WHERE p.estado = 'activo' 
            AND (DATE('now') > p.fecha_devolucion_estimada OR DATE(p.fecha_devolucion_estimada, '-7 days') <= DATE('now'))
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
            
            # Resumen de alertas
            col1, col2, col3 = st.columns(3)
            with col1:
                vencidos = len(alertas_vencimiento[alertas_vencimiento['estado_alerta'] == 'VENCIDO'])
                st.metric("🔴 Vencidos", vencidos)
            with col2:
                por_vencer = len(alertas_vencimiento[alertas_vencimiento['estado_alerta'] == 'POR VENCER'])
                st.metric("🟡 Por Vencer (7 días)", por_vencer)
            with col3:
                if vencidos > 0:
                    mas_vencido = alertas_vencimiento[alertas_vencimiento['estado_alerta'] == 'VENCIDO']['dias_vencido'].max()
                    st.metric("⏰ Máximo Retraso", f"{mas_vencido} días")
                else:
                    st.metric("⏰ Máximo Retraso", "0 días")
        else:
            st.success("✅ No hay préstamos próximos a vencer o vencidos")
        
        # Ubicaciones actuales de elementos prestados
        st.subheader("📍 Ubicaciones Actuales de Elementos Prestados")
        ubicaciones_actuales = pd.read_sql_query("""
            SELECT e.codigo, e.nombre as elemento,
                   b.nombre as beneficiario, b.direccion as ubicacion,
                   h.nombre as hermano_responsable, h.telefono,
                   l.nombre as logia,
                   p.fecha_prestamo, p.fecha_devolucion_estimada
            FROM prestamos p
            JOIN elementos e ON p.elemento_id = e.id
            JOIN beneficiarios b ON p.beneficiario_id = b.id
            JOIN hermanos h ON p.hermano_solicitante_id = h.id
            LEFT JOIN logias l ON h.logia_id = l.id
            WHERE p.estado = 'activo'
            ORDER BY e.codigo
        """, conn)
        
        if not ubicaciones_actuales.empty:
            st.dataframe(ubicaciones_actuales, use_container_width=True)
            st.caption(f"📍 Total de elementos prestados: {len(ubicaciones_actuales)}")
        else:
            st.info("📦 Todos los elementos están en depósitos")
        
        conn.close()
    except Exception as e:
        st.error(f"Error al cargar dashboard: {e}")

def main():
    """Función principal de la aplicación"""
    if not authenticate():
        return
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.title("🏛️ BEO - Banco de Elementos Ortopédicos")
        st.caption("Sistema de Gestión Integral - Versión Corregida")
    
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
    
    st.sidebar.markdown("---")
    st.sidebar.caption("Banco de Elementos Ortopédicos v2.1")
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
