from typing import Dict, Any


class PaymentMapper:

    @staticmethod
    def prepare_payment_data(invoice_schema: Dict[str, Any], payment_reference_number:str, payment_method:str, status:str, payment_allocation) -> Dict[str, Any]:
        payload_data = {
            'invoice': invoice_schema.get('id'),
            'user': invoice_schema.get('user'),
            'advisor': invoice_schema.get('advisor'),
            'payment_reference_number': payment_reference_number,#f"Exonerated - {invoice.invoice_number}"
            'payment_method': payment_method,
            'status': status,
            'amount': invoice_schema.get('total'),
            'amount_paid': invoice_schema.get('total'),
            'currency': invoice_schema.get('currency'),
            'payer_name': invoice_schema.get('user_name'),
            'payment_terms_conditions': True,
            'payment_allocation': payment_allocation
        }

        return payload_data