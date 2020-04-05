import pytest
from wmapi import app


@pytest.mark.asyncio
async def test_create_scan():
    client = app.test_client()
    response = await client.post('/scan', json={'target': "192.168.0.1-20"})
    assert response.status_code == 400

    response = await client.post('/scan', json={'target': ["192.168.0.1-20"]})
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_scans():
    client = app.test_client()
    response = await client.get('/scan')
    assert response.status_code == 200

    created_scans = await response.get_json()
    assert len(created_scans) == 1

    response = await client.get(f'/scan/{list(created_scans.keys())[0]}')
    assert response.status_code == 200
    scan_info = await response.get_json()
    assert len(scan_info.keys()) > 0