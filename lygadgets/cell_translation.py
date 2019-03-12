''' Translation functions that take Cells/Devices in different types of languages
    and convert them to Cells/Devices in other languages

    Supported: phidl, pya (GSI version), klayout.db (standalone version)
    Not yet supported: nazca, IPKISS, gdspy, other suggestions?
'''
import os
import pya
import json

### support port translation in phidl ###
from phidl import geometry as pg, Device, Port
phidl_port_layer, phidl_port_datatype = None, 0

def port_to_labeltext(port):
    essential_info = (str(port.name),
                      # port.midpoint,  # rather than put this in the text, use the label position
                      float(port.width),
                      float(port.orientation),
                      # port.parent,  # this is definitely not serializable
                      # port.info,  # would like to include, but it might go longer than 1024 characters
                      # port.uid,  # not including because it is part of the build process, not the port state
                     )
    return json.dumps(essential_info)


def port_from_labeltext(label_text):
    # You will have to set the midpoint elsewhere
    name, width, orientation = json.loads(label_text)
    return Port(name=name, width=width, orientation=orientation)


def draw_port(port, layer=None):
    ''' Puts a triangle down in the actual geometry that will go to GDS.
        Similar to what quickplot does
    '''
    if port.parent is None:
        raise ValueError('Port {}: Port needs a parent in which to draw'.format(self.name))
    triangle_points = [[0, 0]] * 3
    triangle_points[0] = port.endpoints[0]
    triangle_points[1] = port.endpoints[1]
    triangle_points[2] = (port.midpoint + (port.normal - port.midpoint) * port.width / 10)[1]
    port.parent.add_polygon(triangle_points, layer)
    port.parent.label(text=port_to_labeltext(port), position=port.midpoint, layer=layer)


def phidl_write_gds_and_metadata(device, filename, *args, **kwargs):
    referenced_cells = list(device.get_dependencies(recursive=True))
    all_cells = [device] + referenced_cells
    # Insert GDS-visible ports
    if phidl_port_layer is not None:
        for cell in all_cells:
            for port in cell.ports.values():
                draw_port(port, layer=phidl_port_layer)

    ### This is the primary wrapped phidl function
    kwargs['auto_rename'] = kwargs.get('auto_rename', False)  # we don't want that extra hierarchy layer, 'topcell'
    device.write_gds(filename, *args, **kwargs)
    ###

    # Take port geometry back out
    if phidl_port_layer is not None:
        for cell in all_cells:
            cell.remove_layers(layers=[phidl_port_layer])


def phidl_import_gds_and_metadata(filename, cellname=None, flatten=False):
    device = pg.import_gds(filename, cellname=cellname, flatten=flatten)
    referenced_cells = list(device.get_dependencies(recursive=True))
    all_cells = [device] + referenced_cells
    for subcell in all_cells: # Walk through cells
        # Extract GDS-visible ports
        if phidl_port_layer is not None:
            for lab in subcell.labels:
                if lab.layer == phidl_port_layer:
                    the_port = port_from_labeltext(lab.text)
                    the_port.midpoint = lab.position
                    subcell.add_port(port=the_port)
            subcell.remove_layers(layers=[phidl_port_layer])
    return device


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
            return phidl_write_gds_and_metadata

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
            def phidlDevice_reader(phidl_device, filename, *args, **kwargs):
                #### hacks, because sometimes pya saves an extra topcell called $$$CONTEXT_INFO$$$
                from gdspy import GdsLibrary
                gdsii_lib = GdsLibrary()
                gdsii_lib.read_gds(filename)
                top_level_cells = gdsii_lib.top_level()
                if len(top_level_cells) == 1:
                    cellname = top_level_cells[0].name
                if len(top_level_cells) == 2:
                    for tc in top_level_cells:
                        if tc.name != '$$$CONTEXT_INFO$$$':
                            cellname = tc.name
                #### end hacks
                tempdevice = phidl_import_gds_and_metadata(filename, *args, cellname=cellname, **kwargs)
                for e in tempdevice.elements:
                    phidl_device.elements.append(e)
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
