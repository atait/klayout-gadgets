import os, sys
from lygadgets import anyCell_to_anyCell, pya, any_write
from lytest import run_xor
from phidl import Device, geometry as pg

sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__),
                                              '..', 'examples', 'salt', 'lypy_hybrid',
                                              'tech', 'example_tech')))
from lygadgets_pcells.pcell_examples import some_device

def back_and_forth():
    # from phidl to pya and back
    init_device = some_device(10, 20)

    pya_layout = pya.Layout()
    pya_cell = pya_layout.create_cell('newname')
    anyCell_to_anyCell(init_device, pya_cell)

    final_device = Device()
    anyCell_to_anyCell(pya_cell, final_device)

    return init_device, pya_layout, final_device


def test_translation_running():
    back_and_forth()


def phidl_port_translation():
    # Conversion between object and geometric representation of ports
    try:
        pg.with_geometric_ports
    except AttributeError:
        pass  # skipping
    def geom_equal(A, B):
        h1 = A.hash_geometry(precision = 1e-4)
        h2 = B.hash_geometry(precision = 1e-4)
        return h1 == h2
    init_D = pg.compass(layer = 1)
    geom_D = pg.with_geometric_ports(init_D, layer = 2)
    end_D = pg.with_object_ports(geom_D, layer = 2)
    assert geom_equal(init_D, end_D)

    assert len(geom_D.ports) == 0
    geom_D.remove_layers([2], include_labels = True)
    assert geom_equal(init_D, geom_D)

    assert geom_equal(init_D, end_D)
    for pnam, port in init_D.ports.items():
        assert np.all(end_D.ports[pnam].midpoint == port.midpoint)

    # now through the filesystem
    end2_D = anyCell_to_anyCell(init_D, Device())
    for pnam, port in init_D.ports.items():
        assert np.all(end_D.ports[pnam].midpoint == port.midpoint)
    assert geom_equal(init_D, end2_D)
    assert init_D.name == end2.name


def test_translation_correct():
    # do an XOR test
    filenames = ['test{}.gds'.format(ifile) for ifile in range(3)]
    cell_list = back_and_forth()
    for fn, cell in zip(filenames, cell_list):
        any_write(cell, fn)

    try:
        run_xor(filenames[0], filenames[1])
        run_xor(filenames[0], filenames[2])
    finally:
        [os.remove(fn) for fn in filenames]
        pass
