import lygadgets
lygadgets.patch_environment()

import pya
import os
wdg = pya.QDialog(pya.Application.instance().main_window())
wdg.setAttribute(pya.Qt.WA_DeleteOnClose)

ui_file = pya.QFile(os.path.join(os.path.dirname(os.path.realpath(__file__)), "waveguidebuilder.ui"))
ui_file.open(pya.QIODevice().ReadOnly)
window = pya.QFormBuilder().load(ui_file, pya.Application.instance().main_window())
ui_file.close