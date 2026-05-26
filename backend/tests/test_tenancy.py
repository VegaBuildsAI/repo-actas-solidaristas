import pytest
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient
from fastapi import FastAPI


def _make_app_with_middleware():
    from actas.tenancy.middleware import TenantMiddleware

    app = FastAPI()
    app.add_middleware(TenantMiddleware)

    @app.get("/test-org")
    async def test_org(request: Request):
        return {"org_id": request.state.org_id}

    @app.get("/healthz")
    async def healthz(request: Request):
        return {"org_id": request.state.org_id}

    return app


def test_org_id_extracted_from_header():
    app = _make_app_with_middleware()
    client = TestClient(app)
    response = client.get("/test-org", headers={"X-Organization-Id": "some-uuid"})
    assert response.status_code == 200
    assert response.json()["org_id"] == "some-uuid"


def test_org_id_none_when_header_absent():
    app = _make_app_with_middleware()
    client = TestClient(app)
    response = client.get("/test-org")
    assert response.status_code == 200
    assert response.json()["org_id"] is None


def test_exempt_path_has_no_org_id():
    app = _make_app_with_middleware()
    client = TestClient(app)
    response = client.get("/healthz", headers={"X-Organization-Id": "should-be-ignored"})
    assert response.status_code == 200
    assert response.json()["org_id"] is None
