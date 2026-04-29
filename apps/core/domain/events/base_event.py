"""
Base class for Domain Events.
Todos los eventos de dominio deben heredar de esta clase.
"""
from datetime import datetime
from typing import Dict, Any


class DomainEvent:
    """
    Clase base para eventos de dominio.

    Los eventos de dominio representan algo que ha sucedido en el dominio
    y que puede ser de interés para otros bounded contexts.

    Siguiendo DDD, los eventos deben:
    - Ser inmutables (solo lectura)
    - Tener un timestamp
    - Describir algo que ya ocurrió (pasado: "PaymentCaptured", no "CapturePayment")
    """

    def __init__(self):
        self.occurred_at = datetime.now()

    @property
    def event_type(self) -> str:
        """Retorna el tipo de evento (nombre de la clase)"""
        return self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializa el evento a diccionario.
        Útil para logging, debugging y Event Store.
        """
        return {
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            **self._get_event_data()
        }

    def _get_event_data(self) -> Dict[str, Any]:
        """
        Override en clases hijas para proporcionar datos específicos del evento.
        Por defecto retorna todos los atributos públicos.
        """
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith('_') and key != 'occurred_at'
        }

    def __str__(self):
        return f"{self.event_type} at {self.occurred_at}"

    def __repr__(self):
        return f"<{self.event_type}({self.to_dict()})>"

