# 📁 Carpeta de Contexto - Órdenes de Pago

Esta carpeta contiene toda la documentación de contexto necesaria para trabajar con el sistema de órdenes de pago.

---

## 🆕 NUEVO CHAT CON IA

👉 **¿Vas a iniciar un nuevo chat?** Lee primero: [`PARA_NUEVO_CHAT.md`](./PARA_NUEVO_CHAT.md)

---

## 📋 ARCHIVOS DISPONIBLES

### 0. **PARA_NUEVO_CHAT.md** 🚀 GUÍA DE INICIO

**Úsalo cuando:**

- Vas a comenzar un nuevo chat con IA
- Necesitas saber qué archivos cargar
- Quieres un prompt inicial optimizado

**Contiene:**

- Checklist para nuevo chat
- Archivos a cargar según tarea
- Prompt inicial recomendado
- Tips para trabajar con IA

---

### 1. **REFERENCIA_RAPIDA.md** ⭐ COMIENZA AQUÍ

**Úsalo cuando:**

- Necesitas un recordatorio rápido de cómo funciona el sistema
- Buscas endpoints específicos
- Quieres ver ejemplos de código rápidos
- Necesitas comandos útiles

**Contiene:**

- Resumen ejecutivo de 2 páginas
- Endpoints principales
- Ejemplos de código
- Comandos útiles
- Checklist para nuevos chats

---

### 2. **CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md** 📚 CONTEXTO COMPLETO

**Úsalo cuando:**

- Inicias trabajo en un nuevo chat de IA
- Necesitas entender toda la arquitectura
- Vas a implementar nuevas funcionalidades
- Necesitas ver todas las reglas de negocio
- Requieres documentación técnica completa

**Contiene:**

- Arquitectura completa (Clean Architecture + DDD)
- Modelos detallados con propiedades y métodos
- Todos los endpoints de la API
- Reglas de negocio completas
- Flujos completos de trabajo
- Validaciones y restricciones
- Ejemplos frontend en React, Vue, Angular
- Configuración necesaria
- Testing y debugging

**Tamaño:** ~50 páginas (contexto completo)

---

### 3. **CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md** 📧 CONTEXTO DE ENVÍO

**Úsalo cuando:**

- Trabajas específicamente en funcionalidad de envío de enlaces
- Necesitas modificar templates de correo
- Trabajas con tareas de Celery
- Implementas notificaciones por email
- Necesitas generar PDFs

**Contiene:**

- Implementación detallada del sistema de envío
- Tres formas de enviar enlaces
- Plantillas HTML (correo y PDF)
- Tareas asíncronas con Celery
- Código frontend específico para envío
- Eliminación de contraseñas temporales
- Configuración de email y WeasyPrint

**Tamaño:** ~40 páginas

---

## 🎯 ¿QUÉ ARCHIVO DEBO USAR?

### Para un nuevo chat con IA:

```
1. REFERENCIA_RAPIDA.md           → Lectura rápida (2 min)
2. CONTEXTO_COMPLETO_SISTEMA...   → Contexto completo del sistema
3. CONTEXTO_COMPLETO_ENVIO...     → Solo si trabajas con envío de correos
```

### Para consulta rápida:

```
REFERENCIA_RAPIDA.md → Busca lo que necesitas aquí primero
```

### Para implementar nuevas features:

```
CONTEXTO_COMPLETO_SISTEMA... → Lee todo primero
```

### Para modificar envío de correos:

```
CONTEXTO_COMPLETO_ENVIO... → Todo sobre emails y PDFs
```

---

## 📝 EJEMPLO: INICIO DE CHAT CON IA

### Opción 1: Chat General sobre Órdenes de Pago

```markdown
Hola, voy a trabajar en el sistema de órdenes de pago.

Adjunto el contexto completo:

- REFERENCIA_RAPIDA.md
- CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md

Necesito implementar [describe tu tarea aquí]
```

### Opción 2: Chat Específico sobre Envío de Enlaces

```markdown
Hola, voy a trabajar en el envío de enlaces de pago.

Adjunto el contexto:

- REFERENCIA_RAPIDA.md
- CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md

Necesito [describe tu tarea específica sobre envío]
```

### Opción 3: Chat Completo (TODO)

```markdown
Hola, voy a trabajar en el sistema de órdenes de pago.

Adjunto TODO el contexto disponible:

- REFERENCIA_RAPIDA.md
- CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md
- CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md

Necesito implementar funcionalidad completa que incluye [...]
```

---

## 🔄 MANTENER ACTUALIZADO

Cuando hagas cambios importantes al sistema:

1. ✅ Actualiza `REFERENCIA_RAPIDA.md` si cambias endpoints o funcionalidad básica
2. ✅ Actualiza `CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md` si cambias arquitectura o modelos
3. ✅ Actualiza `CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md` si cambias sistema de correos

---

## 📚 DOCUMENTACIÓN ADICIONAL

Además de estos archivos de contexto, revisa:

- `../docs/` - Documentación técnica específica
- `../models.py` - Código fuente de los modelos
- `../presentation/views/` - Código de los endpoints
- `../tasks.py` - Tareas de Celery

---

## 💡 TIPS

1. **No copies todo el contexto** en cada mensaje de IA - adjúntalo al inicio del chat
2. **Usa REFERENCIA_RAPIDA** para consultas rápidas sin necesidad de IA
3. **Mantén sincronizados** el código y la documentación
4. **Lee primero, implementa después** - evita errores conociendo el contexto completo

---

## 🆘 AYUDA

Si tienes dudas:

1. Lee primero `REFERENCIA_RAPIDA.md`
2. Busca en `CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md`
3. Si es sobre correos, revisa `CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md`
4. Consulta el código fuente en `../`
5. Pregunta al equipo de desarrollo

---

**Última actualización:** 28 de Noviembre de 2025  
**Mantenido por:** Equipo de Desarrollo API

