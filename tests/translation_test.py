import os, sys
from lygadgets import anyCell_to_anyCell, pya, any_write
from lytest import run_xor
from phidl import Device

sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__),
                                              '..', 'examples', 'salt', 'lypy_hybrid',
                                              'tech', 'example_tech')))
from lygadgets_pcells.pcell_examples import some_device

def back_and_forth():
    init_device = some_device(10, 20)

    pya_layout = pya.Layout()
    pya_cell = pya_layout.create_cell('newname')
    anyCell_to_anyCell(init_device, pya_cell)

    final_device = Device()
    anyCell_to_anyCell(pya_cell, final_device)

    return init_device, pya_layout, final_device

def test_translation_running():
    back_and_forth()

def test_translation_correct():
    # do an XOR test
    filenames = ['test{}.gds'.format(ifile) for ifile in range(3)]
    cell_list = back_and_forth()
    for fn, cell in zip(filenames, cell_list):
        any_write(cell, fn)

    try:
        run_xor(filenames[0], filenames[1])
        # run_xor(filenames[0], filenames[2])  # this will not work until phidl is updated
    finally:
        [os.remove(fn) for fn in filenames]
        pass
