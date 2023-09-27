import os, sys
import lygadgets
from lygadgets.salt_linker import link_any, unlink_any


def test_gui_spoofs():
    lygadgets.patch_environment()

    import pya
    # Borrowed from SiEPIC-Tools: https://github.com/lukasc-ubc/SiEPIC-Tools
    wdg = pya.QDialog(pya.Application.instance().main_window())
    wdg.setAttribute(pya.Qt.WA_DeleteOnClose)

    ui_file = pya.QFile(os.path.join(os.path.dirname(os.path.realpath(__file__)), "waveguidebuilder.ui"))
    ui_file.open(pya.QIODevice().ReadOnly)
    window = pya.QFormBuilder().load(ui_file, pya.Application.instance().main_window())
    ui_file.close


def test_technology():
    import pya
    # assert pya.Technology.technology_names() == ['']  # This asserts bug behavior that was fixed in 2022
    example_home = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'examples')
    example_home = os.path.realpath(example_home)
    tech_home = os.path.join(example_home, 'salt', 'lypy_hybrid', 'tech', 'example_tech')
    try:
        link_any(tech_home)
        lygadgets.Technology.reload_salt()
        assert 'example_tech' in lygadgets.Technology.technology_names()
        tech_obj = lygadgets.Technology.technology_by_name('example_tech')
        assert tech_obj.name == 'example_tech'
    finally:
        unlink_any('example_tech')
