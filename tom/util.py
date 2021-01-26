import os
from pathlib import Path
from xml.etree import ElementTree

from tom.tom import Train


def example(data_dir, pattern):
    train_specs = os.listdir(data_dir)
    t_spec_file = data_dir + '/'
    t_spec_file += next(spec for spec in train_specs if pattern in spec)
    return train_specs, Path(t_spec_file)


def __indent_xml(elem, level=0):
    i = "\n" + level * "  "
    j = "\n" + (level - 1) * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for sub_elem in elem:
            __indent_xml(sub_elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem


def xml_to_string(xml: ElementTree.Element) -> str:
    __indent_xml(xml)
    return ElementTree.tostring(xml, encoding='unicode', method='xml')


def dump_routing_info_as_xml(t: Train) -> str:
    x: ElementTree.Element = t.routing_info_to_xml(schema="file:///../tests/data/xml")
    return xml_to_string(x)
