import logging

from apps.core.infrastructure.inbox.repository.inbox_repository import InboxRepository

logger = logging.getLogger(__name__)

class ProcessPayPal:

    def process(self, payload):
        event_type = payload.get('event_type')
        event_id = payload.get('id')
        resource = payload.get('resource', {})
        
        # Extraer payment_order_id según el tipo de evento
        payment_order_id = self._extract_payment_order_id(event_type, resource)

        print(f"payload: {payload}")
        print(f"Procesando evento PayPal: {event_type}")
        print(f"payment_order_id: {payment_order_id}")

        # Extraer nombre del pagador para CHECKOUT.ORDER.APPROVED
        payer_name = None
        if event_type == 'CHECKOUT.ORDER.APPROVED':
            payer_name = self._extract_payer_name(resource)

        logger.info(f"payment_order_id: {payment_order_id}")
        if payment_order_id:
            InboxRepository().save_event(
                provider="paypal",
                event_type=event_type,
                event_id=event_id,
                payment_order_id=int(payment_order_id),
                payload=payload,
                payer_name=payer_name
            )

    @staticmethod
    def _extract_payment_order_id(event_type: str, resource: dict) -> str | None:
        """
        Extrae el payment_order_id del resource según el tipo de evento.
        
        - CHECKOUT.ORDER.APPROVED: resource.purchase_units[0].custom_id
        - PAYMENT.CAPTURE.COMPLETED: resource.custom_id
        
        Args:
            event_type: Tipo de evento de PayPal
            resource: Diccionario con los datos del resource
            
        Returns:
            str: payment_order_id o None si no se encuentra
        """
        try:
            if event_type == 'CHECKOUT.ORDER.APPROVED':
                # Para ORDER.APPROVED, el custom_id está en purchase_units
                purchase_units = resource.get('purchase_units', [])
                if purchase_units and len(purchase_units) > 0:
                    custom_id = purchase_units[0].get('custom_id')
                    if custom_id:
                        logger.info(f"payment_order_id extraído de purchase_units: {custom_id}")
                        return custom_id
            else:
                # Para CAPTURE.COMPLETED y otros eventos, está directamente en resource
                custom_id = resource.get('custom_id')
                if custom_id:
                    logger.info(f"payment_order_id extraído de resource: {custom_id}")
                    return custom_id
                    
            logger.warning(f"No se pudo extraer payment_order_id del evento {event_type}")
            return None
            
        except Exception as e:
            logger.error(f"Error al extraer payment_order_id: {str(e)}")
            return None

    @staticmethod
    def _extract_payer_name(resource: dict) -> str | None:
        """
        Extrae el nombre del pagador del resource de PayPal.
        
        Intenta obtener el nombre de diferentes ubicaciones:
        1. purchase_units[0].shipping.name.full_name
        2. payer.name.given_name + payer.name.surname
        
        Args:
            resource: Diccionario con los datos del resource de PayPal
            
        Returns:
            str: Nombre completo del pagador o None si no se encuentra
        """
        try:
            # Opción 1: purchase_units[0].shipping.name.full_name
            purchase_units = resource.get('purchase_units', [])
            if purchase_units and len(purchase_units) > 0:
                shipping = purchase_units[0].get('shipping', {})
                name_data = shipping.get('name', {})
                payer_name = name_data.get('full_name')
                
                if payer_name:
                    logger.info(f"Nombre del pagador extraído de shipping: {payer_name}")
                    return payer_name
            
            # Opción 2: payer.name (si existe)
            payer = resource.get('payer', {})
            payer_name_data = payer.get('name', {})
            given_name = payer_name_data.get('given_name', '')
            surname = payer_name_data.get('surname', '')
            
            if given_name or surname:
                payer_name = f"{given_name} {surname}".strip()
                logger.info(f"Nombre del pagador extraído de payer: {payer_name}")
                return payer_name
                
        except Exception as e:
            logger.warning(f"No se pudo extraer el nombre del pagador: {str(e)}")
        
        return None

