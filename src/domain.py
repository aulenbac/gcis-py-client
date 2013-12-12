__author__ = 'abuddenberg'


class Gcisbase(object):
    def __init__(self, _gcis_fields, **kwargs):
        self. __dict__.update(dict.fromkeys(_gcis_fields, None))

        for k in kwargs:
            if hasattr(self, k):
                setattr(self, k, kwargs[k])


class Figure(Gcisbase):
    _gcis_fields = [
        'usage_limits', 'kindred_figures', 'time_end', 'keywords', 'lat_min', 'create_dt', 'lat_max', 'time_start',
        'uuid', 'title', 'ordinal', 'lon_min', 'report_identifier', 'chapter', 'submission_dt', 'uri', 'lon_max',
        'caption', 'source_citation', 'attributes', 'identifier', 'chapter_identifier'
    ]

    _translations = {
        'what_is_the_name_of_the_figure_as_listed_in_the_report': 'title',
        'when_was_this_figure_created': 'create_dt'
    }
    
    def __init__(self, **kwargs):
        #Create attributes from the master list
        self. __dict__.update(dict.fromkeys(self._gcis_fields, None))

        #Special case for chapter
        chap_tree = kwargs.pop('chapter', None)
        self.chapter = Chapter(**chap_tree) if chap_tree else None

        #Special case for images
        image_list = kwargs.pop('images', None)
        self.images = [Image(**image) for image in image_list if len()]

        for k in kwargs:
            if hasattr(self, k):
                setattr(self, k, kwargs[k])

    @property
    def figure_num(self):
        if self.chapter and self.chapter.number and self.ordinal:
            return '{0}.{1}'.format(self.chapter.number, self.ordinal)
        else:
            return None

    def __str__(self):
        return 'Figure: {f_num}: {f_name}'.format(f_num=self.figure_num, f_name=self.title)

    def __repr__(self):
        return super(Figure, self).__repr__()


class Chapter(object):
    _gcis_fields = ['report_identifier', 'identifier', 'number', 'url', 'title']

    def __init__(self, **kwargs):
        self. __dict__.update(dict.fromkeys(self._gcis_fields, None))

        for k in kwargs:
            if hasattr(self, k):
                setattr(self, k, kwargs[k])


class Image(object):
    _gcis_fields = []

    def __init__(self, **kwargs):
        self. __dict__.update(dict.fromkeys(self._gcis_fields, None))

        for k in kwargs:
            if hasattr(self, k):
                setattr(self, k, kwargs[k])