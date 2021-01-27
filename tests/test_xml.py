import xmlschema

import tom.config as config
from tom.tom import Train, TSI_SCHEMA_VERSION
from xml.etree import ElementTree

from tom.util import xml_to_string


def taftap_schema():
    taf_cat = 'taf_cat_complete_sector.xsd'
    xs = xmlschema.XMLSchema(f"data/xml/{taf_cat}")
    return taf_cat, xs


def _test_xmlschema():
    taf_cat, xs = taftap_schema()
    assert xs.target_namespace == 'http://taf-jsg.info/schemes'
    assert xs.name == taf_cat
    assert xs.version == TSI_SCHEMA_VERSION
    ri = xs.elements.get('TrainInformation')
    assert ri is not None
    version = ri.get('RouteInfoVersion')
    assert version.name == 'RouteInfoVersion'

    child_names = [n.local_name for n in ri.iter()]
    assert child_names == ['TrainInformation',
                           'RouteSection',
                           'SectionID',
                           'PlannedJourneyLocation',
                           'PlannedCalendar',
                           'Successors',
                           'SectionID',
                           'Route',
                           'PlannedCalendar',
                           'PlannedJourneyLocation']


def check_xml_instance_to_dict(xml_element):
    _, xs = taftap_schema()
    r = xs.to_dict(xml_element)
    assert r['@xmlns'] == xs.target_namespace
    assert r['@version'] == TSI_SCHEMA_VERSION
    assert r['@RouteInfoVersion'] == 1
    sections = r['RouteSection']
    assert len(sections) == 4
    first_section = sections[0]
    assert first_section['@SectionVersion'] == 1
    assert len(first_section['PlannedJourneyLocation']) == 2
    calendar = first_section['PlannedCalendar']
    assert calendar['BitmapDays'] == '110001111000111100011110001111'
    # assert calendar['ri:ValidityPeriod'] == 22


def _test_simple():
    check_xml_instance_to_dict('../build/TR-12AB-1/ri-TR-12AB-1.xml')


def test_all_to_xml(all_trains):
    t: Train = all_trains
    __to_xml_and_check(t)


def test_ac_ff_to_xml(train_ac_ff):
    t: Train = train_ac_ff
    __to_xml_and_check(t, do_check=False)


def __to_xml_and_check(t: Train, do_check=False):
    xml: ElementTree.Element = t.routing_info_to_xml(schema="file:///../tests/data/xml")
    xml_as_string = xml_to_string(xml)
    config.output_file("")
    xml_file = config.output_file(f"ri-{t.id()}", subdir=t.id(), suffix="xml")
    with open(xml_file, "w") as f:
        f.write(xml_as_string)
    if do_check:
        check_xml_instance_to_dict(xml)
