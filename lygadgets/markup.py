
import xmltodict

def xml_to_dict(xml_content):
    raise RuntimeError('lygadgets.markup.xml_to_dict is deprecated. Use the xmltodict package')
    # return xmltodict.parse(xml_content, process_namespaces=True)


def lyp_to_layerlist(lyp_file):
    ''' Now works with multiple tabs. It ignores the tab names '''
    with open(lyp_file, 'r') as fx:
        lyp_dict = xmltodict.parse(fx.read(), process_namespaces=True)
    all_layers = []
    if 'layer-properties-tabs' in lyp_dict.keys():
        all_layer_tabs = lyp_dict['layer-properties-tabs']['layer-properties']
    else:
        all_layer_tabs = [lyp_dict['layer-properties']]

    for tab in all_layer_tabs:
        tab_layers = tab['properties']
        if not isinstance(tab_layers, list):
            tab_layers = [tab_layers]
        all_layers.extend(tab_layers)
    return all_layers
