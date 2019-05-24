import os
import requests
import json

import six
import slugify

from ckanapi.cli.utils import pretty_json
from ckanapi.errors import CKANAPIError

DL_CHUNK_SIZE = 100 * 1024
DATAPACKAGE_TYPES = {  # map datastore types to datapackage types
    'text': 'string',
    'numeric': 'number',
    'timestamp': 'datetime',
}


def create_resource(resource, filename, datapackage_dir, stderr):
    '''Downloads the resource['url'] to disk.
    '''
    path = os.path.join('data', filename)

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

    # filter out some resources
    ckan_resources = []
    for resource in record.get('resources', []):
        if resource['format'] in resource_formats_to_ignore:
            continue
        ckan_resources.append(resource)
    dataset = dict(record, resources=ckan_resources)

    # get the datapackage (metadata)
    datapackage = dataset_to_datapackage(dataset)

    for cres, dres in zip(ckan_resources, datapackage.get('resources', [])):
        filename = resource_filename(dres)

        # download the resource
        cres = \
            create_resource(resource, filename, datapackage_dir, stderr)
        dres['path'] = 'data/' + filename

        populate_schema_from_datastore(cres, dres)

    json_path = os.path.join(datapackage_dir, 'datapackage.json')
    with open(json_path, 'wb') as out:
        out.write(pretty_json(datapackage))

    return datapackage_dir, datapackage, json_path


def resource_filename(dres):
    # prefer resource names from datapackage metadata, because those have been
    # made unique
    name = dres['name']
    ext = slugify.slugify(dres['format'])
    if name.endswith(ext):
        name = name[:-len(ext)]
    return name + '.' + ext


def populate_schema_from_datastore(cres, dres):
    """
    populate the data schema in a datapackage resource, from the Datastore.
    This info must already be added to the cres using
    'populate_datastore_res_fields'

    :param cres: CKAN resource dict
    :param dres: datapackage.json style resource dict, for the same resource as
                 the cres
    """
    # convert datastore data dictionary to datapackage schema
    if 'schema' not in dres and 'datastore_fields' in cres:
        fields = []
        for f in cres['datastore_fields']:
            if f['id'] == '_id':
                continue
            df = {'name': f['id']}
            dtyp = DATAPACKAGE_TYPES.get(f['type'])
            if dtyp:
                df['type'] = dtyp
            dtit = f.get('info', {}).get('label', '')
            if dtit:
                df['title'] = dtit
            ddesc = f.get('info', {}).get('notes', '')
            if ddesc:
                df['description'] = ddesc
            fields.append(df)
        dres['schema'] = {'fields': fields}

def populate_datastore_res_fields(ckan, res):
    """
    update resource dict in-place with datastore_fields values
    in every resource with datastore active using ckan
    LocalCKAN/RemoteCKAN instance
    """
    if not res.get('datastore_active', False):
        return
    try:
        ds = ckan.call_action('datastore_search', {
            'resource_id': res['id'],
            'limit':0})
    except CKANAPIError:
        pass
    res['datastore_fields'] = ds['fields']


# functions below are from https://github.com/frictionlessdata/ckan-datapackage-tools
# commit c87e07d0d0
# we can't import and use until dependency issue is resolved:
# https://github.com/frictionlessdata/ckan-datapackage-tools/issues/11

def _convert_to_datapackage_resource(resource_dict):
    '''Convert a CKAN resource dict into a Data Package resource dict.

    from https://github.com/frictionlessdata/ckan-datapackage-tools
    '''
    resource = {}

    if resource_dict.get('url'):
        resource['path'] = resource_dict['url']
    # TODO: DataStore only resources?

    if resource_dict.get('description'):
        resource['description'] = resource_dict['description']

    if resource_dict.get('format'):
        resource['format'] = resource_dict['format']

    if resource_dict.get('hash'):
        resource['hash'] = resource_dict['hash']

    if resource_dict.get('name'):
        resource['name'] = slugify.slugify(resource_dict['name']).lower()
        resource['title'] = resource_dict['name']
    else:
        resource['name'] = resource_dict['id']

    schema = resource_dict.get('schema')
    if isinstance(schema, six.string_types):
        try:
            resource['schema'] = json.loads(schema)
        except ValueError:
            # Assume it's a path or URL
            resource['schema'] = schema
    elif isinstance(schema, dict):
        resource['schema'] = schema

    return resource


def dataset_to_datapackage(dataset_dict):
    '''Convert the given CKAN dataset dict into a Data Package dict.

    :returns: the datapackage dict
    :rtype: dict

    '''
    PARSERS = [
        _rename_dict_key('title', 'title'),
        _rename_dict_key('version', 'version'),
        _parse_ckan_url,
        _parse_notes,
        _parse_license,
        _parse_author_and_source,
        _parse_maintainer,
        _parse_tags,
        _parse_extras,
    ]
    dp = {
        'name': dataset_dict['name']
    }

    for parser in PARSERS:
        dp.update(parser(dataset_dict))

    resources = dataset_dict.get('resources')
    if resources:
        dp['resources'] = [_convert_to_datapackage_resource(r)
                           for r in resources]

    # Ensure unique resource names
    names = {}
    for resource in dp.get('resources', []):
        if resource['name'] in names.keys():
            old_resource_name = resource['name']
            resource['name'] = resource['name'] + str(names[old_resource_name])
            names[old_resource_name] += 1
        else:
            names[resource['name']] = 0

    return dp


def _rename_dict_key(original_key, destination_key):
    def _parser(the_dict):
        result = {}

        if the_dict.get(original_key):
            result[destination_key] = the_dict[original_key]

        return result
    return _parser


def _parse_ckan_url(dataset_dict):
    result = {}

    if dataset_dict.get('ckan_url'):
        result['homepage'] = dataset_dict['ckan_url']

    return result


def _parse_notes(dataset_dict):
    result = {}

    if dataset_dict.get('notes'):
        result['description'] = dataset_dict['notes']

    return result


def _parse_license(dataset_dict):
    result = {}
    license = {}

    if dataset_dict.get('license_id'):
        license['type'] = dataset_dict['license_id']
    if dataset_dict.get('license_title'):
        license['title'] = dataset_dict['license_title']
    if dataset_dict.get('license_url'):
        license['url'] = dataset_dict['license_url']

    if license:
        result['license'] = license

    return result


def _parse_author_and_source(dataset_dict):
    result = {}
    source = {}

    if dataset_dict.get('author'):
        source['name'] = dataset_dict['author']
    if dataset_dict.get('author_email'):
        source['email'] = dataset_dict['author_email']
    if dataset_dict.get('url'):
        source['web'] = dataset_dict['url']

    if source:
        result['sources'] = [source]

    return result


def _parse_maintainer(dataset_dict):
    result = {}
    author = {}

    if dataset_dict.get('maintainer'):
        author['name'] = dataset_dict['maintainer']
    if dataset_dict.get('maintainer_email'):
        author['email'] = dataset_dict['maintainer_email']

    if author:
        result['author'] = author

    return result


def _parse_tags(dataset_dict):
    result = {}

    keywords = [tag['name'] for tag in dataset_dict.get('tags', [])]

    if keywords:
        result['keywords'] = keywords

    return result


def _parse_extras(dataset_dict):
    result = {}

    extras = [[extra['key'], extra['value']] for extra
              in dataset_dict.get('extras', [])]

    for extra in extras:
        try:
            extra[1] = json.loads(extra[1])
        except (ValueError, TypeError):
            pass

    if extras:
        result['extras'] = dict(extras)

    return result
