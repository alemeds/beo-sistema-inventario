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
                tipo TEXT NOT NULL,
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
                elemento_id INTEGER,
                beneficiario_id INTEGER,
                hermano_solicitante_id INTEGER,
                duracion_dias INTEGER,
                fecha_devolucion_estimada DATE,
                fecha_devolucion_real DATE,
                estado TEXT DEFAULT 'activo',
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
        
        conn.commit()
        conn.close()

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
        
        ### 🔧 Cambiar Estado de Elementos
        - **Ir a:** Gestión de Elementos → "🔧 Cambiar Estado de Elementos"
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
        
        1. **Ir a:** Formulario de Préstamo → "🔄 DEVOLVER ELEMENTOS"
        
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
           - Si el elemento necesita mantenimiento, usar "🔧 Devolver a Mantenimiento"
        
        ### 🏢 Selección de Depósito
        - Puedes elegir a qué depósito devolver cada elemento
        - No necesariamente debe ser el depósito original
        - Útil para redistribuir elementos según necesidades
        
        ### ⏰ Devoluciones Anticipadas
        - **SÍ puedes devolver** antes de la fecha límite
        - No hay restricciones de tiempo
        - Útil para elementos que ya no se necesitan
        
        ### 📚 Historial de Devoluciones
        - **Ir a:** Formulario de Préstamo → "Historial de Devoluciones"
        - **Ver todas** las devoluciones realizadas
        - **Filtrar por fechas** y cumplimiento
        - **Estadísticas** de cumplimiento (a tiempo, con retraso, anticipadas)
        
        ### 💡 Consejos
        - Describir bien el estado del elemento al devolverlo
        - Si hay daños, usar "🔧 Devolver a Mantenimiento"
        - Las devoluciones anticipadas son válidas y recomendadas
        - El historial ayuda a evaluar el cumplimiento por logia
        """)
    
    elif seccion == "🔧 Cambio de Estados":
        st.markdown("""
        ## 🔧 Cambio Manual de Estados
        
        ### ¿Para qué sirve?
        Cambiar manualmente el estado de elementos para correcciones, mantenimiento o casos especiales.
        
        ### 📝 Cómo Cambiar el Estado de un Elemento
        
        1. **Ir a:** Gestión de Elementos → "🔧 Cambiar Estado de Elementos"
        
        2. **Encontrar el Elemento:**
           - **Filtrar por estado actual:** Disponible, Prestado, Mantenimiento
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
        - **Historial automático** en observaciones del elemento
        - **Fecha y hora** del cambio
        - **Responsable** que autorizó
        - **Razón detallada** del cambio
        
        ### 🎯 Casos de Uso Comunes
        
        #### Devolución No Registrada
        ```
        Estado: prestado → disponible
        Razón: "Devolución no registrada"
        Obs: "El elemento fue devuelto ayer pero no se registró"
        ```
        
        #### Mantenimiento Preventivo
        ```
        Estado: disponible → mantenimiento
        Razón: "Mantenimiento preventivo"
        Obs: "Revisión semestral programada"
        ```
        
        #### Corrección de Error
        ```
        Estado: prestado → disponible
        Razón: "Error en registro anterior"
        Obs: "Se registró préstamo por error"
        ```
        
        ### 💡 Consejos
        - Usar esta función solo para casos especiales
        - Para devoluciones normales, usar "🔄 DEVOLVER ELEMENTOS"
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
        R: Sí, puedes devolver elementos en cualquier momento desde "🔄 DEVOLVER ELEMENTOS".
        
        **P: ¿Qué pasa si no devuelven a tiempo?**
        R: El sistema marca como "VENCIDO" y aparece en alertas del Dashboard.
        
        **P: ¿Puedo cambiar la duración de un préstamo ya registrado?**
        R: No directamente, pero puedes registrar la devolución y crear un nuevo préstamo.
        
        ### 🦽 Gestión de Elementos
        
        **P: ¿Cómo marco un elemento como dañado?**
        R: Ve a "🔧 Cambiar Estado de Elementos" y cambia a "Mantenimiento".
        
        **P: ¿Puedo mover un elemento a otro depósito?**
        R: Sí, durante la devolución puedes elegir el depósito de destino.
        
        **P: ¿Qué pasa si registro un código duplicado?**
        R: El sistema mostrará error. Cada código debe ser único.
        
        ### 📊 Reportes y Seguimiento
        
        **P: ¿Cómo veo qué logia usa más el BEO?**
        R: En el Dashboard, revisa el gráfico "Préstamos por Logia".
        
        **P: ¿Puedo ver el historial de un elemento específico?**
        R: Actualmente no hay vista específica, pero se puede implementar.
        
        **P: ¿Cómo exporto datos para reportes?**
        R: Actualmente no hay función de exportación, pero se puede agregar.
        
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
        
        **P: ¿Hay manual de administrador?**
        R: Este manual cubre el uso básico. Para administración avanzada, contactar soporte.
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
        conn = db.get_connection()
        logias_df = pd.read_sql_query("SELECT id, nombre, numero FROM logias ORDER BY numero, nombre", conn)
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
                fecha_iniciacion = st.date_input("Fecha de Iniciación", value=None)
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
    
    tab1, tab2, tab3 = st.tabs(["Nuevo Elemento", "Inventario", "🔧 Cambiar Estado"])
    
    with tab1:
        conn = db.get_connection()
        depositos_df = pd.read_sql_query("SELECT id, nombre FROM depositos", conn)
        categorias_df = pd.read_sql_query("SELECT id, nombre FROM categorias", conn)
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
        st.markdown("**Gestión manual de estados para casos especiales**")
        st.info("💡 Para devoluciones normales, usar 'Formulario de Préstamo' → '🔄 DEVOLVER ELEMENTOS'")
        
        if st.button("🔄 Actualizar Lista"):
            st.rerun()

def gestionar_prestamos():
    """Gestión de préstamos según formulario BEO"""
    st.header("📋 Formulario de Préstamo BEO")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Nuevo Préstamo", "Préstamos Activos", "🔄 DEVOLVER ELEMENTOS", "Historial"])
    
    with tab1:
        st.subheader("📝 Nuevo Formulario de Préstamo")
        
        with st.form("prestamo_beo_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📅 Información General")
                fecha_prestamo = st.date_input("Fecha*", value=date.today())
                
                st.markdown("#### ⏱️ Duración del Préstamo")
                col_dur1, col_dur2 = st.columns(2)
                with col_dur1:
                    duracion_tipo = st.selectbox("Tipo", ["Días", "Meses"])
                with col_dur2:
                    duracion_cantidad = st.number_input("Cantidad", min_value=1, value=90 if duracion_tipo == "Días" else 3)
                
                duracion_dias = duracion_cantidad * 30 if duracion_tipo == "Meses" else duracion_cantidad
                st.info(f"📅 Duración: {duracion_dias} días")
                
                st.markdown("#### 👨‍🤝‍👨 Hermano Solicitante")
                conn = db.get_connection()
                hermanos_df = pd.read_sql_query("""
                    SELECT h.id, h.nombre, h.telefono, h.grado, l.nombre as logia
                    FROM hermanos h
                    LEFT JOIN logias l ON h.logia_id = l.id
                    WHERE h.activo = 1
                    ORDER BY h.nombre
                """, conn)
                
                if not hermanos_df.empty:
                    hermano_idx = st.selectbox(
                        "Seleccionar Hermano",
                        options=range(len(hermanos_df)),
                        format_func=lambda x: f"{hermanos_df.iloc[x]['nombre']} - {hermanos_df.iloc[x]['logia']}"
                    )
                    hermano_solicitante_id = hermanos_df.iloc[hermano_idx]['id']
                else:
                    st.error("No hay hermanos registrados")
                    hermano_solicitante_id = None
            
            with col2:
                st.markdown("#### 🎯 Beneficiario del Préstamo")
                tipo_beneficiario = st.radio("¿Es Hermano o Familiar?", ["Hermano", "Familiar"])
                
                if tipo_beneficiario == "Hermano":
                    beneficiario_nombre = hermanos_df.iloc[hermano_idx]['nombre'] if not hermanos_df.empty else ""
                    beneficiario_telefono = hermanos_df.iloc[hermano_idx]['telefono'] if not hermanos_df.empty else ""
                    parentesco = None
                    hermano_responsable_id = None
                else:
                    parentesco = st.selectbox("Parentesco", ["Madre", "Padre", "Esposa/o", "Hijo/a", "Hermano/a", "Otro"])
                    beneficiario_nombre = st.text_input("Nombre del Familiar*")
                    beneficiario_telefono = st.text_input("Teléfono")
                    hermano_responsable_id = hermano_solicitante_id
                
                st.markdown("#### 📍 Información del Préstamo")
                direccion_entrega = st.text_area("Dirección de entrega*")
                
                elementos_disponibles = pd.read_sql_query("""
                    SELECT e.id, e.codigo, e.nombre, c.nombre as categoria
                    FROM elementos e
                    JOIN categorias c ON e.categoria_id = c.id
                    WHERE e.estado = 'disponible'
                    ORDER BY e.codigo
                """, conn)
                
                if not elementos_disponibles.empty:
                    elemento_id = st.selectbox(
                        "Elemento a Prestar*",
                        options=elementos_disponibles['id'].tolist(),
                        format_func=lambda x: f"{elementos_disponibles[elementos_disponibles['id'] == x]['codigo'].iloc[0]} - {elementos_disponibles[elementos_disponibles['id'] == x]['nombre'].iloc[0]}"
                    )
                else:
                    st.error("No hay elementos disponibles")
                    elemento_id = None
                
                fecha_devolucion_estimada = fecha_prestamo + timedelta(days=duracion_dias)
                st.date_input("Fecha estimada de devolución", value=fecha_devolucion_estimada, disabled=True)
                
                observaciones_prestamo = st.text_area("Observaciones")
                entregado_por = st.text_input("Entregado por*")
                
                conn.close()
            
            submitted = st.form_submit_button("📋 Registrar Préstamo", use_container_width=True)
            
            if submitted:
                if hermano_solicitante_id and elemento_id and beneficiario_nombre and direccion_entrega and entregado_por:
                    try:
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            INSERT INTO beneficiarios (tipo, hermano_id, hermano_responsable_id, 
                                                     parentesco, nombre, telefono, direccion)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (tipo_beneficiario.lower(), 
                             hermano_solicitante_id if tipo_beneficiario == "Hermano" else None,
                             hermano_responsable_id, parentesco, beneficiario_nombre, 
                             beneficiario_telefono, direccion_entrega))
                        
                        beneficiario_id = cursor.lastrowid
                        
                        cursor.execute("""
                            INSERT INTO prestamos 
                            (fecha_prestamo, elemento_id, beneficiario_id, hermano_solicitante_id,
                             duracion_dias, fecha_devolucion_estimada, observaciones_prestamo, entregado_por)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (fecha_prestamo, elemento_id, beneficiario_id, hermano_solicitante_id,
                             duracion_dias, fecha_devolucion_estimada, observaciones_prestamo, entregado_por))
                        
                        cursor.execute("UPDATE elementos SET estado = 'prestado' WHERE id = ?", (elemento_id,))
                        
                        conn.commit()
                        conn.close()
                        st.success("✅ Préstamo registrado exitosamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.error("❌ Campos obligatorios faltantes")
    
    with tab2:
        st.subheader("📋 Préstamos Activos")
        st.info("💡 Para devolver elementos, usar la pestaña '🔄 DEVOLVER ELEMENTOS'")
        
        conn = db.get_connection()
        prestamos_activos = pd.read_sql_query("""
            SELECT e.codigo, e.nombre as elemento, b.nombre as beneficiario,
                   h.nombre as hermano, p.fecha_prestamo, p.fecha_devolucion_estimada,
                   CASE 
                       WHEN DATE('now') > p.fecha_devolucion_estimada THEN 'VENCIDO'
                       WHEN DATE(p.fecha_devolucion_estimada, '-7 days') <= DATE('now') THEN 'POR VENCER'
                       ELSE 'VIGENTE'
                   END as estado
            FROM prestamos p
            JOIN elementos e ON p.elemento_id = e.id
            JOIN beneficiarios b ON p.beneficiario_id = b.id
            JOIN hermanos h ON p.hermano_solicitante_id = h.id
            WHERE p.estado = 'activo'
            ORDER BY p.fecha_devolucion_estimada
        """, conn)
        conn.close()
        
        if not prestamos_activos.empty:
            st.dataframe(prestamos_activos, use_container_width=True)
        else:
            st.info("No hay préstamos activos")
    
    with tab3:
        st.header("🔄 DEVOLVER ELEMENTOS")
        st.info("✨ Aquí puedes devolver cualquier elemento prestado en cualquier momento")
        
        if st.button("🔄 Actualizar Lista"):
            st.rerun()
    
    with tab4:
        st.subheader("📚 Historial de Devoluciones")
        st.info("📋 Aquí aparecerá el historial de todas las devoluciones realizadas")

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
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_elementos = pd.read_sql_query("SELECT COUNT(*) as total FROM elementos", conn).iloc[0]['total']
    disponibles = pd.read_sql_query("SELECT COUNT(*) as total FROM elementos WHERE estado = 'disponible'", conn).iloc[0]['total']
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
            fig = px.bar(estado_elementos, x='estado', y='cantidad')
            st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("🚨 Alertas de Vencimiento")
    prestamos_vencer = pd.read_sql_query("""
        SELECT e.codigo, e.nombre as elemento, b.nombre as beneficiario,
               p.fecha_devolucion_estimada
        FROM prestamos p
        JOIN elementos e ON p.elemento_id = e.id
        JOIN beneficiarios b ON p.beneficiario_id = b.id
        WHERE p.estado = 'activo' 
        AND p.fecha_devolucion_estimada <= DATE('now', '+7 days')
        ORDER BY p.fecha_devolucion_estimada
    """, conn)
    
    if not prestamos_vencer.empty:
        st.dataframe(prestamos_vencer, use_container_width=True)
    else:
        st.success("✅ No hay préstamos próximos a vencer")
    
    conn.close()

def main():
    """Función principal de la aplicación"""
    if not authenticate():
        return
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.title("🏛️ BEO - Banco de Elementos Ortopédicos")
        st.caption("Sistema de Gestión Integral")
    
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
    st.sidebar.caption("Banco de Elementos Ortopédicos")
    if st.sidebar.button("🚪 Cerrar Sesión"):
        st.session_state.authenticated = False
        st.rerun()
    
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

if __name__ == "__main__":
    main()
