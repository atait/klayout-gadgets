import lygadgets
import os

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
    assert pya.Technology.technology_names() == ['']
    new_klayout_home = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'examples')
    new_klayout_home = os.path.realpath(new_klayout_home)
    os.environ['KLAYOUT_HOME'] = new_klayout_home
    assert 'salt_test' in lygadgets.Technology.technology_names()
    tech_obj = lygadgets.Technology.technology_by_name('salt_test')
    assert tech_obj.name == 'salt_test'
    assert tech_obj.base_path() == os.path.join(new_klayout_home, 'salt', 'salt_test')
