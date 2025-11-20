# 🏛️ Instrucciones para Cargar Logias en la Base de Datos

Este documento explica cómo cargar las logias de la Gran Logia de la Argentina en la base de datos Neon PostgreSQL.

## 📋 Pre-requisitos

1. ✅ Archivo `.streamlit/secrets.toml` configurado con credenciales de Neon
2. ✅ Dependencias instaladas (`pip install -r requirements.txt`)
3. ✅ Conexión a internet activa

## 🚀 Ejecutar el Script

### Opción 1: Script Seguro (RECOMENDADO)

Usa el script que lee credenciales desde `secrets.toml`:

```bash
python cargar_logias_seguro.py
```

### Opción 2: Script con Credenciales Hardcodeadas

⚠️ **NO RECOMENDADO** - Solo para testing local:

```bash
python cargar_logias.py
```

**Nota:** Este archivo está en `.gitignore` y no se sube a Git por seguridad.

## 📊 Qué hace el script

El script carga automáticamente:

### ZONA 1 - Capital Federal (CABA)
- 155 logias ubicadas en Ciudad Autónoma de Buenos Aires
- Direcciones en diversos templos masónicos de CABA

### ZONA 2 - Gran Buenos Aires
- 71 logias ubicadas en localidades del conurbano
- Incluye: San Isidro, Vicente López, Tigre, Lomas de Zamora, Pilar, etc.

**Total: ~226 logias**

## 📝 Formato de salida

El script mostrará:

```
🏛️  CARGADOR DE LOGIAS - GRAN LOGIA DE LA ARGENTINA
============================================================

📍 ZONA 1 - Capital Federal (CABA)
============================================================
✅ Logia 'UNION DEL PLATA' N°1 - Capital Federal
✅ Logia 'CONFRATERNIDAD ARGENTINA' N°2 - Capital Federal
...

============================================================
📊 RESUMEN:
   ✅ Cargadas: 155
   ⚠️  Duplicadas: 0
   ❌ Errores: 0
============================================================

============================================================
📍 ZONA 2 - Gran Buenos Aires
============================================================
✅ Logia 'EGALITE HUMANITE FRATERNITE' N°20 - La Lucila
...

============================================================
✅ PROCESO COMPLETADO!
📊 Total logias cargadas: 226
============================================================
```

## ⚠️ Manejo de Duplicados

- Si una logia **ya existe** en la base de datos, el script la omitirá
- No sobrescribirá datos existentes
- Es seguro ejecutar el script múltiples veces

## 🔧 Solución de Problemas

### Error: "could not translate host name"
**Causa:** No hay conexión a internet o DNS no resuelve
**Solución:** Verifica tu conexión a internet

### Error: "No module named 'toml'"
**Causa:** Falta la dependencia toml
**Solución:** `pip install toml`

### Error: "Error al cargar secrets.toml"
**Causa:** Falta el archivo de configuración
**Solución:** Verifica que `.streamlit/secrets.toml` existe y tiene la sección `[database]`

## 📁 Estructura de Datos Cargados

Para cada logia se registra:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `nombre` | Nombre de la logia | UNION DEL PLATA |
| `numero` | Número de la logia | 1 |
| `oriente` | Localidad/Ciudad | Capital Federal |
| `direccion` | Dirección completa | TTE. GRAL. J. D. PERON 1242, CABA |
| `venerable_maestro` | NULL (se completa manualmente después) | - |
| `hospitalario` | NULL (se completa manualmente después) | - |
| `activo` | TRUE por defecto | true |

## 📌 Próximos Pasos

Después de cargar las logias:

1. **Completar datos de Venerables y Hospitalarios**
   Desde la app web: 🏛️ Gestión de Logias → Editar logia

2. **Registrar Hermanos**
   Desde la app web: 👨‍🤝‍👨 Gestión de Hermanos

3. **Crear Depósitos**
   Desde la app web: 🏢 Gestión de Depósitos

4. **Registrar Elementos**
   Desde la app web: 🦽 Gestión de Elementos

## 🔗 Referencias

- **Fuente de datos:** https://www.masoneria-argentina.org.ar/sobre-la-gla/logias-de-la-obediencia/
- **Fecha de extracción:** 20 de Noviembre 2025
- **Organización:** Gran Logia de la Argentina de Libres y Aceptados Masones

---

¿Problemas o dudas? Verifica que la configuración de Neon PostgreSQL esté correcta en `.streamlit/secrets.toml`
