from gcis_client import GcisClient

base_url = 'http://data.gcis-dev-front.joss.ucar.edu'

gcis = GcisClient(base_url, 'andrew.buddenberg@noaa.gov', 'fcee8e3f11f36313e463ece51aab15242f71f3d552d565be')

# #Let's pull a list of all figures in Chapter 2 of the NCA3draft
for partial_figure in gcis.get_figure_listing('nca3draft', chapter_id='our-changing-climate'):
    #The listing doesn't provide all available fields for the figure (Images, for instance).
    #There aren't very many figures, so let's go ahead and grab a complete version of each
    full_figure = gcis.get_figure('nca3draft', partial_figure.identifier, chapter_id='our-changing-climate')
    print full_figure


#Let's work with the infamous temperature figure
fig2_7 = gcis.get_figure('nca3draft', 'observed-us-temperature-change')

#Warning: Images and Chapters are specifically excluded from JSON output.  This is what gets sent to GCIS. So...
print fig2_7.as_json(indent=4)

#...you might want to view the original input
print fig2_7.original

#Let's see about the images:
for image in fig2_7.images:
    print image

#How about the whole Image?
print gcis.get_image('69da6d93-4426-4061-a2a1-7b3d01f2dc1c').as_json(indent=4)

#Let's assign some GCMD keywords (The first 4 from the list)
# keyword_ids = [k['identifier'] for k in gcis.get_keyword_listing()[0:4]]

# for keyword_id in keyword_ids:
#     resp = gcis.associate_keyword_with_figure(keyword_id, 'nca3draft', 'observed-us-temperature-change')
#     print resp.status_code, resp.text
