import string
from .utility_functions import reverse_dict
"""
File to set constant objects that are needed throughout the hitsDB app
"""

idx_to_letters_map = dict(enumerate(string.ascii_letters.upper()))
letters_to_idx_map = reverse_dict(idx_to_letters_map)

picklist_map = {
    1: {'name': 'PlateType', 'desc': 'plate to be used as defined in Plate Definition','optional':False},
    2: {'name': 'PlateID', 'desc' : 'this is user’s custom ID for a specific plate, e.g. it could be CI-NewJersey-23 or anything user requires','optional':False},
    3: {'name':'Location', 'desc': 'where to bring the position. “AM” is normally used which stands for Aperture Main.', 'optional':False},
    4: {'name':'Plate Row', 'desc': 'e.g. if the location is B5a then this would be “B”. Must match Plate Definition.','optional':False},
    5: {'name':'Plate Column', 'desc':'e.g. if the location is B5a then this would be “5”. Must match Plate Definition.'},'optional':False,
    6: {'name':'Plate Subwell', 'desc':'if the location is B5a then this would be “a”. Must match Plate Definition.','optional':False},
    7: {'name':'Comment', 'desc':'this field is a comment generated by the software. Convention is to prefix with “OK” or “Fail” and the result of experiment (e.g. “FAIL: melted”).', 'optional': True},
    8: {'name':'CrystalID', 'desc':'This is field auto-generated by the software, using the Xta-no field/mask of the “Workflow control” screen.', 'optional':True},
    9: {'name':'Time of Arrival', 'desc':'time when the move to bring the plate position to the target destination stopped.', 'optional':True},
    10: {'name':'Time of Departure', 'desc':'time when one of the red or green (success/fail) buttons was pressed and picking was completed.', 'optional':True},
    11: {'name':'Duration', 'desc':'Time of Departure – Time of Arrival.', 'optional':True},
    12: {'name': 'Destination Name', 'desc': 'this field is auto-generated by using the “Destination” section of the “Workflow control” tab. For example, this could be a puck identifier', 'optional':True},
    13: {'name': 'Destination Location', 'desc':'this field is auto-generated by using the “Destination” section of the “Workflow control” tab. It represents individual location within the destination (e.g. a pin number in a puck)', 'optional':False },
    14: {'name': 'Barcode', 'desc':'', 'optional':False},
    15: {'name': 'External Comment', 'desc':'any other comment user wishes to enter in the file.', 'optional':True}
}

echoSrc_to_mrc3Dest_map = {

}

subwell_map = {
    1: 'a',
    2: 'b',
    3: 'c',
}

reverse_subwell_map = reverse_dict(subwell_map)


