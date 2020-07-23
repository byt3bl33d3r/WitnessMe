import pytest
import shutil
import pathlib
from time import sleep
from fastapi.testclient import TestClient
from witnessme.console.wmapi import app

client = TestClient(app)


def test_create_scan():
    response = client.post("/screenshot/", json={"target": "192.168.0.1-20"})
    assert response.status_code == 422

    response = client.post(
        "/screenshot/",
        json={
            "target": ["192.168.0.1-20", "https://google.com"],
            "ports": [7373],
            "threads": 10,
            "timeout": 35,
        },
    )
    assert response.status_code == 200


def test_get_scans():
    response = client.get("/screenshot/")
    created_scans = response.json()
    assert response.status_code == 200
    assert len(created_scans) == 1


def test_get_scan_by_id():
    response = client.get("/screenshot/")
    created_scans = response.json()

    response = client.get(f"/screenshot/{list(created_scans.keys())[0]}")
    scan_info = response.json()

    assert response.status_code == 200
    assert len(scan_info.keys()) > 0


"""
def test_scan(fake_target_file):
    response = client.post("/screenshot/", json={"target": ["https://google.com"], "ports": [443], "threads": 10, "timeout": 10})
    scan = response.json()
    assert response.status_code == 200

    scan_id = scan['id']
    report_folder_path = pathlib.Path(scan['report_folder'])

    try:
        response = client.get(f"/screenshot/{scan_id}/start")
        assert response.status_code == 200

        response = client.get(f"/screenshot/{scan_id}")
        assert response.status_code == 200
        assert response.json()['state'] == 'started'

        sleep(6)

        response = client.get(f"/screenshot/{scan_id}/stop")
        assert response.status_code == 200

        response = client.get(f"/screenshot/{scan_id}")
        assert response.status_code == 200
        assert response.json()['state'] == 'stopped'
    finally:
        shutil.rmtree(report_folder_path.absolute(), ignore_errors=True)
"""
