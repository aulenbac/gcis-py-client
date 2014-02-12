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
                try:
                    #Strip whitespace from strings for consistency
                    data[k] = data[k].strip()

                    #We now have unicode characters infesting our data.  I'm sure this is wrong.
                    data[k] = data[k].encode('utf-8')
                except AttributeError:
                    pass
                finally:
                    setattr(self, k, data[k])

    def merge(self, other):
        for k in self.__dict__:
            if self.__dict__[k] in (None, '') and hasattr(other, k):
                self.__dict__[k] = getattr(other, k)
        return self

    def as_json(self, indent=0):
        out_fields = self._gcis_fields
        return json.dumps({f: self.__dict__[f] for f in out_fields}, indent=indent)


class Figure(Gcisbase):
    _gcis_fields = [
        'usage_limits', 'kindred_figures', 'time_end', 'keywords', 'lat_min', 'create_dt', 'lat_max', 'time_start',
        'uuid', 'title', 'ordinal', 'lon_min', 'report_identifier', 'chapter', 'submission_dt', 'uri', 'lon_max',
        'caption', 'source_citation', 'attributes', 'identifier', 'chapter_identifier', 'images'
    ]

    _translations = {
        'what_is_the_figure_id': 'identifier',
        'what_is_the_name_of_the_figure_as_listed_in_the_report': 'title',
        'when_was_this_figure_created': 'create_dt',
        'what_is_the_chapter_and_figure_number': 'figure_num'
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
        self.identifier = self.identifier.replace('/figure/', '') if self.identifier != '' else '***ID MISSING***'

    @property
    def figure_num(self):
        if self.chapter and self.chapter.number and self.ordinal:
            return '{0}.{1}'.format(self.chapter.number, self.ordinal)
        else:
            return self.ordinal

    #TODO: Ordinal handling is unnecessarily complex
    @figure_num.setter
    def figure_num(self, value):
        try:
            chp, fig = value.split('.')
            chp = int(chp)
            fig = int(fig)

        except ValueError:
            raise Exception('Invalid chapter/figure numbers: ' + value)

        if self.chapter:
            self.chapter.number = chp
            self.ordinal = fig
        else:
            self.ordinal = value

    def as_json(self, indent=0):
        #Exclude a couple of fields
        out_fields = set(self._gcis_fields) - set(['images', 'chapter'])
        return json.dumps({f: self.__dict__[f] for f in out_fields}, indent=indent)

    def __str__(self):
        string = '{f_id}: Figure {f_num}: {f_name}\n\tImages: {imgs}'.format(
            f_id=self.identifier, f_num=self.figure_num, f_name=self.title, imgs=[i.identifier for i in self.images]
        )
        return string

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

    def __init__(self, data, local_path=None, remote_path=None):
        super(Image, self).__init__(data, fields=self._gcis_fields, trans=self._translations)

        #Hack
        self.identifier = self.identifier.replace('/image/', '')

        self.local_path = local_path
        self.remote_path = remote_path

        #This does not accurately reflect GCIS' data model
        self.datasets = []

    def __str__(self):
        return 'Image: {id} {name}'.format(id=self.identifier, name=self.title)


class Dataset(Gcisbase):
    _gcis_fields = ['contributors', 'vertical_extent', 'native_id', 'href', 'references', 'cite_metadata',
                    'scale', 'publication_dt', 'temporal_extent', 'version', 'parents', 'scope', 'type',
                    'processing_level', 'files', 'data_qualifier', 'access_dt', 'description', 'spatial_ref_sys',
                    'spatial_res', 'spatial_extent', 'doi', 'name', 'url', 'uri', 'identifier']

    _translations = {
        'data_set_access_date': 'access_dt',
        'data_set_publication_year': 'publication_dt',
        # HACK elsewhere 'start_time and end_time': '',
        'data_set_id': 'native_id',
        # HACK elsewhere'': 'doi',
        # HACK elsewhere 'maximum_latitude etc. etc. etc.': '',
        'data_set_version': 'version',
        'data_set_name': 'name',
        'data_set_citation': 'cite_metadata',
        'data_set_description': 'description',
        # Not sure'': 'type',
    }

    def __init__(self, data):
        super(Dataset, self).__init__(data, fields=self._gcis_fields, trans=self._translations)

    def __str__(self):
        return 'Dataset: {id} {name}'.format(id=self.identifier, name=self.name)