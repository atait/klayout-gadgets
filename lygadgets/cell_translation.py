''' Translation functions that take Cells/Devices in different types of languages
    and convert them to Cells/Devices in other languages

    Supported: phidl, pya (GSI version), klayout.db (standalone version)
    Not yet supported: nazca, IPKISS, gdspy, other suggestions?

    Todo:
    - zeropdk read/write geometric ports
    - rudimentary pya2phidl_flat
    - use tempfile.TemporaryFile within anyCell_to_anyCell
    - better document and debug anyCell_to_anyCell
'''
import os

default_phidl_portlayer = 41
do_write_ports = True

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
        if issubclass(celltype, (phidl.Device, phidl.device_layout.DeviceReference)):
            if do_write_ports:
                def write_with_ports(device, filename, *args, port_layer=None, **kwargs):
                    if port_layer is None:
                        port_layer = default_phidl_portlayer
                    # If its a reference, use its parent
                    if issubclass(celltype, phidl.device_layout.DeviceReference):
                        device = device.parent
                    # Try to convert to geometric ports
                    try:
                        port2geom = phidl.geometry.ports_to_geometry
                    except AttributeError:  # it is an older version of phidl
                        pass
                    else:
                        device = port2geom(device, layer=port_layer)
                    # The actual write
                    device.write_gds(filename, *args, **kwargs)
                return write_with_ports
            else:
                def write_parent(device, filename, *args, **kwargs):
                    # If its a reference, use its parent
                    if issubclass(celltype, phidl.device_layout.DeviceReference):
                        device = device.parent
                    device.write_gds(filename, *args, **kwargs)
                return write_parent

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
                    wop = phidl.geometry.geometry_to_ports
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
    global do_write_ports
    do_write_ports_orig = do_write_ports
    do_write_ports = True
    tempfile = os.path.expanduser('~/temp_cellTranslation.gds')
    any_write(initial_cell, tempfile)
    new_cell = any_read(final_cell, tempfile)
    os.remove(tempfile)
    do_write_ports = do_write_ports_orig

    # Transfer other data (ports, metadata, CML files, etc.)
    pass  # TODO

    return new_cell


def phidl2pya_flat(cell, device):
    ''' Inserts polygons from a phidl device into an existing pya cell.
        It is simpler than going through GDS, but it is rudimentary.
        No positioning control. No cell references: auto-flatten.
        Make sure the Device is moved to the desired location before converting.
        If you have zeropdk, returns zeropdk.Ports corresponding to the top-level phidl Ports

            Cel = pya.Layout().create_cell('name')
            Dev = phidl.geometry.rectangle((10, 10))
            phidl2pya_flat(Cel, Dev)
    '''
    import pya
    device = device.flatten()
    for container in device.polygons:
        for lay, dtyp, shape in zip(container.layers, container.datatypes, container.polygons):
            pya_layer = cell.layout().layer(lay, dtyp)
            poly_dpts = [pya.DPoint(*f) for f in shape]
            dpoly = pya.DSimplePolygon(poly_dpts)
            dpoly.layout(cell, pya_layer)
    try:
        from zeropdk.pcell import Port
    except ImportError:
        return None
    else:
        ports = []
        for nam, po in device.ports.items():
            normal_vec = pya.DVector(*(po.normal[1] - po.normal[0]))
            pyapo = Port(nam, pya.DPoint(*po.midpoint), normal_vec, po.width)
            ports.append(pyapo)
        return ports
