import xmltodict

def xml_to_dict(xml_content):
    return xmltodict.parse(xml_content, process_namespaces=True)
