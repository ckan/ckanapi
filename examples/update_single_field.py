#!/usr/bin/python3
from ckanapi import RemoteCKAN
server_url='https://ckan.my-domain.com'
token = 'very_secret_token'
selected_id = '0f800659-16d2-449a-923f-a6d04f8edbb9'
with RemoteCKAN(server_url, apikey=token) as ckan:
    ckan.action.package_patch(id=selected_id, title='New title')