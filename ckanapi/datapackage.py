import os
import requests

from ckan_datapackage_tools.converter import dataset_to_datapackage

from ckanapi.cli.utils import pretty_json

DL_CHUNK_SIZE = 100 * 1024


def create_resource(resource, datapackage_dir, stderr):
    # Resources can have multiple sources with the same name, or names with
    # filesystem-unfriendly characters, or URLs with a trailing slash, or
    # multiple URLs with the same final path component, so we're just going to
    # name all downloads using the resource's UID.
    path = os.path.join('data', resource['id'])

    try:
        r = requests.get(resource['url'], stream=True)
        with open(os.path.join(datapackage_dir, path), 'wb') as f:
            for chunk in r.iter_content(chunk_size=DL_CHUNK_SIZE):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
        return dict(resource, path=path)
    except requests.ConnectionError:
        stderr.write('URL {url} refused connection. The resource will not be downloaded\n'.format(url=resource['url']))
    except requests.exceptions.RequestException as e:
        stderr.write(str(e.args[0]) if len(e.args) > 0 else '')
        stderr.write('\n')
    except Exception as e:
        stderr.write(str(e.args[0]) if len(e.args) > 0 else '')
    return resource


def create_datapackage(record, base_path, stderr):
    # TODO: how are we going to handle which resources to
    # leave alone? They're very inconsistent in some instances
    # And I can't imagine anyone wants to download a copy
    # of, for example, the API base endpoint
    resource_formats_to_ignore = ['API', 'api']
    dataset_name = record.get('name', '')

    datapackage_dir = os.path.join(base_path, dataset_name)
    os.makedirs(os.path.join(datapackage_dir, 'data'))

    resources = [(resource if resource['format'] in resource_formats_to_ignore else create_resource(resource, datapackage_dir, stderr)) for resource in record.get('resources', [])]

    json_path = os.path.join(datapackage_dir, 'datapackage.json')
    with open(json_path, 'wb') as out:
        out.write(pretty_json(dataset_to_datapackage(dict(record, resources=resources))))
