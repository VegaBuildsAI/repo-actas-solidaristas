from fastapi import Depends, HTTPException, Request, status

from actas.deps import get_current_user


def require_org(request: Request, user=Depends(get_current_user)) -> str:
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header X-Organization-Id requerido",
        )
    return org_id
