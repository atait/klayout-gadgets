# Patches the current bug in klayout pymod that does not load technologies on initialization
from lygadgets.environment import klayout_home
from lygadgets import xml_to_dict
import os

import pya  # Not tested with the new standalone version of pya


def init_klayout_technologies():
    def unique_name(existing_list):
        for iTmp in range(len(existing_list)):
            tempname = 'temp' + str(iTmp)
            if tempname not in existing_list:
                return tempname
    if os.path.isdir(klayout_home()):
        for root, dirnames, filenames in os.walk(klayout_home(), followlinks=True):
            for fn in filenames:
                if fn.endswith('.lyt'):
                    new_tech = pya.Technology.create_technology(unique_name(pya.Technology.technology_names()))
                    new_tech.load(os.path.join(root, fn))


def klayout_last_open_technology():
    rc_file = os.path.join(klayout_home(), 'klayoutrc')
    with open(rc_file, 'r') as file:
        rc_dict = xml_to_dict(file.read())
    return rc_dict['config']['initial-technology']
