import asyncio
import tempfile
import zipfile
import json
import logging
import uuid
import functools
import concurrent.futures
import os
from witnessme.scan import WitnessMeScan
from witnessme.utils import patch_pyppeteer
from quart import Quart, request, jsonify
from quart.logging import default_handler

handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] - %(filename)s: %(funcName)s - %(message)s")
)

quart_app_logger = logging.getLogger('quart.app')
quart_app_logger.removeHandler(default_handler)
quart_app_logger.addHandler(handler)

log = logging.getLogger("witnessme")
log.setLevel(logging.INFO)
log.addHandler(handler)

patch_pyppeteer()

class ActiveScans:
    def __init__(self):
        self.scans = []

    def add(self, scan: WitnessMeScan):
        self.scans.append(scan)

    def get(self, scan_id: uuid.UUID):
        return next(filter(lambda  s: s.id == scan_id, self.scans), {})

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ActiveScans):
            return {
                str(scan.id): {
                    'target': scan.target,
                    'inputs': scan.stats.inputs,
                    'execs': scan.stats.execs,
                    'pending': scan.stats.pending,
                    'done': scan.stats.done
                } for scan in obj.scans
            }

        if isinstance(obj, WitnessMeScan):
            return {
                'target': obj.target,
                'inputs': obj.stats.inputs,
                'execs': obj.stats.execs,
                'pending': obj.stats.pending,
                'done': obj.stats.done
            }

        if isinstance(obj, uuid.UUID):
            return str(obj)

        return super().default(obj)

app = Quart(__name__)
app.config.update({
    'SCANS': ActiveScans()
    #'DATABASE': app.root_path / 'blog.db'
})
app.json_encoder = CustomJSONEncoder

async def zip_scan_folder(tmp_file: tempfile.NamedTemporaryFile,  scan_folder: str):
    app.logger.info(f"Compressing scan folder {scan_folder} to {tmp_file.name}...")
    with zipfile.ZipFile(tmp_file, "w", compresslevel=9, compression=zipfile.ZIP_DEFLATED) as zf:
        for dirname, _, files in os.walk(scan_folder):
            zf.write(dirname)
            for filename in files:
                zf.write(os.path.join(dirname, filename))

@app.route('/scan/', methods=['POST'])
async def start_scan():
    r = await request.get_json()

    if not r.get("target"):
        return {"error": "target is required"}, 400
    
    if not type(r.get("target")) == list:
        return {"error": "target must be an array"}, 400

    scan = WitnessMeScan(**r)
    app.config['SCANS'].add(scan)

    if 'file' in r['target']:
        return {
            "id": scan.id,
            "upload": f"http://127.0.0.0.1:5000/scan/{scan.id}/upload"
        }

    asyncio.create_task(scan.run())
    return {'id': scan.id}

@app.route('/scan/', methods=['GET'])
async def get_scans():
    return jsonify(app.config['SCANS'])

@app.route('/scan/<uuid:scan_id>', methods=['GET'])
async def get_scan_by_id(scan_id):
    return jsonify(app.config['SCANS'].get(scan_id))

@app.route('/scan/<uuid:scan_id>/result', methods=['GET'])
async def get_scan_result(scan_id):
    scan = app.config['SCANS'].get(scan_id)
    if not scan:
        return {"error": "specified scan id does not exist"}
    if not scan.stats.done:
        return {"error": "scan has not finished"}, 400

    loop = asyncio.get_running_loop()
    with tempfile.NamedTemporaryFile() as tmp_file:
        await loop.run_in_executor(
            functools.partial(zip_scan_folder, tmp_file, scan.report_folder)
        )

        async def async_file_reader():
            data_chunk = None
            with open(tmp_file ,"rb") as report:
                data_chunk = report.read(4096)
                while data_chunk is not None:
                    yield data_chunk
                    data_chunk = report.read(4096)

        return async_file_reader(), 200, {'Transfer-Encoding': 'chunked'}

@app.route('/scan/<uuid:scan_id>/upload', methods=['POST'])
async def upload_scan_target_file(scan_id):
    return {}

if __name__ == '__main__':
    app.run(debug=True)
