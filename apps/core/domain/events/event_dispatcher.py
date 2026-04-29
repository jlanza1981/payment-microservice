"""
Event Dispatcher - Sistema de despacho de eventos de dominio.
Implementación pura sin dependencia de frameworks externos.
"""
import logging
from typing import Callable, List, Dict, Type, TypeVar
from .base_event import DomainEvent

logger = logging.getLogger(__name__)

# TypeVar para permitir handlers específicos de subclases
TEvent = TypeVar('TEvent', bound=DomainEvent)


class EventDispatcher:
    """
    Dispatcher centralizado para eventos de dominio.

    Permite registrar handlers para tipos específicos de eventos
    y despacharlos de forma desacoplada entre bounded contexts.

    Ejemplo de uso:

    # 1. Definir evento
    class PaymentCaptured(DomainEvent):
        def __init__(self, invoice_id: int):
            super().__init__()
            self.invoice_id = invoice_id

    # 2. Registrar handler
    def on_payment_captured(event: PaymentCaptured):
        print(f"Pago capturado para factura {event.invoice_id}")

    EventDispatcher.register(PaymentCaptured, on_payment_captured)

    # 3. Despachar evento
    event = PaymentCaptured(invoice_id=123)
    EventDispatcher.dispatch(event)
    """

    # Almacén de handlers: {EventClass: [handler1, handler2, ...]}
    _handlers: Dict[Type[DomainEvent], List[Callable]] = {}

    @classmethod
    def register(cls, event_class: Type[TEvent], handler: Callable[[TEvent], None]) -> None:
        """
        Registra un handler para un tipo específico de evento.

        Args:
            event_class: Clase del evento (ej: PaymentCaptured)
            handler: Función que procesará el evento
        """
        if event_class not in cls._handlers:
            cls._handlers[event_class] = []

        if handler not in cls._handlers[event_class]:
            cls._handlers[event_class].append(handler)
            logger.info(
                f"Handler registrado: {handler.__name__} para evento {event_class.__name__}"
            )
        else:
            logger.warning(
                f"Handler {handler.__name__} ya estaba registrado para {event_class.__name__}"
            )

    @classmethod
    def unregister(cls, event_class: Type[DomainEvent], handler: Callable):
        """
        Desregistra un handler específico.
        Útil para testing o reconfiguración en runtime.
        """
        if event_class in cls._handlers and handler in cls._handlers[event_class]:
            cls._handlers[event_class].remove(handler)
            logger.info(
                f"Handler desregistrado: {handler.__name__} para evento {event_class.__name__}"
            )

    @classmethod
    def dispatch(cls, event: DomainEvent):
        """
        Despacha un evento a todos los handlers registrados.

        Args:
            event: Instancia del evento a despachar

        Nota: Los errores en handlers individuales se capturan y loggean
        pero no detienen el procesamiento de otros handlers.
        """
        event_class = event.__class__
        handlers = cls._handlers.get(event_class, [])

        if not handlers:
            logger.debug(
                f"No hay handlers registrados para {event_class.__name__}"
            )
            return

        logger.info(
            f"Despachando evento {event.event_type} a {len(handlers)} handler(s)"
        )

        for handler in handlers:
            try:
                logger.debug(f"Ejecutando handler: {handler.__name__}")
                handler(event)
                logger.debug(f"Handler {handler.__name__} ejecutado exitosamente")

            except Exception as e:
                logger.error(
                    f"Error en handler {handler.__name__} para evento {event.event_type}: {str(e)}",
                    exc_info=True
                )
                # No re-lanzamos la excepción para que otros handlers sigan ejecutándose

    @classmethod
    def clear_all_handlers(cls):
        """
        Limpia todos los handlers registrados.
        Útil principalmente para testing.
        """
        cls._handlers.clear()
        logger.info("Todos los handlers han sido limpiados")

    @classmethod
    def get_registered_handlers(cls, event_class: Type[DomainEvent] = None) -> Dict:
        """
        Retorna los handlers registrados.

        Args:
            event_class: Si se proporciona, retorna solo handlers de ese evento.
                        Si es None, retorna todos.

        Returns:
            Dict con los handlers registrados
        """
        if event_class:
            return {event_class: cls._handlers.get(event_class, [])}
        return cls._handlers.copy()