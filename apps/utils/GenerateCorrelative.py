from django.db import transaction
from django.utils import timezone

from apps.core.models import LetrasCorrelativos


@transaction.atomic
def generate_correlative(document_type, prefix):
    current_year = timezone.now().year
    correlative, _ = LetrasCorrelativos.objects.select_for_update().get_or_create(
        document_type=document_type,
        letra=prefix,
        year=current_year,
        defaults={'last_number': 0}
    )
    correlative.last_number += 1
    correlative.save()

    prefix = correlative.letra or ''
    return f"{prefix}-{current_year}-{str(correlative.last_number).zfill(6)}"
