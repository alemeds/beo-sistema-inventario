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
    
    tab1, tab2, tab3, tab4 = st.tabs(["Nuevo Préstamo", "Préstamos Activos", "🔄 DEVOLUCIÓN SIMPLE", "Historial"])
    
    with tab1:
        st.subheader("📝 Nuevo Formulario de Préstamo")
        st.caption("Completar la siguiente encuesta a fin de tener un control sobre los elementos ortopédicos prestados")
        
        with st.form("prestamo_beo_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📅 Información General")
                fecha_prestamo = st.date_input("Fecha*", value=date.today())
                
                # Duración del préstamo - EXACTO COMO EL FORMULARIO ORIGINAL
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
                
                # HERMANO QUE SOLICITA EL PEDIDO - EXACTO COMO FORMULARIO ORIGINAL
                st.markdown("#### 👨‍🤝‍👨 Hermano que solicita el pedido")
                
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
                    
                    # Mostrar información COMPLETA del hermano como en el formulario original
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
            
            with col2:
                # A QUIEN VA DIRIGIDO EL PEDIDO - EXACTO COMO FORMULARIO ORIGINAL
                st.markdown("#### 🎯 ¿A quién va dirigido el pedido de préstamo?, ¿Es Hermano o Familiar?")
                tipo_beneficiario = st.radio("Tipo de beneficiario:", ["Hermano", "Familiar"])
                
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
                        # Para hermanos, la logia es la misma
                        logia_beneficiario = hermanos_df.iloc[hermano_beneficiario_idx]['logia']
                    else:
                        beneficiario_nombre = ""
                        beneficiario_telefono = ""
                        parentesco = None
                        hermano_responsable_id = None
                        logia_beneficiario = ""
                
                else:  # Familiar - EXACTO COMO FORMULARIO ORIGINAL
                    st.markdown("**Si es Familiar:**")
                    parentesco = st.selectbox(
                        "Que tipo de parentesco",
                        ["Madre", "Padre", "Esposa/o", "Hijo/a", "Hermano/a", "Abuelo/a", "Nieto/a", "Tío/a", "Sobrino/a", "Otro"]
                    )
                    
                    if parentesco == "Otro":
                        parentesco = st.text_input("Especificar parentesco")
                    
                    # De qué hermano - EXACTO COMO FORMULARIO ORIGINAL
                    if not hermanos_df.empty:
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
                
                # DIRECCIÓN Y INFORMACIÓN DEL PRÉSTAMO - COMO FORMULARIO ORIGINAL
                st.markdown("#### 📍 Dirección de donde va dirigido el Elemento Ortopédico solicitado")
                direccion_entrega = st.text_area("Dirección completa*", help="Dirección donde se entregará el elemento")
                
                # Mostrar teléfono del beneficiario
                st.text_input("Teléfono", value=beneficiario_telefono or "", disabled=True)
                
                # Mostrar logia (automático)
                st.text_input("Logia", value=logia_beneficiario, disabled=True)
                
                # ELEMENTO SOLICITADO
                st.markdown("#### 🦽 Elemento Ortopédico Solicitado")
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
                
                # FECHA ESTIMADA DE DEVOLUCIÓN - COMO FORMULARIO ORIGINAL
                fecha_devolucion_estimada = fecha_prestamo + timedelta(days=duracion_dias)
                st.markdown("#### 📅 Fecha estimada de devolución del Elemento Ortopédico prestado")
                st.date_input(
                    "Fecha estimada de devolución", 
                    value=fecha_devolucion_estimada, 
                    disabled=True,
                    help=f"Calculada automáticamente: {fecha_prestamo.strftime('%d/%m/%Y')} + {duracion_dias} días = {fecha_devolucion_estimada.strftime('%d/%m/%Y')}"
                )
                
                # CAMPOS ADICIONALES DEL FORMULARIO
                st.markdown("#### 📝 Información Adicional")
                observaciones_prestamo = st.text_area("Observaciones del préstamo", help="Cualquier información relevante sobre el préstamo")
                
                # Responsables
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
        st.subheader("📋 Préstamos Activos - Monitoreo")
        st.info("💡 Para devolver elementos, usar la pestaña '🔄 DEVOLUCIÓN SIMPLE'")
        
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
                
        else:
            st.info("ℹ️ No hay préstamos activos en este momento")
        
        conn.close()

    with tab3:
        st.header("🔄 DEVOLUCIÓN SIMPLE DE ELEMENTOS")
        st.markdown("**✨ Proceso simplificado para recibir elementos devueltos**")
        st.info("💡 **Tip:** Solo completa lo esencial - fecha, quien recibe y a qué depósito va")
        
        conn = db.get_connection()
        
        # Obtener préstamos activos de forma simple
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
            st.markdown("### 📋 Elementos Disponibles para Devolución")
            
            # Filtro simple
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
                st.markdown(f"#### Mostrando {len(prestamos_filtrados)} elementos")
                
                # Lista simple de elementos para devolver
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
                    
                    # Tarjeta simple
                    with st.container():
                        st.markdown(f"""
                        <div style="background-color: {estado_color}; padding: 10px; border-radius: 8px; margin: 5px 0;">
                        <h5>{estado_emoji} {prestamo['codigo']} - {prestamo['elemento']}</h5>
                        <p><strong>Beneficiario:</strong> {prestamo['beneficiario']} | <strong>Hermano:</strong> {prestamo['hermano_solicitante']} ({prestamo['logia']})</p>
                        <p><strong>Prestado:</strong> {prestamo['fecha_prestamo']} | <strong>Debe devolver:</strong> {prestamo['fecha_devolucion_estimada']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Botón de devolución simple
                        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
                        with col_btn1:
                            if st.button(f"✅ DEVOLVER", key=f"dev_simple_{prestamo['id']}", type="primary"):
                                st.session_state[f'devolver_simple_{prestamo["id"]}'] = True
                        
                        # Formulario simple de devolución
                        if st.session_state.get(f'devolver_simple_{prestamo["id"]}', False):
                            st.markdown("---")
                            st.markdown("#### 📝 Registrar Devolución Simple")
                            
                            with st.form(f"devolucion_simple_{prestamo['id']}"):
                                col_dev1, col_dev2, col_dev3 = st.columns(3)
                                
                                with col_dev1:
                                    fecha_devolucion = st.date_input("Fecha de Devolución*", value=date.today())
                                    recibido_por = st.text_input("Recibido por*", placeholder="Nombre de quien recibe")
                                
                                with col_dev2:
                                    # Obtener depósitos disponibles
                                    depositos_disponibles = pd.read_sql_query("SELECT id, nombre FROM depositos ORDER BY nombre", conn)
                                    
                                    if not depositos_disponibles.empty:
                                        deposito_devolucion_id = st.selectbox(
                                            "Depósito de Destino*",
                                            options=depositos_disponibles['id'].tolist(),
                                            format_func=lambda x: depositos_disponibles[depositos_disponibles['id'] == x]['nombre'].iloc[0]
                                        )
                                    else:
                                        st.error("No hay depósitos disponibles")
                                        deposito_devolucion_id = None
                                    
                                    estado_elemento = st.selectbox("Estado del elemento:", ["Bueno", "Regular", "Necesita Mantenimiento"])
                                
                                with col_dev3:
                                    observaciones = st.text_area("Observaciones (opcional)", placeholder="Estado del elemento, observaciones...")
                                
                                # Botones de acción
                                col_action1, col_action2 = st.columns(2)
                                
                                with col_action1:
                                    if st.form_submit_button("✅ CONFIRMAR DEVOLUCIÓN", type="primary", use_container_width=True):
                                        if recibido_por and deposito_devolucion_id:
                                            try:
                                                cursor = conn.cursor()
                                                
                                                # Determinar estado final del elemento
                                                if estado_elemento == "Necesita Mantenimiento":
                                                    estado_final = "mantenimiento"
                                                else:
                                                    estado_final = "disponible"
                                                
                                                # Actualizar préstamo
                                                observaciones_completas = f"Estado: {estado_elemento}. {observaciones}".strip()
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
                                                
                                                st.success(f"""
                                                ✅ **Devolución Registrada**
                                                
                                                📦 **Elemento:** {prestamo['codigo']} - {prestamo['elemento']}  
                                                👤 **Recibido por:** {recibido_por}  
                                                📅 **Fecha:** {fecha_devolucion}  
                                                📊 **Estado:** {estado_final}
                                                """)
                                                
                                                del st.session_state[f'devolver_simple_{prestamo["id"]}']
                                                time.sleep(2)
                                                st.rerun()
                                                
                                            except Exception as e:
                                                st.error(f"❌ Error: {e}")
                                        else:
                                            st.error("❌ Campos obligatorios faltantes")
                                
                                with col_action2:
                                    if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                        del st.session_state[f'devolver_simple_{prestamo["id"]}']
                                        st.rerun()
                        
                        st.markdown("---")
            else:
                st.warning("❌ No se encontraron elementos con los filtros aplicados")
        
        else:
            st.info("ℹ️ **No hay elementos prestados actualmente**")
            st.markdown("Para registrar un nuevo préstamo, ve a la pestaña **'Nuevo Préstamo'**")
        
        conn.close()
    
    with tab4:
        st.subheader("📚 Historial de Devoluciones")
        st.markdown("**Registro completo de todas las devoluciones realizadas**")
        
        conn = db.get_connection()
        
        # Obtener historial básico
        historial_devoluciones = pd.read_sql_query("""
            SELECT e.codigo, e.nombre as elemento,
                   b.nombre as beneficiario,
                   h.nombre as hermano_solicitante,
                   p.fecha_prestamo, p.fecha_devolucion_estimada, p.fecha_devolucion_real,
                   p.recibido_por, p.observaciones_devolucion,
                   CAST((JULIANDAY(p.fecha_devolucion_real) - JULIANDAY(p.fecha_devolucion_estimada)) AS INTEGER) as dias_diferencia
            FROM prestamos p
            JOIN elementos e ON p.elemento_id = e.id
            JOIN beneficiarios b ON p.beneficiario_id = b.id
            JOIN hermanos h ON p.hermano_solicitante_id = h.id
            WHERE p.estado = 'devuelto'
            ORDER BY p.fecha_devolucion_real DESC
            LIMIT 50
        """, conn)
        
        if not historial_devoluciones.empty:
            # Filtros simples
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
                st.dataframe(historial_filtrado, use_container_width=True)
                
                # Estadísticas simples
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Devoluciones", len(historial_filtrado))
                with col2:
                    a_tiempo = len(historial_filtrado[historial_filtrado['dias_diferencia'] <= 0])
                    st.metric("A Tiempo/Anticipadas", a_tiempo)
                with col3:
                    con_retraso = len(historial_filtrado[historial_filtrado['dias_diferencia'] > 0])
                    st.metric("Con Retraso", con_retraso)
            else:
                st.warning("No hay devoluciones en el rango de fechas seleccionado")
        else:
            st.info("No hay devoluciones registradas aún")
        
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
