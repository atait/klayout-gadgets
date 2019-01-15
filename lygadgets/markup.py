import xmltodict

def xml_to_dict(xml_content):
    # to be deprecated
    return xmltodict.parse(xml_content, process_namespaces=True)


def lyp_to_layerlist(lyp_file):
    with open(lyp_file, 'r') as fx:
        lyp_dict = xmltodict.parse(fx.read(), process_namespaces=True)
    all_layers = lyp_dict['layer-properties']['properties']
    return all_layers
