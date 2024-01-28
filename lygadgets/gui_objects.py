''' Safe versions of the GUI members for window and active layout.
    These use patch_environment so they will work fine in GUI/GSI and at least not error in standalone.
'''
import pya
from lygadgets.technology import Technology
from lygadgets.environment import patch_environment

def gui_window():
    patch_environment()  # makes sure the Application attribute gets spoofed into the standalone
    from lygadgets import pya
    return pya.Application.instance().main_window()


def gui_view():
    lv = gui_window().current_view()
    if lv is None:
        raise UserWarning("No view selected. Make sure you have an open layout.")
    return lv


def gui_active_layout():
    ly = gui_view().active_cellview().layout()
    if ly is None:
        raise UserWarning("No layout. Make sure you have an open layout.")
    return ly


def gui_active_cell():
    cell = gui_view().active_cellview().cell
    if cell is None:
        raise UserWarning("No cell. Make sure you have an open layout.")
    return cell


def gui_active_technology_name():
    return gui_window().initial_technology  # gets the technology from the selection menu


def gui_active_technology():
    technology = gui_active_technology_name()
    tech_obj = Technology.technology_by_name(technology)
    return tech_obj
