import json
import csv
from io import StringIO
from werkzeug.formparser import parse_form_data
from wsgiref.simple_server import make_server


def mock_ckan(environ, start_response):
    status = '200 OK'
    headers = [
        ('Content-type', 'application/json;charset=utf-8'),
        ]
    if environ['PATH_INFO'] == '/api/action/site_read':
        start_response(status, headers)
        return [json.dumps(True).encode('utf-8')]
    if environ['PATH_INFO'] == '/api/action/organization_list':
        start_response(status, headers)
        return [json.dumps({
            "help": "none",
            "success": True,
            "result": ["aa", "bb", "cc"]
            }).encode('utf-8')]
    if environ['PATH_INFO'] == '/api/action/test_echo_user_agent':
        start_response(status, headers)
        return [json.dumps({
            "help": "none",
            "success": True,
            "result": environ['HTTP_USER_AGENT']
            }).encode('utf-8')]
    if environ['PATH_INFO'] == '/api/action/test_echo_content_type':
        start_response(status, headers)
        return [json.dumps({
            "help": "none",
            "success": True,
            "result": environ['CONTENT_TYPE']
            }).encode('utf-8')]
    if environ['PATH_INFO'] == '/api/action/test_upload':
        _, form, files = parse_form_data(environ)
        upload_data = files['upload'].stream.read().decode('utf-8').splitlines()
        csv_file = StringIO()
        writer = csv.writer(csv_file)
        for line_data in upload_data:
            row_data = line_data.split(',')
            writer.writerow(row_data)
        csv_file.seek(0)
        records = list(csv.reader(csv_file))
        start_response(status, headers)
        return [json.dumps({
            "help": "none",
            "success": True,
            "result": {
                'option': form['option'],
                'last_row': records[-1],
                },
            }).encode('utf-8')]
    if environ['PATH_INFO'].startswith('/api/action/'):
        start_response(status, headers)
        return [json.dumps({
            "help": "none",
            "success": False,
            "error": {'__type': 'Not Found Error'},
            }).encode('utf-8')]
    start_response('404 Not Found', headers)
    return []

httpd = make_server('localhost', 8901, mock_ckan)
httpd.serve_forever()

