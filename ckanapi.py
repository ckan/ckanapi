try:
    from ckan.lib.navl.dictization_functions import DataError
    from ckan.logic import (ParameterError, NotAuthorized, NotFound,
                            ValidationError)
    from ckan.search import SearchQueryError, SearchError

except ImportError:

    # Implement the minimum to be compatible with existing errors
    class CKANAPIError(Exception):
        pass

    class DataError(CKANAPIError):
        def __init__(self, error):
            self.error = error

    class NotAuthorized(CKANAPIError):
        pass

    class NotFound(CKANAPIError):
        pass

    class ValidationError(CKANAPIError):
        def __init__(self, error_dict):
            self.error_dict = error_dict

    class ParameterError(CKANAPIError):
        pass

    class SearchQueryError(CKANAPIError):
        pass

    class SearchError(CKANAPIError):
        pass




def reverse_apicontroller_action(response):
    """
    Make an API call look like a direct action call by reversing the
    exception -> HTTP response translation that APIController.action does
    """
    try:
        parsed = json.loads(response)
        err = parsed.get('error', {})
        if not err:
            return parsed
    except ValueError:
        err = {}

    etype = err.get('__type')
    emessage = err.get('message', ': ').split(': ', 1)[1]
    if etype == 'Search Query Error':
        # I refuse to eval(emessage), even if it would be more correct
        raise SearchQueryError(emessage) 
    elif etype == 'Search Error':
        # I refuse to eval(emessage), even if it would be more correct
        raise SearchError(emessage) 
    elif etype == 'Parameter Error':
        e = ParameterError()
        e.extra_msg = emessage
        raise e
    elif etype == 'Validation Error':
        raise ValidationError(err)
    elif etype == 'Not Found Error':
        e = NotFound()
        e.extra_msg = emessage
        raise e
    elif etype == 'Not Found Error':
        raise NotAuthorized()
    else:
        raise DataError(response.split(': ')[-1].split(' - ', 1)[0])
