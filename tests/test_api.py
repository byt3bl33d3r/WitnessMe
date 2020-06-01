import pytest
from fastapi.testclient import TestClient
from wmapi import app

client = TestClient(app)


def test_create_scan():
    response = client.post("/scan/", json={"target": "192.168.0.1-20"})
    assert response.status_code == 422

    response = client.post("/scan/", json={"target": ["192.168.0.1-20"]})
    assert response.status_code == 200


def test_get_scans():
    response = client.get("/scan/")
    created_scans = response.json()
    assert response.status_code == 200
    assert len(created_scans) == 1


def test_get_scan_by_id():
    response = client.get("/scan/")
    created_scans = response.json()

    response = client.get(f"/scan/{list(created_scans.keys())[0]}")
    scan_info = response.json()

    assert response.status_code == 200
    assert len(scan_info.keys()) > 0
