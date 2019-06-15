''' Translation functions that take Cells/Devices in different types of languages
    and convert them to Cells/Devices in other languages

    Supported: phidl, pya (GSI version), klayout.db (standalone version)
    Not yet supported: nazca, IPKISS, gdspy, other suggestions?
'''
import os

default_phidl_portlayer = 41

def celltype_to_write_function(celltype):
    ''' Takes a class that represents a layout Cell and gives a function that writes its geometry to disc
        This is typically an unbound method of the class.
        (there is always some version of this, although some languages don't explicitly call it Cell)

        This uses try-excepted on-the-fly importing because not everybody is going to have every language installed.
        But if they don't, then their celltype is not going to be from that language.
    '''
    def not_supported_error(language_name):
        raise NotImplementedError(('The translator does not yet support {}.\n'.format(language_name)
                                    + 'Supported languages are: pya, phidl\n'
                                    + 'Future support will include: gdspy, nazca, ipkiss'))

    if type(celltype) is not type:
        celltype = type(celltype)

    try: import pya  # ok I know we already imported this, but in the future it can also be on-the-fly (i.e. converting phidl to nazca)
    except ImportError: pass
    else:
        if issubclass(celltype, pya.Cell):
            return pya.Cell.write
        elif issubclass(celltype, pya.Layout):
            return pya.Layout.write

    try: import phidl
    except ImportError: pass
    else:
        if issubclass(celltype, phidl.Device):
            def write_with_ports(device, filename, *args, port_layer=None, **kwargs):
                if port_layer is None:
                    port_layer = default_phidl_portlayer
                try:
                    wgp = phidl.geometry.with_geometric_ports
                except AttributeError:  # it is an older version of phidl
                    pass
                else:
                    device = wgp(device, layer=port_layer)
                device.write_gds(filename, *args, **kwargs)
            return write_with_ports

    # try: import gdspy
    # except ImportError: pass
    # else:
    #     not_supported_error('gdspy')

    # try: import nazca
    # except ImportError: pass
    # else:
    #     not_supported_error('nazca')

    # try: import ipkiss
    # except ImportError: pass
    # else:
    #     not_supported_error('ipkiss')

    raise TypeError('celltype: {} is not recognized as a layout cell object'.format(celltype.__name__))


def any_write(cell, *args, **kwargs):
    write = celltype_to_write_function(cell)
    return write(cell, *args, **kwargs)


def celltype_to_read_function(celltype):
    ''' Takes a class that represents a layout Cell and gives its class' read method.
    '''
    def not_supported_error(language_name):
        raise NotImplementedError(('The translator does not yet support {}.\n'.format(language_name)
                                    + 'Supported languages are: pya, phidl\n'
                                    + 'Future support will include: gdspy, nazca, ipkiss'))

    if type(celltype) is not type:
        celltype = type(celltype)

    try: import pya  # ok I know we already imported this, but in the future it can also be on-the-fly (i.e. converting phidl to nazca)
    except ImportError: pass
    else:
        if issubclass(celltype, pya.Cell):
            def pyaCell_reader(pya_cell, filename, *args, **kwargs):
                templayout = pya.Layout()
                templayout.read(filename)
                tempcell = templayout.top_cell()
                # Transfer the geometry of the imported cell to the one specified
                pya_cell.name = tempcell.name
                pya_cell.copy_tree(tempcell)
                return pya_cell
            return pyaCell_reader

    try: import phidl
    except ImportError: pass
    else:
        if issubclass(celltype, phidl.Device):
            def phidlDevice_reader(phidl_device, filename, *args, port_layer=None, **kwargs):
                # phidl_device is not really used. It is just there to determine type.
                if 'cellname' in kwargs:
                    cellname = kwargs.pop('cellname')
                else:
                    #### hacks, because sometimes pya saves an extra topcell called $$$CONTEXT_INFO$$$
                    from gdspy import GdsLibrary
                    gdsii_lib = GdsLibrary()
                    gdsii_lib.read_gds(filename)
                    top_level_cells = gdsii_lib.top_level()
                    if len(top_level_cells) == 1:
                        cellname = top_level_cells[0].name
                    elif len(top_level_cells) == 2:
                        for tc in top_level_cells:
                            if tc.name != '$$$CONTEXT_INFO$$$':
                                cellname = tc.name
                    else:
                        raise ValueError('There are multiple top level cells: {}.\n Please specify with the cellname argument.'.format(top_level_cells))
                    #### end hacks

                # main read function
                tempdevice = phidl.geometry.import_gds(filename, *args, cellname=cellname, **kwargs)

                # check for port geometry
                try:
                    wop = phidl.geometry.with_object_ports
                except AttributeError:
                    pass
                else:
                    if port_layer is None:
                        port_layer = default_phidl_portlayer
                    tempdevice = wop(tempdevice, layer=port_layer)
                # copy over from temporary device
                phidl_device.polygons = tempdevice.polygons
                phidl_device.references = tempdevice.references
                phidl_device.ports = tempdevice.ports
                phidl_device.labels = tempdevice.labels
                phidl_device.name = tempdevice.name
                return phidl_device
            return phidlDevice_reader

    # try: import gdspy
    # except ImportError: pass
    # else:
    #     not_supported_error('gdspy')

    # try: import nazca
    # except ImportError: pass
    # else:
    #     not_supported_error('nazca')

    # try: import ipkiss
    # except ImportError: pass
    # else:
    #     not_supported_error('ipkiss')

    raise TypeError('celltype: {} is not recognized as a layout cell object'.format(celltype.__name__))


def any_read(cell, *args, **kwargs):
    read = celltype_to_read_function(cell)
    return read(cell, *args, **kwargs)


def anyCell_to_anyCell(initial_cell, final_cell):
    ''' Transfers the geometry of some initial_cell into another format.
        This initial_cell can be any type of layout object in any supported language.

        initial_cell must provide a way to write its geometry to a file and have only one top cell.
        This function will figure out what that way is, based on the class of initial_cell.

        final_cell must provide a way to read geometry in from a file.

        The supported types and their mapping to write methods are contained in celltype_to_write_function and celltype_to_read_function.
    '''
    tempfile = os.path.realpath('temp_cellTranslation.gds')
    any_write(initial_cell, tempfile)
    new_cell = any_read(final_cell, tempfile)
    os.remove(tempfile)
    return new_cell
