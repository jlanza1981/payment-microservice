from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class EmailAttachment:
    """
    Representa un adjunto para un correo electrónico.
    """
    filename: str
    content: bytes
    mimetype: str = "application/octet-stream"


@dataclass
class EmailData:
    """
    Esta entidad encapsula toda la información necesaria para enviar
    un email, incluyendo destinatarios, contenido, adjuntos, etc.
    """
    subject: str
    recipients: List[str]
    template_name: Optional[str] = None
    template_context: Optional[Dict[str, Any]] = None
    body: Optional[str] = None
    attachments: Optional[List[EmailAttachment]] = None
    from_email: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None

    def __post_init__(self):
        """Valida que los datos del email sean correctos."""
        if not self.body and not self.template_name:
            raise ValueError("Debe proporcionar 'body' o 'template_name'")
        if not self.recipients:
            raise ValueError("Debe proporcionar al menos un destinatario")