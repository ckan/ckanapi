ckanapi
=======

This module a thin wrapper around the CKAN's action API.
It may be used from within a plugin or separate from CKAN entirely.

Making an API Request::

    import ckanapi
    import pprint
    demo = ckanapi.RemoteCKAN('http://demo.ckan.org')
    groups = demo.action.group_list(id='data-explorer')
    pprint.pprint(groups)

result::

    {u'help': u'Return a list of the names of the site\'s groups.\n\n    :param order_by: the field to sort the list by, must be ``\'name\'`` or\n      ``\'packages\'`` (optional, default: ``\'name\'``) Deprecated use sort.\n    :type order_by: string\n    :param sort: sorting of the search results.  Optional.  Default:\n        "name asc" string of field name and sort-order. The allowed fields are\n        \'name\' and \'packages\'\n    :type sort: string\n    :param groups: a list of names of the groups to return, if given only\n        groups whose names are in this list will be returned (optional)\n    :type groups: list of strings\n    :param all_fields: return full group dictionaries instead of  just names\n        (optional, default: ``False``)\n    :type all_fields: boolean\n\n    :rtype: list of strings\n\n    ',
     u'result': [u'data-explorer',
                 u'example-group',
                 u'geo-examples',
                 u'skeenawild'],
     u'success': True}




