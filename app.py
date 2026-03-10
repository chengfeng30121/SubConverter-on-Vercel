#!/usr/bin/python3
import os
import sys
import subprocess
import threading
import time
from flask import Flask, request, Response
import requests
from urllib.parse import quote

app = Flask(__name__)

def check_and_run_subconverter():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if sys.platform == "win32":
        exe_name = "subconverter.exe"
        os.system(f"taskkill /f /im {exe_name}")
    else:
        exe_name = "subconverter"
        os.system(f"killall -9 {exe_name}")
    exe_path = os.path.join(script_dir, exe_name)
    if not os.path.exists(exe_path):
        print(f"Error: {exe_name} not found in {script_dir}")
        sys.exit(1)
    if False:
        try:
            os.chmod(exe_path, 0o755)
        except Exception as e:
            print(f"Error: Failed to set executable permission: {e}")
            sys.exit(1)
    def run():
        while True:
            try:
                process = subprocess.Popen([exe_path])
                process.wait()
            except Exception as e:
                print(f"Subconverter crashed: {e}")
            time.sleep(1)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()

check_and_run_subconverter()

def proxy_request(path):
    query_string = request.query_string.decode('utf-8')
    if query_string:
        encoded_query = '&'.join(
            f"{key}={quote(value, safe='')}" 
            for key, value in request.args.items(multi=True)
        )
        url = f"http://127.0.0.1:25500/{path}?{encoded_query}"
    else:
        url = f"http://127.0.0.1:25500/{path}"
    
    headers = {key: value for key, value in request.headers if key.lower() != 'host'}
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False
        )
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for name, value in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    except requests.exceptions.RequestException as e:
        return Response(f"Proxy error: {e}", 500)

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def catch_all(path):
    return proxy_request(path)
