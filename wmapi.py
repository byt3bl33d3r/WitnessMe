import asyncio
import zipfile
import json
import logging
import uuid
import functools
import concurrent.futures
import os
from witnessme.scan import WitnessMeScan
from witnessme.utils import patch_pyppeteer, gen_random_string
from quart import Quart, request, jsonify, Response
from quart.logging import LocalQueueHandler

handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(filename)s: %(funcName)s - %(message)s")
)

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
        return next(filter(lambda  s: s.id == scan_id, self.scans), None)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ActiveScans):
            return {
                str(scan.id): {
                    'inputs': scan.stats.inputs,
                    'execs': scan.stats.execs,
                    'pending': scan.stats.pending,
                    'started': scan.stats.started,
                    'done': scan.stats.done,
                    'target': len(scan.target)
                } for scan in obj.scans
            }

        if isinstance(obj, WitnessMeScan):
            return {
                'id': str(obj.id),
                'target': obj.target,
                'ports': obj.ports,
                'timeout': obj.timeout,
                'threads': obj.threads,
                'report_folder': obj.report_folder,
                'inputs': obj.stats.inputs,
                'execs': obj.stats.execs,
                'pending': obj.stats.pending,
                'done': obj.stats.done,
                'started': obj.stats.started
            }

        if isinstance(obj, uuid.UUID):
            return str(obj)

        return super().default(obj)

app = Quart(__name__)
app.url_map.strict_slashes = False
app.json_encoder = CustomJSONEncoder
app.config.update({
    'SCANS': ActiveScans()
    #'DATABASE': app.root_path / 'wmapi.db'
})

def zip_scan_folder(scan_folder: str):
    zip_file_path = f"{scan_folder}.zip"

    app.logger.info(f"Compressing scan folder {scan_folder} to {zip_file_path}...")
    with zipfile.ZipFile(zip_file_path, "w", compresslevel=9, compression=zipfile.ZIP_DEFLATED) as zf:
        for dirname, _, files in os.walk(scan_folder):
            zf.write(dirname)
            for filename in files:
                zf.write(os.path.join(dirname, filename))

    return zip_file_path

@app.route('/scan', methods=['POST'])
async def create_scan():
    r = await request.get_json()

    if not r.get("target"):
        return {"error": "target is required"}, 400
    
    if type(r.get("target")) != list:
        return {"error": "target must be an array"}, 400

    app.logger.info("Testing")
    r['target'] = list(
        map(lambda t: f"{t}:{gen_random_string()}" if t.startswith("file:") else t, r['target'])
    )

    scan = WitnessMeScan(**r)
    app.config['SCANS'].add(scan)

    file_targets = list(filter(lambda t: t.startswith('file:'), r['target']))
    if file_targets:
        return {
            "id": scan.id,
            "upload": {
                ft.split(':')[1]: f"{request.url_root}{scan.id}/upload/{ft.split(':')[2]}" 
                for ft in file_targets
            }
        }

    return {'id': scan.id}

@app.route('/scan', methods=['GET'])
async def get_scans():
    return jsonify(app.config['SCANS'])

@app.route('/scan/<uuid:scan_id>', methods=['GET'])
async def get_scan_by_id(scan_id):
    scan = app.config['SCANS'].get(scan_id)
    if not scan:
        return {"error": "specified scan id does not exist"}, 400
    return jsonify(scan)

@app.route('/scan/<uuid:scan_id>/start', methods=['GET'])
async def start_scan(scan_id):
    scan = app.config['SCANS'].get(scan_id)
    if not scan:
        return {"error": "specified scan id does not exist"}, 400

    asyncio.create_task(scan.start())
    return '', 200

@app.route('/scan/<uuid:scan_id>/stop', methods=['GET'])
async def stop_scan(scan_id):
    scan = app.config['SCANS'].get(scan_id)
    if not scan:
        return {"error": "specified scan id does not exist"}, 400

    asyncio.create_task(scan.stop())
    return '', 200

@app.route('/scan/<uuid:scan_id>/result', methods=['GET'])
async def get_scan_result(scan_id):
    scan = app.config['SCANS'].get(scan_id)
    if not scan:
        return {"error": "specified scan id does not exist"}, 400
    if not scan.stats.done:
        return {"error": "scan has not finished"}, 400

    loop = asyncio.get_running_loop()
    zip_file = await loop.run_in_executor(
            None, functools.partial(zip_scan_folder, scan.report_folder)
        )

    async def async_file_reader():
        with open(zip_file, 'rb') as report_zip:
            data_chunk = report_zip.read(4096)
            while len(data_chunk) > 0:
                yield data_chunk
                data_chunk = report_zip.read(4096)

    return Response(async_file_reader(), status=200, mimetype="application/zip")

@app.route('/scan/<uuid:scan_id>/upload/<string:file_id>', methods=['POST'])
async def upload_scan_target_file(scan_id, file_id):
    scan = app.config['SCANS'].get(scan_id)
    if not scan:
        return {"error": "specified scan id does not exist"}, 400

    for i, t in enumerate(scan.target):
        if t.startswith("file:"):
            _,f_name,f_id = t.split(':')
            if f_id == file_id:
                with open(f_name, 'wb') as uploaded_scan_file:
                    async for data in request.body:
                        uploaded_scan_file.write(data)
                    scan.target.append(upload_scan_target_file.path)
                scan.target[i] = f_name
                return '', 200

if __name__ == '__main__':
    app.run(debug=True)
