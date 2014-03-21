from types import NoneType

__author__ = 'abuddenberg'

from copy import deepcopy
import json
from dateutil.parser import parse
import re
import inspect


class Gcisbase(object):
    def __init__(self, data, fields=[], trans={}):
        #Setup class variables
        self.gcis_fields = fields
        self.translations = trans

        #Save off a copy of the original JSON for debugging
        self.original = deepcopy(data)

        #Create attributes from the master list
        self. __dict__.update(dict.fromkeys(self.gcis_fields, None))

        #Perform translations
        for term in self.translations:
            val = data.pop(term, None)
            if val is not None:
                data[self.translations[term]] = val

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
        #This sucks
        attrs_we_care_about = [(attr, v) for attr, v in inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
                               if not attr.startswith('__')]

        for attr, value in attrs_we_care_about:
            if value in (None, '') and hasattr(other, attr):
                setattr(self, attr, getattr(other, attr))

        return self

    def as_json(self, indent=0, omit_fields=[]):
        out_fields = set(self.gcis_fields) - (set(['uri', 'href']) | set(omit_fields))
        return json.dumps({f: getattr(self, f) for f in out_fields}, indent=indent)


class Figure(Gcisbase):
    def __init__(self, data):
        self.gcis_fields = [
            'usage_limits', 'kindred_figures', 'time_end', 'keywords', 'lat_min', 'create_dt', 'lat_max', 'time_start',
            'title', 'ordinal', 'lon_min', 'report_identifier', 'chapter', 'submission_dt', 'uri', 'lon_max',
            'caption', 'source_citation', 'attributes', 'identifier', 'chapter_identifier', 'images'
        ]

        self.translations = {
            'what_is_the_figure_id': 'identifier',
            'what_is_the_name_of_the_figure_as_listed_in_the_report': 'title',
            'when_was_this_figure_created': 'create_dt',
            'what_is_the_chapter_and_figure_number': 'figure_num'
        }

        super(Figure, self).__init__(data, fields=self.gcis_fields, trans=self.translations)

        #Special case for chapter
        chap_tree = data.pop('chapter', None)
        self.chapter = Chapter(chap_tree) if chap_tree else self.chapter

        #Special case for images
        image_list = data.pop('images', None)
        self.images = [Image(image) for image in image_list] if image_list else []

        #Hack
        self.identifier = self.identifier.replace('/figure/', '') if self.identifier != '' else '***ID MISSING***'

    @property
    def figure_num(self):
        if isinstance(self.chapter, Chapter) and self.chapter.number and self.ordinal:
            return '{0}.{1}'.format(self.chapter.number, self.ordinal)
        else:
            return '{0}.{1}'.format(self.chapter, self.ordinal)

    #TODO: Ordinal handling is unnecessarily complex
    @figure_num.setter
    def figure_num(self, value):
        try:
            chp, fig = value.split('.')
            chp = int(chp)
            fig = int(fig)
        except ValueError:
            print 'Invalid chapter/figure numbers: ' + value
            chp = None
            fig = None
        self.ordinal = fig

        #If we have an actual Chapter instance, populate it
        if isinstance(self.chapter, Chapter):
            self.chapter.number = chp
        else:
            self.chapter = chp

    def as_json(self, indent=0):
        return super(Figure, self).as_json(omit_fields=['images', 'chapter', 'kindred_figures', 'keywords'])

    def __str__(self):
        string = '{f_id}: Figure {f_num}: {f_name}\n\tImages: {imgs}'.format(
            f_id=self.identifier, f_num=self.figure_num, f_name=self.title, imgs=[i.identifier for i in self.images]
        )
        return string

    def __repr__(self):
        # return super(Figure, self).__repr__()
        return self.__str__()

    def merge(self, other):
        # Special handling for Chapters
        if isinstance(other.chapter, Chapter) and isinstance(self.chapter, Chapter):
            self.chapter.merge(other.chapter)

        #This might want to move to Chapter's merge()
        elif isinstance(other.chapter, Chapter) and not isinstance(self.chapter, Chapter):
            chapter_num = self.chapter
            self.chapter = other.chapter
            self.chapter.number = chapter_num

        return super(Figure, self).merge(other)


class Chapter(Gcisbase):
    def __init__(self, data):
        self.gcis_fields = ['report_identifier', 'identifier', 'number', 'url', 'title']

        super(Chapter, self).__init__(data, fields=self.gcis_fields)


class Image(Gcisbase):
    def __init__(self, data, local_path=None, remote_path=None):
        self.gcis_fields = ['attributes', 'create_dt', 'description', 'identifier', 'lat_max', 'lat_min', 'lon_max',
                            'uri', 'lon_min', 'position', 'submission_dt', 'time_end', 'time_start', 'title', 'href',
                            'usage_limits']

        self.translations = {
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

        super(Image, self).__init__(data, fields=self.gcis_fields, trans=self.translations)

        #Hack
        self.identifier = self.identifier.replace('/image/', '')

        self.local_path = local_path
        self.remote_path = remote_path

        #This does not accurately reflect GCIS' data model
        self.datasets = []

    def __str__(self):
        return 'Image: {id} {name}'.format(id=self.identifier, name=self.title)


class Dataset(Gcisbase):
    def __init__(self, data):
        self.gcis_fields = ['contributors', 'vertical_extent', 'native_id', 'href', 'references', 'cite_metadata',
                        'scale', 'publication_year', 'temporal_extent', 'version', 'parents', 'scope', 'type',
                        'processing_level', 'files', 'data_qualifier', 'access_dt', 'description', 'spatial_ref_sys',
                        'spatial_res', 'spatial_extent', 'doi', 'name', 'url', 'uri', 'identifier', 'release_dt',
                        'attributes']

        self.translations = {
            'data_set_access_date': 'access_dt',
            'data_set_publication_year': 'publication_year',
            'data_set_original_release_date': 'release_dt',
            # HACK elsewhere 'start_time and end_time': '',
            'data_set_id': 'native_id',
            # HACK elsewhere'': 'doi',
            # HACK elsewhere 'maximum_latitude etc. etc. etc.': '',
            'data_set_version': 'version',
            'data_set_name': 'name',
            'data_set_citation': 'cite_metadata',
            'data_set_description': 'description',
            # Not sure'': 'type',
            'data_set_location': 'url',
            'data_set_variables': 'attributes'
        }

        #This desperately needs to get added to the webform
        self._identifiers = {
            'Global Historical Climatology Network - Daily': 'ghcn-daily',
            'Global Historical Climatology Network - Monthly': 'ghcn-monthly',
            'NCDC Merged Land and Ocean Surface Temperature': 'MLOST',
            'Climate Division Database Version 2': 'cddv2',
            'Eighth degree-CONUS Daily Downscaled Climate Projections by Katharine Hayhoe': 'CMIP3-Downscaled', #Problem
            'Eighth degree-CONUS Daily Downscaled Climate Projections': 'CMIP3-Downscaled', #Problem
            'Earth Policy Institute Atmospheric Carbon Dioxide Concentration, 1000-2012': 'EPI-CO2',
            'Daily 1/8-degree gridded meteorological data [1 Jan 1949 - 31 Dec 2010]': 'Maurer',
            'NCEP/NCAR Reanalysis': 'NCEP-NCAR',
            'NCDC Global Surface Temperature Anomalies': 'NCDC-GST-Anomalies',
            'GRACE Static Field Geopotential Coefficients JPL Release 5.0 GSM': 'GRACE',
            'UW/NCDC Satellite Derived Hurricane Intensity Dataset': 'Hurricane-Intensity',
            'Bias-Corrected and Spatially Downscaled Surface Water Projections Hydrologic Data': 'Water-Projections',
            'International Best Track Archive for Climate Stewardship (IBTrACS)': 'IBTrACS',
            'the World Climate Research Programme\'s (WCRP\'s) Coupled Model Intercomparison Project phase 3 (CMIP3) multi-model dataset': 'CMIP3',
            'North American Regional Climate Change Assessment Program dataset': 'NARCCAP',
            'Gridded Population of the World Version 3 (GPWv3): Population Count Grid': 'GPWv3'


        }

        #Private attributes for handling date parsing
        self._release_dt = None
        self._access_dt = None
        self._publication_year = None

        #These do not accurately reflect GCIS' data model
        self.note = None
        self.activity = None

        super(Dataset, self).__init__(data, fields=self.gcis_fields, trans=self.translations)

        self.identifier = self._identifiers[self.name] if self.name in self._identifiers else self.name

    def __str__(self):
        return 'Dataset: {id} {name}'.format(id=self.identifier, name=self.name)

    def as_json(self, indent=0):
        return super(Dataset, self).as_json(omit_fields=['files', 'parents', 'contributors', 'references'])

    def merge(self, other):
        for k in self.__dict__:
            #If our copy of the field is empty or the other copy is longer, take that one.
            #TODO: Shoot myself for professional negligence.
            if hasattr(other, k) and (self.__dict__[k] in (None, '') or len(getattr(other, k)) > self.__dict__[k]):
                self.__dict__[k] = getattr(other, k)
            return self

    @property
    def release_dt(self):
        return self._release_dt

    @release_dt.setter
    def release_dt(self, value):
        try:
            self._release_dt = parse(value).isoformat() if value else None
        except TypeError:
            self._release_dt = None

    @property
    def access_dt(self):
        return self._access_dt

    @access_dt.setter
    def access_dt(self, value):
        try:
            self._access_dt = parse(value).isoformat() if value else None
        except TypeError:
            # print "Problem with date: " + self.access_dt
            self._access_dt = None

    @property
    def publication_year(self):
        return self._publication_year

    @publication_year.setter
    def publication_year(self, value):
        match = re.search('\d{4}', value) if value else None
        if match:
            self._publication_year = match.group()
        else:
            self._publication_year = None