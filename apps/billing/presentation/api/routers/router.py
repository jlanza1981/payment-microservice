from ninja import Router

from apps.core.infrastructure.security.auth_bearer import AuthBearer

router = Router(tags=["Payment Orders"], auth=AuthBearer())
