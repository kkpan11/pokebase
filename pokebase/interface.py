# -*- coding: utf-8 -*-

from .api import get_resource, get_data
from .common import BASE_URL, SPRITE_URL


def _make_obj(d):
    """Takes a dictionary and returns a NamedAPIResource or APIMetadata.

    The names and values of the data will match exactly with those found
    in the online docs at https://pokeapi.co/docsv2/ . In some cases, the data
    may be of a standard type, such as an integer or string. For those cases,
    the input value is simply returned, unchanged.

    :param d: the dictionary to be converted
    :return either the same value, if it does not need to be converted, or a
    NamedAPIResource or APIMetadata instance, depending on the data inputted.
    """

    if isinstance(d, dict):
        if 'url' in d.keys():
            url = d['url']
            id_ = url.split('/')[-2]      # ID of the data.
            location = url.split('/')[-3]  # Where the data is located.
            return NamedAPIResource(location, id_, lazy_load=True)
        else:
            return APIMetadata(d)
    else:
        return d


def name_id_convert(resource_type, name_or_id):

    if isinstance(name_or_id, int):
        id_ = name_or_id
        name = _convert_id_to_name(resource_type, id_)

    elif isinstance(name_or_id, str):
        name = name_or_id
        id_ = _convert_name_to_id(resource_type, name)

    return name, id_


def _convert_id_to_name(resouce_type, id_):
    resource_data = APIResourceList(resouce_type)

    for resource in resource_data:
        if resource['url'].split('/')[-2] == str(id_):

            # Return the matching name, or None if it doesn't exsist.
            return resource.get('name', None)


def _convert_name_to_id(resource_type, name):

    resource_data = APIResourceList(resource_type)

    for resource in resource_data:
        if resource.get('name') == name:
            return int(resource.get('url').split('/')[-2])


class NamedAPIResource(object):
    """Core API class, used for accessing the bulk of the data.

    The class uses a modified __getattr__ function to serve the appropriate
    data, so lookup data via the `.` operator, and use the `PokeAPI docs
    <https://pokeapi.co/docsv2/>`_ or the builtin `dir` function to see the
    possible lookups.

    This class takes the complexity out of lots of similar classes for each
    different kind of data served by the API, all of which are very similar,
    but not identical.
    """

    def __init__(self, resource_type, resource_name, lazy_load=False):

        name, id_ = name_id_convert(resource_type, resource_name)
        url = '/'.join([BASE_URL, resource_type, str(id_)])

        self.__dict__.update({'name': name,
                              'resource_type': resource_type,
                              'id_': id_,
                              'url': url})

        self.__loaded = False

        if not lazy_load:
            self._load()
            self.__loaded = True

    def __getattr__(self, attr):
        """Modified method to auto-load the data when it is needed.

        If the data has not yet been looked up, it is loaded, and then checked
        for the requested attribute. If it is not found, AttributeError is
        raised.
        """

        if not self.__loaded:
            self._load()
            self.__loaded = True

            return self.__getattribute__(attr)

        else:
            raise AttributeError('{} object has no attribute {}'
                                 .format(type(self), attr))

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return '<{}-{}>'.format(self.resource_type, self.name)

    def _load(self):
        """Function to collect reference data and connect it to the instance as
         attributes.

         Internal function, does not usually need to be called by the user, as
         it is called automatically when an attribute is requested.

        :return None
        """

        data = get_data(self.resource_type, self.id_)

        for k, v in data.items():    # Make our custom objects from the data.

            if isinstance(v, dict):
                data[k] = _make_obj(v)

            elif isinstance(v, list):
                data[k] = [_make_obj(i) for i in v]

        self.__dict__.update(data)

        return None


class APIResourceList(object):
    """Class for a data container.

    Used to access data corresponding to a category, rather than an individual
    reference. Ex. APIResourceList('berry') gives information about all
    berries, such as which ID's correspond to which berry names, and
    how many berries there are.

    You can iterate through all the names or all the urls, using the respective
    properties. You can also iterate on the object itself to run through the
    `dict`s with names and urls together, whatever floats your boat.
    """

    def __init__(self, name):
        """Creates a new APIResourceList instance.

        :param name: the name of the resource to get (ex. 'berry' or 'move')
        """

        response = get_resource(name)

        self.name = name
        self.__results = [i for i in response['results']]
        self.count = response['count']

    def __len__(self):
        return self.count

    def __iter__(self):
        return iter(self.__results)

    def __str__(self):
        return str(self.__results)

    @property
    def names(self):
        """Useful iterator for all the resource's names."""
        for result in self.__results:
            yield result.get('name', result['url'].split('/')[-2])

    @property
    def urls(self):
        """Useful iterator for all of the resource's urls."""
        for result in self.__results:
            yield result['url']


class APIMetadata(object):
    """Helper class for smaller references.

    This class emulates a dictionary, but attribute lookup is via the `.`
    operator, not indexing. (ex. instance.attr, not instance['attr']).

    Used for "Common Models" classes and NamedAPIResource helper classes.
    https://pokeapi.co/docsv2/#common-models
    """

    def __init__(self, data):

        for k, v in data.items():

            if isinstance(v, dict):
                data[k] = _make_obj(v)

        self.__dict__.update(data)