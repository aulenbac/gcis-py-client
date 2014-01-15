from gcis_client import GcisClient

base_url = 'http://data.gcis-dev-front.joss.ucar.edu'

gcis = GcisClient(base_url, 'andrew.buddenberg@noaa.gov', 'fcee8e3f11f36313e463ece51aab15242f71f3d552d565be')

# #Let's pull a list of all figures in Chapter 2 of the NCA3draft
# for partial_figure in gcis.get_figure_listing('nca3draft', chapter_id='our-changing-climate'):
#     #The listing doesn't provide all available fields for the figure (Images, for instance).
#     #There aren't very many figures, so let's go ahead and grab a complete version of each
#     full_figure = gcis.get_figure('nca3draft', partial_figure.identifier, chapter_id='our-changing-climate')
#     print full_figure


#Let's work with the infamous temperature figure
fig2_6 = gcis.get_figure('nca3draft', 'temperature-change')

#Warning: Images and Chapters are specifically excluded from JSON output.  This is what gets sent to GCIS. So...
print fig2_6.as_json(indent=4)

#...you might want to view the original input
print fig2_6.original

#Let's see about the images:
for image in fig2_6.images:
    print image

