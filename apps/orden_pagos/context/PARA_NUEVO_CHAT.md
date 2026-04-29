# 🚀 INICIAR NUEVO CHAT - Sistema de Órdenes de Pago

> **Guía rápida para comenzar a trabajar con IA en un nuevo chat**

---

## 📋 CONTEXTO MÍNIMO (Carga esto primero)

Para trabajar eficientemente en un nuevo chat, carga estos archivos en orden:

### 1️⃣ **REFERENCIA_RAPIDA.md** (⭐ SIEMPRE PRIMERO)

- 2 páginas con lo esencial
- Endpoints principales
- Ejemplos de código
- Comandos útiles

### 2️⃣ **Luego elige según tu tarea:**

#### Si vas a trabajar en el sistema completo:

- `CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md`
- Toda la arquitectura, modelos, endpoints, reglas de negocio

#### Si solo trabajas con envío de enlaces:

- `CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md`
- Flujo completo de envío de enlaces y correos

#### Si necesitas ambos:

- Carga los dos contextos completos

---

## 🎯 PROMPT INICIAL RECOMENDADO

Usa este prompt al iniciar un nuevo chat:

```
Hola, voy a trabajar en el sistema de órdenes de pago de Django.

Aquí te paso el contexto del sistema:
[Adjuntar REFERENCIA_RAPIDA.md]
[Adjuntar CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md (si es necesario)]

El sistema usa:
- Django + DRF
- Clean Architecture + DDD
- PostgreSQL
- Celery para tareas asíncronas
- WeasyPrint para PDFs

Por favor confirma que has entendido la arquitectura y estás listo para trabajar.
```

---

## 📂 ESTRUCTURA DE ARCHIVOS DE CONTEXTO

```
context/
├── PARA_NUEVO_CHAT.md                          ← Estás aquí
├── REFERENCIA_RAPIDA.md                        ← ⭐ Siempre primero (2 pág)
├── CONTEXTO_COMPLETO_SISTEMA_ORDEN_PAGOS.md    ← Arquitectura completa (~50 pág)
├── CONTEXTO_COMPLETO_ENVIO_ENLACE_PAGO.md      ← Envío de enlaces (~30 pág)
└── README.md                                   ← Guía de archivos de contexto
```

---

## ✅ CHECKLIST PARA NUEVO CHAT

- [ ] Cargar `REFERENCIA_RAPIDA.md`
- [ ] Cargar contexto completo según tarea
- [ ] Confirmar con IA que entendió la arquitectura
- [ ] Mencionar tecnologías clave (Django, DRF, Clean Arch, DDD)
- [ ] Indicar la tarea específica a realizar

---

## 🔄 ACTUALIZACIONES DEL SISTEMA

**Última actualización:** 2025-01-28

**Cambios recientes:**

- ✅ Sin contraseñas temporales (estudiantes recuperan por web)
- ✅ Envío de enlaces con creación/actualización automática
- ✅ Generación de PDF con plantilla personalizable
- ✅ Envío asíncrono con Celery
- ✅ Paginación personalizada

---

## 💡 TIPS PARA IA

1. **Siempre menciona que usamos Clean Architecture + DDD**
2. **Los modelos están en `domain/entities/`**
3. **Los casos de uso en `application/use_cases/`**
4. **Los serializers en `presentation/serializers/`**
5. **Los views en `presentation/views/`**

---

## 📞 DOCUMENTACIÓN ADICIONAL

Si necesitas más detalles, consulta la carpeta `docs/`:

- `PAYMENT_ORDERS_API_DOCUMENTATION.md` - API completa
- `GUIA_FRONTEND_ENVIO_ENLACE.md` - Frontend
- `EJEMPLO_USO_ENVIO_ENLACE_PAGO.md` - Ejemplos
- Y más...

---

**¡Listo para comenzar! 🚀**

