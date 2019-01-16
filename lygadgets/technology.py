'''
    lygadgets.Technology serves as a drop-in for pya.Technology in the pymod standalone.

    The difference is that the lygadgets version loads all the installed technologies in salt.
    This is not a bug. The intention of pymod:pya.Technology is to isolate from the state of a user's machine,
    but some packages are not associated with a particular technology, so they have to get it from salt.

    Nothing happens on import: Autoload from salt is triggered when you ask for either
    - Technology.technology_names, or
    - Technology.technology_by_name, or
    - Technology.has_technology

    lygadgets.Technology also offers a new method: register_lyt
    which takes the .lyt file, turns it into a Technology object (eventually returns), and adds to the class registry
'''
from lygadgets import klayout_home, pya
import xmltodict
import os

# default active is tricky and a bad idea if it just for CL convenience
# perhaps lygadgets has an idea of active technology
# this would have to be influenced by GUI switches, but those are not global

try:
    import pya
except ImportError:
    print('Did not find pya. You will not be able to use lygadgets.Technology')
    class Technology(object):
        pass
else:
    class Technology(pya.Technology):
        ''' '''
        _salt_loaded = False

        @classmethod
        def _register_pyatech(cls, pya_tech):
            if cls.has_technology(pya_tech.name):
                print("Warning: overwriting %s technology" % pya_tech.name)
                new_tech = cls.technology_by_name(pya_tech.name)
            else:
                new_tech = cls.create_technology(pya_tech.name)

            # Registering new technology to klayout's database
            new_tech.assign(pya_tech)
            return new_tech

        @classmethod
        def register_lyt(cls, lyt_filename):
            pya_tech = _load_pya_tech(lyt_filename)
            cls._register_pyatech(pya_tech)
            return pya_tech

        @classmethod
        def _load_salt(cls):
            ''' Crawls through klayout_home directory looking for .lyt files.
                Registers them with the class, returns nothing
            '''
            if cls._salt_loaded:
                return None
            cls._salt_loaded = True
            if os.path.isdir(klayout_home()):
                search_paths = [os.path.join(klayout_home(), rel_path) for rel_path in ['salt', 'tech']]
                for path in search_paths:
                    for root, dirnames, filenames in os.walk(path, followlinks=True):
                        for fn in filenames:
                            if fn.endswith('.lyt'):
                                cls.register_lyt(os.path.join(root, fn))

        # These override methods of pya.Technology

        @classmethod
        def technology_names(cls):
            ''' Equivalent behavior to pya.Technology.technology_names() in klayout's GSI '''
            cls._load_salt()
            return super().technology_names()

        @classmethod
        def technology_by_name(cls, tech_name):
            ''' Equivalent behavior to pya.Technology.technology_by_name() in klayout's GSI '''
            cls._load_salt()
            return super().technology_by_name(tech_name)

        @classmethod
        def has_technology(cls, tech_name):
            ''' Equivalent behavior to pya.Technology.has_technology() in klayout's GSI '''
            cls._load_salt()
            return super().has_technology(tech_name)

        # End of overrides.


    def _load_pya_tech(lyt_filename):
        ''' Parses the .lyt which is in xml format.
            Returns the new Technology object. Does not register it to the Technology class
        '''
        # workaround while https://github.com/klayoutmatthias/klayout/pull/215 is not solved
        absolute_filepath = os.path.realpath(os.path.expanduser(lyt_filename))
        with open(absolute_filepath, 'r') as file:
            lyt_xml = file.read()
        pya_tech = Technology.technology_from_xml(lyt_xml)
        pya_tech.default_base_path = os.path.dirname(absolute_filepath)
        # end of workaround
        return pya_tech

def klayout_last_open_technology():
    # use this to pick out a starting "active" technology
    if os.path.isdir(klayout_home()):
        rc_file = os.path.join(klayout_home(), 'klayoutrc')
        if os.path.isfile(rc_file):
            with open(rc_file, 'r') as file:
                rc_dict = xmltodict.parse(file.read(), process_namespaces=True)
            return rc_dict['config']['initial-technology']
    return ''
