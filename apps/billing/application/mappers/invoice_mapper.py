from typing import Dict, Any, List

from apps.billing.application.commands import InvoiceDetailCommand


class InvoiceMapper:

    @staticmethod
    def prepare_invoice_data(data: Dict[str, Any]) -> Dict[str, Any]:

        invoice_details: List[InvoiceDetailCommand] = []

        program_data = data.get("program_data")
        unit_price_from_program = None

        if program_data:
            unit_price_from_program = (
                program_data.get("unit_price")
                if isinstance(program_data, dict)
                else getattr(program_data, "unit_price", None)
            )

        for c in data.get("payment_order_details", []):

            if isinstance(c, dict):
                payment_concept_id = c.get("payment_concept")
                description = c.get("description", c.get("payment_concept_name", ""))
                quantity = c.get("quantity", 1)
                amount = c.get("amount", 0)
                discount_amount = c.get("discount_amount", 0)
            else:
                payment_concept_id = getattr(c, "payment_concept", None)
                description = getattr(c, "description", getattr(c, "payment_concept_name", ""))
                quantity = getattr(c, "quantity", 1)
                amount = getattr(c, "amount", 0)
                discount_amount = getattr(c, "discount_amount", 0)

            unit_price = unit_price_from_program or amount

            invoice_detail = InvoiceDetailCommand(
                payment_concept=payment_concept_id,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                discount=discount_amount
            )

            invoice_details.append(invoice_detail)

        payload_invoice = {
            "user": data.get("student"),
            "advisor": data.get("advisor"),
            "payment_order": data.get("id"),
            "invoice_details": invoice_details,
            "status": data.get("status"),
            "currency": data.get("currency"),
        }

        if "notes" in data:
            payload_invoice["notes"] = data.get("notes", "")

        return payload_invoice