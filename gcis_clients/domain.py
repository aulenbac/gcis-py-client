__author__ = 'abuddenberg'

from copy import deepcopy
import json
import re
import inspect

from dateutil.parser import parse


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


class GcisObject(Gcisbase):
    def __init__(self, data, **kwargs):
        #Special case for contributors
        contrib_list = data.pop('contributors', None)
        self.contributors = [Contributor(contrib) for contrib in contrib_list] if contrib_list else []

        parents_list = data.pop('parents', None)
        self.parents = [Parent(parent) for parent in parents_list] if parents_list else []

        super(GcisObject, self).__init__(data, **kwargs)

    def add_contributor(self, contributor):
        self.contributors.append(contributor)

    def add_person(self, person):
        self.contributors.append(Contributor(person, Organization()))

    def add_parent(self, parent):
        self.parents.append(parent)


class Figure(GcisObject):
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


class Chapter(GcisObject):
    def __init__(self, data):
        self.gcis_fields = ['report_identifier', 'identifier', 'number', 'url', 'title']

        super(Chapter, self).__init__(data, fields=self.gcis_fields)


class Image(GcisObject):
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

        #Private attributes for handling date parsing
        self._create_dt = None

        super(Image, self).__init__(data, fields=self.gcis_fields, trans=self.translations)

        #Hack
        self.identifier = self.identifier.replace('/image/', '')

        self.local_path = local_path
        self.remote_path = remote_path

        #This does not accurately reflect GCIS' data model
        self.datasets = []

    @property
    def create_dt(self):
        return self._create_dt

    @create_dt.setter
    def create_dt(self, value):
        try:
            self._create_dt = parse(value).isoformat() if value else None
        except TypeError:
            self._create_dt = None

    def __str__(self):
        return 'Image: {id}: {name}'.format(id=self.identifier, name=self.title)


class Dataset(GcisObject):
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
            'Global Historical Climatology Network - Daily': 'nca3-ghcn-daily-r201305',
            'Global Historical Climatology Network - Monthly': 'nca3-ghcn-monthly-r201305',
            'NCDC Merged Land and Ocean Surface Temperature': 'nca3-mlost',
            'U.S. Climate Divisional Dataset Version 2': 'nca3-cddv2-r1',
            'Climate Division Database Version 2': 'nca3-cddv2-r1',
            'Eighth degree-CONUS Daily Downscaled Climate Projections by Katharine Hayhoe': 'nca3-cmip3-downscaled-r201304',
            'Eighth degree-CONUS Daily Downscaled Climate Projections': 'nca3-cmip3-downscaled-r201304',
            'Earth Policy Institute Atmospheric Carbon Dioxide Concentration, 1000-2012': 'nca3-epi-co2-r201307',
            'Daily 1/8-degree gridded meteorological data [1 Jan 1949 - 31 Dec 2010]': 'nca3-maurer-r201304',
            'NCEP/NCAR Reanalysis': 'nca3-ncep-ncar-r1',
            'NCDC Global Surface Temperature Anomalies': 'nca3-ncdc-gst-anomalies-r201307',
            'GRACE Static Field Geopotential Coefficients JPL Release 5.0 GSM': 'nca3-grace-r201307',
            'UW/NCDC Satellite Derived Hurricane Intensity Dataset': 'nca3-hursat-r1',
            'Bias-Corrected and Spatially Downscaled Surface Water Projections Hydrologic Data': 'nca3-water-projections-r201208',
            'International Best Track Archive for Climate Stewardship (IBTrACS)': 'nca3-ibtracs-r201311',
            'the World Climate Research Programme\'s (WCRP\'s) Coupled Model Intercomparison Project phase 3 (CMIP3) multi-model dataset': 'nca3-cmip3-r201205',
            'World Climate Research Programme\'s (WCRP\'s) Coupled Model Intercomparison Project phase 3 (CMIP3) multi-model dataset': 'nca3-cmip3-r201205',
            'World Climate Research Program\'s (WCRP\'s) Coupled Model Intercomparison Project phase 3 (CMIP3) multi-model dataset': 'nca3-cmip3-r201205',
            'North American Regional Climate Change Assessment Program dataset': 'nca3-narccap-r201205',
            'Gridded Population of the World Version 3 (GPWv3): Population Count Grid': 'nca3-gpwv3-r201211',
            'ETCCDI Extremes Indices Archive': 'nca3-etccdi-r201305',
            'Historical Climatology Network Monthly (USHCN) Version 2.5': 'nca3-ushcn',
            'Annual Maximum Ice Coverage (AMIC)': 'nca3-amic-r201308',
            'Global Historical Climatology Network-Daily (GHCN-D) Monthly Summaries: North American subset': 'nca3-ghcnd-monthly-summaries-r201401',
            'Global Sea Level From TOPEX & Jason Altimetry': 'nca3-topex-jason-altimetry-r1',
            'World Climate Research Program\'s (WCRP\'s) Coupled Model Intercomparison Project phase 5 (CMIP5) multi-model ensemble': 'nca3-cmip5-r1',

            #Surely we can do better
            'Proxy Data': 'nca3-proxy-data-r1',
            'Tide Gauge Data': 'nca3-tide-gauge-data-r1',
            'Projected Sea Level Rise': 'nca3-projected-sea-level-rise-r1',
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

        #Hack to fix a particular kind of bad URL
        if self.url and self.url.startswith('ttp://'):
            self.url = self.url.replace('ttp://', 'http://')

    def __repr__(self):
        return 'Dataset: {id}: {name}'.format(id=self.identifier, name=self.name)

    def __str__(self):
        return self.__repr__()

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
            
            
class Activity(GcisObject):
    def __init__(self, data):
        self.gcis_fields = ['start_time', 'uri', 'methodology', 'data_usage', 'href', 'metholodogies', 'end_time',
                            'output_artifacts', 'duration', 'identifier', 'publication_maps', 'computing_environment',
                            'software', 'visualization_software', 'notes']

        self.translations = {
            'how_much_time_was_invested_in_creating_the_image': 'duration',
            '35_what_are_all_of_the_files_names_and_extensions_associated_with_this_image': 'output_artifacts',
            'what_operating_systems_and_platforms_were_used': 'computing_environment',
            'what_analytical_statistical_methods_were_employed_to_the_data': 'methodology',
            'describe_how_the_data_was_used_in_the_image_figure_creation': 'data_usage',
            'list_the_name_and_version_of_the_software': 'software',
            'what_software_applications_were_used_to_manipulate_the_data': 'notes',
            '33_what_software_applications_were_used_to_visualize_the_data': 'visualization_software'

        }

        super(Activity, self).__init__(data, fields=self.gcis_fields, trans=self.translations)

    def as_json(self, indent=0):
        return super(Activity, self).as_json(omit_fields=['metholodogies', 'publication_maps'])

    def __repr__(self):
        return 'Activity: {id}'.format(id=self.identifier)

    def __str__(self):
        return self.__repr__()


class Person(Gcisbase):
    def __init__(self, data):
        self.gcis_fields = ['first_name', 'last_name', 'middle_name', 'contributors', 'url', 'uri', 'href', 'orcid',
                            'id']

        self.translations = {}

        super(Person, self).__init__(data, fields=self.gcis_fields, trans=self.translations)

    def as_json(self, indent=0):
        return super(Person, self).as_json(omit_fields=['contributors'])

    def __repr__(self):
        return 'Person: {id}: {fn} {ln}'.format(id=self.id, fn=self.first_name, ln=self.last_name)

    def __str__(self):
        return self.__repr__()


class Organization(Gcisbase):
    def __init__(self, data):
        self.gcis_fields = ['organization_type_identifier', 'url', 'uri', 'href', 'country_code', 'identifier', 'name']

        self.translations = {}

        self._identifiers = {
            'NOAA NCDC/CICS-NC': 'cooperative-institute-climate-satellites-nc',
            'NCDC/CICS-NC': 'cooperative-institute-climate-satellites-nc',
            'NOAA NCDC/CICS NC': 'cooperative-institute-climate-satellites-nc',
            'NESDIS/NCDC': 'national-climatic-data-center',
            'NCDC': 'national-climatic-data-center',
            'U.S. Forest Service': 'us-forest-service',
            'NOAA Pacific Marine Environmental Laboratory': 'pacific-marine-environmental-laboratory',
            'Jet Propulsion Laboratory': 'jet-propulsion-laboratory',
            'HGS Consulting': 'hgs-consulting-llc',
            'University of Virginia': 'university-virginia',
            'Miami-Dade Dept. of Regulatory and Economic Resources': 'miami-dade-dept-regulatory-economic-resources',
            'Nansen Environmental and Remote Sensing Center': 'nansen-environmental-and-remote-sensing-center',
            'University of Illinois at Urbana-Champaign': 'university-illinois',
            'USGCRP': 'us-global-change-research-program',
            'National Park Service': 'national-park-service',
            'Institute of the Environment': 'university-arizona',
            'USGS': 'us-geological-survey',
            'University of Puerto Rico': 'university-puerto-rico',
            'University of Alaska': 'university-alaska',
            'U.S. Department of Agriculture': 'us-department-agriculture',
            'Kiksapa Consulting': 'kiksapa-consulting-llc',
            'Centers for Disease Control and Prevention': 'centers-disease-control-and-prevention',
            'Pacific Northwest Laboratories': 'pacific-northwest-national-laboratory',
            'Susanne Moser Research & Consulting': 'susanne-moser-research-consulting',
            'NEMAC': 'national-environmental-modeling-analysis-center',
        }

        super(Organization, self).__init__(data, fields=self.gcis_fields, trans=self.translations)

        if not self.identifier:
            self.identifier = self._identifiers[self.name] if self.name in self._identifiers else None

    def __repr__(self):
        return 'Organization: {id}: {name}'.format(id=self.identifier, name=self.name)

    def __str__(self):
        return self.__repr__()


class Contributor(Gcisbase):
    def __init__(self, data):
        self.gcis_fields = ['role_type_identifier', 'organization_uri', 'uri', 'href', 'person_uri', 'person_id', 'id']

        #Hack
        self.people_role_map = {
            'Kenneth Kunkel': 'scientist',
            'Xungang Yin': 'scientist',
            'Nina Bednarsek': 'scientist',
            'Henry Schwartz': 'scientist',
            'Jessicca Griffin': 'graphic_artist',
            'James Youtz': 'scientist',
            'Chris Fenimore': 'scientist',
            'Deb Misch': 'graphic_artist',
            'James Galloway': 'scientist',
            'Laura Stevens': 'scientist',
            'Nichole Hefty': 'point_of_contact',
            'Mike Squires': 'scientist',
            'Peter Thorne': 'scientist',
            'Donald Wuebbles': 'scientist',
            'Felix Landerer': 'scientist',
            'David Wuertz': 'scientist',
            'Russell Vose': 'scientist',
            'Gregg Garfin': 'scientist',
            'Jeremy Littell': 'scientist',
            'Emily Cloyd': 'contributing_author',
            'F. Chapin': 'scientist',
            ' Chapin': 'scientist',
            'Andrew Buddenberg': 'analyst',
            'Jerry Hatfield': 'author',
            'George Luber': 'lead_author',
            'Kathy Hibbard': 'lead_author',
            'Susanne Moser': 'convening_lead_author',
            'Bull Bennett': 'convening_lead_author',
            'Ernesto Weil': 'scientist',
            'William Elder': 'scientist',
            'Greg Dobson': 'analyst'
        }
        self._role = None

        super(Contributor, self).__init__(data, fields=self.gcis_fields)

        person_tree = data.pop('person', None)
        org_tree = data.pop('organization', None)

        self.person = Person(person_tree) if person_tree else None
        self.organization = Organization(org_tree) if org_tree else None

    @property
    def role(self):

        #Hack hack hack
        if self._role is None and self.person is not None:
            horrible_key = ' '.join((self.person.first_name, self.person.last_name))
            self._role = Role(self.people_role_map[horrible_key]) if horrible_key in self.people_role_map else None

        return self._role

    def __repr__(self):
        return '({p}/{o}/{r})'.format(p=self.person, o=self.organization, r=self.role)

    def __str__(self):
        return self.__repr__()


class Role(object):
    def __init__(self, type_id):
        self.type_id = type_id

    def __repr__(self):
        return self.type_id

    def __str__(self):
        return self.__repr__()


class Parent(Gcisbase):
    def __init__(self, data):
        self.gcis_fields = ['relationship', 'url', 'publication_type_identifier', 'label', 'activity_uri', 'note']

        self.translations = {
            'what_type_of_publication_was_the_figure_published_in': 'publication_type_identifier',
            'name_title': 'label',
            'article_title': 'label',
            'book_title': 'label',
            'web_page_title': 'label',
            'conference_title': 'label',
            'title': 'label',
        }

        self.publication_type_map = {
            'report': 'report',
            'journal_article': 'article',
            'book_section': 'report',
            'electronic_article': 'article',
            'web_page': 'webpage',
            'book': 'book',
            'conference_proceedings': 'generic',
        }

        self.search_hints = {
            'report': {
                'The State of the Climate 2009 Highlights': 'noaa-stateofclim-2009',
                'Global Climate Change Impacts in the United States': 'nca2',
                'Impacts of Climate Change and Variability on Transportation Systems and Infrastructure: Gulf Study, Phase I.': 'ccsp-sap-4_7-2008',
                'Climate and Energy-Water-Land  System Interactions': 'pnnl-21185',
                'Freshwater Use by U.S. Power Plants Electricity\'s thirst for a Precious Resource': 'ucusa-freshwater-2011',
                'New York City Panel on Climate Change Climate Risk Information 2013 Observations, Climate Change Projections and Maps': 'nycpanelonclimch-cri2013',
                'Regional Climate Trends and Scenarios for the U.S. National Climate Assessment. Part 2. Climate of the Southeast U.S.': 'noaa-techreport-nesdis-142-2',
                'Regional Climate Trends and Scenarios for the U.S. National Climate Assessment. Part 3. Climate of the Midwest U.S.': 'noaa-techreport-nesdis-142-3',
                'Reefs at Risk Revisited': ('book', '3788c071-e06a-42c3-b0b9-0396fd494aa3'),
                'Climate Change and Pacific Islands: Indicators and Impacts Report for the 2012 Pacific Islands  Regional Climate Assessment': 'pirca-climate-change-and-pacific-islands',
                'Climate adaptation: Risk, uncertainty and decision-making': 'ukcip-climate-adaptation-risk-uncertainty-and-decision-making',
                'Adapting to Impacts of Climate Change. America\'s Climate Choices: Report of the Panel on 43 Adapting to the Impacts of Climate C': ('book', '1e88532d-c40d-47d2-a872-77b2627fbe89'),
                'Climate Change 2007:  The Physical Science Basis. Contribution of Working Group I to the Fourth Assessment Report of the IPCC': ('book', '92debecd-ca55-46f1-a0c1-734e6b0dc6b1'),
                'Snow, Water, Ice and Permafrost in the Arctic (SWIPA): Climate Change and the Cryosphere': ('book', 'e7c9614c-8db8-410f-9fec-0957292554bf'),
                'Climate Change 2013: The Physical Science Basis. Contribution of Working Group I to the Fifth Assessment  Report of the IPCC': 'ipcc-wg1-ar5-physical-science-basis',
                'Regional Climate Trends and Scenarios for the U.S. National Climate Assessment. Part 9. Climate of the Contiguous United States': 'noaa-techreport-nesdis-142-9',
                'How to Avoid Dangerous Climate Change. A Target for U.S. Emissions Reductions': 'ucusa-howtoavoid-2007',
                'Summary for Decision Makers. Assessment of Climate Change in the Southwest United States': 'swccar-assessment-climate-change-in-southwest-us',
                'Climate Variability and Change in Mobile, Alabama: Task 2 Final Report. Impacts of Climate  25 Change and Variability on Transpo': 'fhwa-hep-12-053',
                'Effects of Climatic Variability and  Change on Forest Ecosystems: A Comprehensive Science  Synthesis for the U.S. Forest  Sector': 'usfs-pnw-gtr-870',
                'Future of America\'s Forests and Rangelands Forest Service. 2010 Resources Planning Act Assessment': 'usfs-gtr-wo-87',
                'Regional Climate Trends and Scenarios for the U.S. National Climate Assessment. Part 5. Climate of the Southwest U.S.': 'noaa-techreport-nesdis-142-5',
                'Regional Climate Trends and Scenarios for the U.S. National Climate Assessment. Part 7. Climate of Alaska': 'noaa-techreport-nesdis-142-7',
                'Reclamation, SECURE Water Act Section 9503(c) - Reclamation Climate Change and Water, Report to  Congress': 'usbr-secure-2011'


            },
            'webpage': {
                'Toxic Algae Bloom in Lake Erie. October 14, 2011': 'afe12af6-a7d3-4b70-99e5-0f80b67b7047',
                'Tribal Energy Program Projects on Tribal Lands': 'abde0ebc-342b-4bb7-b206-016cd3c829c4',
                'Atlas of Rural and Small-Town America. Category: County Classifications. Current Map: Rural-urban Continuum Code, 2013': '2cb79b4a-31cf-43ec-a70a-0371626f1407',
                'Atlas of Rural and Small-Town America. Category: County Classifications. Current Map: Economic Dependence, 1998-2000': '2cb79b4a-31cf-43ec-a70a-0371626f1407',
                'Atlas of Rural and Small-Town America. Category: People.': '2cb79b4a-31cf-43ec-a70a-0371626f1407',
                'St. Petersburg Coastal and Marine Science Center': '2f586ef7-91bb-45e5-b463-ee3e358185ba',
                'NASA Earth Observatory Natural Hazards': 'c57946b1-f413-491f-b75c-1c08f7594f84',
                'Plants of Hawaii': 'a8159919-b01c-442b-afb8-c2e272f81f48',
                'Public Roads': '5f3538ab-eb81-4858-b44e-1304b949b288',
                'Freight Analysis Framework Data Tabulation Tool': '5fe65558-d010-445b-b4f1-9079224dca6b',
                'Ecosystem Services Analysis of Climate Change and Urban Growth in the Upper Santa Cruz Watershed: SCWEPM': 'd4622f7e-aca7-42e6-95da-90579a187c30',
                'State and Local Climate Adaptation': '7de6bfc9-55fa-4d12-ae80-486561b3802c',
                'Climate Change Response Framework - Northwoods': '267378f7-278b-4201-8ffa-a820f5a694b8',
                'NWHI Maps and Publications': 'e6438f11-85f4-4c29-abb5-b09efa3279b2',
                'The Cryosphere Today Compare Daily Sea Ice': 'e4a9eb6a-9421-42c3-94b1-47caf588d41d',
                'NASA Earth Observatory Visualizing the Sea Ice Minimum': '71b4c19e-42da-4f15-99d2-7c7746d8eaf2',
                '2007 Census Ag Atlas Maps: Crops and Plants': 'f39c0146-137f-4668-b401-5972fe40208d',
                'NRCS Photo Gallery': '13da595f-e0f0-4ad0-b87b-44ce3897cd30',
                'Billion-Dollar Weather/Climate Disasters: Mapping': 'd70d7a59-45d7-4b38-baf2-86a7fcf12da3',
                'Before and After: 50 Years of Rising Tides and Sinking Marshes': '6778161f-897b-4f89-942f-8ad2f01f11a0'


            },
            'article': {
                'North American carbon dioxide sources and sinks: magnitude, attribution, and uncertainty': '10.1890/120066',
                'Air Quality and Exercise-Related Health Benefits from Reduced Car Travel  in the Midwestern United States': '10.1289/ehp.1103440',
                'A Shift in Western Tropical Pacific Sea Level Trends during the 1990s': '10.1175/2011JCLI3932.1',
                'An update on Earth\'s energy balance in light of the latest global observations': '10.1038/ngeo1580',
                'About the Lack of Warming...': ('web_page', 'e2ec2d0f-430c-4032-a309-2514ca1f6572'),
                'The Myth of the 1970s Global Cooling Scientific Consensus': '10.1175/2008BAMS2370.1',
                'Hurricane Sandy devestates NY/NJ-area passenger rai systems': ('web_page', '135ae7d9-56e3-4dcb-a81c-42a6f1e9b332'),
                'Climate change impacts of US reactive nitrogen': '10.1073/pnas.1114243109',
                'Range-wide patterns of greater  sage-grouse persistence': '10.1111/j.1472-4642.2008.00502.x',
                'Monitoring and understanding changes in heat waves, cold waves, floods and droughts in the United States: State of Knowledge': '10.1175/BAMS-D-12-00066.1',

            },
            'book': {
                'Climate Change and Pacific Islands: Indicators and Impacts. Report for the 2012 Pacific Islands Regional Climate Assessment': ('report', 'pirca-climate-change-and-pacific-islands'),
                'A focus on climate during the past 100 years in "Climate Variability and Extremes during the Past 100 Years"': '998aa4c2-9f0d-478c-b7bb-19e383c628a9'
            },
            'generic': {
                'Verrazano Narrows Storm Surge Barrier: Against the Deluge: Storm Barriers to  Protect New York City, March 31st 2009': '01d188d1-636b-49e6-af43-c1544cee9319',
                'National Association of Recreation Resource Planners Annual Conference': 'national-association-of-recreation-resource-planners-annual-conference-2005'
            }
        }

        self._publication_type_identifier = None

        super(Parent, self).__init__(data, fields=self.gcis_fields, trans=self.translations)

        #HACK: Set default relationship type
        self.relationship = self.relationship if self.relationship else 'prov:wasDerivedFrom'

        #HACK to smooth out ambiguous search results
        if self.publication_type_identifier in self.search_hints and self.label in \
                self.search_hints[self.publication_type_identifier]:

            hint = self.search_hints[self.publication_type_identifier][self.label]
            if isinstance(hint, tuple):
                type, id = hint
                self.publication_type_identifier = type
            else:
                id = hint
                type = self.publication_type_identifier

            self.url = '/{type}/{id}'.format(type=self.publication_type_identifier, id=id)

    @property
    def publication_type_identifier(self):
        return self._publication_type_identifier

    @publication_type_identifier.setter
    def publication_type_identifier(self, value):
        self._publication_type_identifier = self.publication_type_map[value] \
            if value in self.publication_type_map else '**MISSING**' + value

    def __repr__(self):
        return '{rel}: {type}: {url}: {lbl}'.format(
            rel=self.relationship, type=self.publication_type_identifier, url=self.url, lbl=self.label
        )

    def __str__(self):
        return self.__repr__()