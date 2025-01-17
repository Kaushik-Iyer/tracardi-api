import re
from typing import Optional

from tracardi.config import tracardi
from tracardi.context import Context, ServerContext
from starlette.types import ASGIApp, Receive, Scope, Send
from app.api.auth.user_db import token2user
from tracardi.service.license import License

if License.has_license():
    from com_tracardi.service.tenant_manager import get_tenant_name_from_scope
else:
    from tracardi.service.tenant_manager import get_tenant_name_from_scope


def _get_header_value(scope, key) -> Optional[str]:
    headers = scope.get('headers', None)

    if headers:
        for header, value in headers:
            if header.decode() == key:
                return value.decode()

    return None


def _get_context_object(scope) -> Context:
    # Default context comes from evn variable PRODUCTION
    production = tracardi.version.production

    # If env variable set to PRODUCTION=yes there is no way to change it.
    # Production means production. Otherwise the context can be changed
    # form outside.

    tenant, hostname = get_tenant_name_from_scope(scope)

    if tenant is None:
        raise OSError(f"Can not find tenant for this URL. Reason: Tenant name can not be shorted then 3 letters "
                      f"and must not contain numbers. Your system is set-up to support multi-tenancy "
                      f"that means access only through domain name is available. Scope: {scope}")

    if not production:  # Staging as default

        context = _get_header_value(scope, "x-context")
        # if has some value
        if context and context in ['production', 'staging']:
            production = context.lower() == 'production'

    return Context(production=production, user=None, tenant=tenant, host=hostname)


class ContextRequestMiddleware:
    def __init__(
            self,
            app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ["http", "websocket", "https"]:
            await self.app(scope, receive, send)
            return

        context_object = _get_context_object(scope)
        with ServerContext(context_object) as cm:
            if scope.get('method', None) != "options":
                token = _get_header_value(scope, 'authorization')
                if token:
                    _, token = token.split()
                    user = token2user.get(token)
                    # This is dangerous mutation. Never do this in other places.
                    cm.get_context().user = user

            await self.app(scope, receive, send)
