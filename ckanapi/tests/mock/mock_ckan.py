import json
import cgi
import csv
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


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
        fs = cgi.FieldStorage(
            fp=environ['wsgi.input'],
            environ=environ,
            keep_blank_values=True,
            )
        upload_data = fs.getvalue('upload').decode('utf-8').splitlines()
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
                'option': fs.getvalue('option'),
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

