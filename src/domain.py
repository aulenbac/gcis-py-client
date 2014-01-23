__author__ = 'abuddenberg'

from copy import deepcopy
import json


class Gcisbase(object):
    original = None

    def __init__(self, data, fields=[], trans={}):
        #Save off a copy of the original JSON for debugging
        self.original = deepcopy(data)

        #Create attributes from the master list
        self. __dict__.update(dict.fromkeys(fields, None))

        #Perform translations
        for term in trans:
            val = data.pop(term, None)
            if val is not None:
                data[trans[term]] = val

        for k in data:
            if hasattr(self, k):
                #Strip whitespace from strings for consistency
                try:
                    data[k] = data[k].strip()
                except AttributeError:
                    pass
                finally:
                    setattr(self, k, data[k])


class Figure(Gcisbase):
    _gcis_fields = [
        'usage_limits', 'kindred_figures', 'time_end', 'keywords', 'lat_min', 'create_dt', 'lat_max', 'time_start',
        'uuid', 'title', 'ordinal', 'lon_min', 'report_identifier', 'chapter', 'submission_dt', 'uri', 'lon_max',
        'caption', 'source_citation', 'attributes', 'identifier', 'chapter_identifier', 'images'
    ]

    _translations = {
        'what_is_the_figure_id': 'identifier',
        'what_is_the_name_of_the_figure_as_listed_in_the_report': 'title',
        'when_was_this_figure_created': 'create_dt'
    }
    
    def __init__(self, data):
        super(Figure, self).__init__(data, fields=self._gcis_fields, trans=self._translations)

        #Special case for chapter
        chap_tree = data.pop('chapter', None)
        self.chapter = Chapter(chap_tree) if chap_tree else None

        #Special case for images
        image_list = data.pop('images', None)
        self.images = [Image(image) for image in image_list] if image_list else []

        #Hack
        self.identifier = self.identifier.replace('/figure/', '')


    @property
    def figure_num(self):
        if self.chapter and self.chapter.number and self.ordinal:
            return '{0}.{1}'.format(self.chapter.number, self.ordinal)
        else:
            return None

    def as_json(self, indent=0):
        #Exclude a couple of fields
        out_fields = set(self._gcis_fields) - set(['images', 'chapter'])
        return json.dumps({f: self.__dict__[f] for f in out_fields}, indent=indent)

    def __str__(self):
        return '{f_id}: Figure {f_num}: {f_name}\n\tImages: {imgs}'.format(
            f_id=self.identifier, f_num=self.figure_num, f_name=self.title, imgs=[i.identifier for i in self.images]
        )

    def __repr__(self):
        return super(Figure, self).__repr__()


class Chapter(Gcisbase):
    _gcis_fields = ['report_identifier', 'identifier', 'number', 'url', 'title']

    def __init__(self, data):
        super(Chapter, self).__init__(data, fields=self._gcis_fields)


class Image(Gcisbase):
    _gcis_fields = ['attributes', 'create_dt', 'description', 'identifier', 'lat_max', 'lat_min', 'lon_max', 'lon_min',
                    'position', 'submission_dt', 'time_end', 'time_start', 'title', 'usage_limits']

    _translations = {
        'list_any_keywords_for_the_image': 'attributes',
        'when_was_this_image_created': 'create_dt',
        'what_is_the_image_id': 'identifier',
        'maximum_latitude': 'lat_max',
        'minimum_latitude': 'lat_min',
        'maximum_longitude': 'lon_max',
        'minimum_longitude': 'lon_min',
        'start_time': 'time_start',
        'end_time': 'time_end',
        'what_is_the_name_of_the_image_listed_in_the_report': 'title'
    }

    def __init__(self, data, filepath=None):
        super(Image, self).__init__(data, fields=self._gcis_fields, trans=self._translations)

        #Hack
        self.identifier = self.identifier.replace('/image/', '')
        self.filepath = filepath

    def as_json(self, indent=0):
        out_fields = self._gcis_fields
        return json.dumps({f: self.__dict__[f] for f in out_fields}, indent=indent)

    def __str__(self):
        return 'Image: {id} {name}'.format(id=self.identifier, name=self.title)
