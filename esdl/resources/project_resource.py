#  This work is based on original code developed and copyrighted by TNO 2020.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO
"""
The xmi module introduces XMI resource and XMI parsing.
"""
from enum import unique, Enum
from uuid import uuid4

from lxml.etree import parse
from pyecore.ecore import EProxy

from esdl.processing.string_uri import StringURI
from esdl.resources.resource_type import ProjectManagerResourceType
from esdl.resources.xmlresource import XMLResource

XSI = 'xsi'
XSI_URL = 'http://www.w3.org/2001/XMLSchema-instance'
XMI = 'xmi'
XMI_URL = 'http://www.omg.org/XMI'


@unique
class XMIOptions(Enum):
    OPTION_USE_XMI_TYPE = 0
    SERIALIZE_DEFAULT_VALUES = 1


class ProjectResource(XMLResource):
    """
    Project Resource is a copy of the XMI Resource, but with some special handling for dealing with
    non-unique IDs in a project in which the same energy system is stored more than once. (i.e. two variant collections
    with (more or less) the same energy system (e.g. shared
    """
    def __init__(self, uri=None, use_uuid=False):
        super().__init__(uri, use_uuid)
        self._later = []
        self.prefixes = {}
        self.reverse_nsmap = {}
        self.es_resources = []
        self.type: ProjectManagerResourceType = ProjectManagerResourceType.PROJECT

    def load(self, options=None):
        self.options = options or {}
        self.cache_enabled = True
        tree = parse(self.uri.create_instream())
        xmlroot = tree.getroot()
        self.prefixes.update(xmlroot.nsmap)
        self.reverse_nsmap = {v: k for k, v in self.prefixes.items()}

        self.xsitype = f'{{{self.prefixes.get(XSI)}}}type'
        self.xmiid = f'{{{self.prefixes.get(XMI)}}}id'
        self.schema_tag = f'{{{self.prefixes.get(XSI)}}}schemaLocation'


        # Decode the XMI
        if f'{{{self.prefixes.get(XMI)}}}XMI' == xmlroot.tag:
            real_roots = xmlroot
        else:
            real_roots = [xmlroot]

        def grouper(iterable):
            args = [iter(iterable)] * 2
            return zip(*args)

        self.schema_locations = {}
        schema_tag_list = xmlroot.attrib.get(self.schema_tag, '')
        for prefix, path in grouper(schema_tag_list.split()):
            if '#' not in path:
                path = path + '#'
            self.schema_locations[prefix] = EProxy(path, self)

        energysystems = []
        for variant_coll in xmlroot:
            if variant_coll.tag == 'variantCollection':
                for tag in list(variant_coll):
                    if tag.tag == "energysystem":
                        tag.tag = '{http://www.tno.nl/esdl}EnergySystem'  # update tag to parse it as a separate XMLResource
                        variant_coll.remove(tag)  # remove tag from parsing
                        energysystems.append(tag)

        #real_roots = energysystems
        for i, es_tree in enumerate(energysystems):
            #resource = XMLResource(StringURI(f"VariantCollection_{i}.esdl"))
            resource = self.resource_set.create_resource(StringURI(f"VariantCollection.{i}_{str(uuid4())[:4]}.esdl"))
            if not isinstance(resource, XMLResource):
                raise TypeError(f"EnergySystem Resource should be of type XMLResource, not {type(resource)}")
            resource.load_subtree(xmlroot, es_tree)
            self.es_resources.append(resource)

        for root in real_roots:
            modelroot = self._init_modelroot(root)
            for child in root:
                self._decode_eobject(child, modelroot)

        if self.contents:
            self._decode_ereferences()
            for i, resource in enumerate(self.es_resources):
                # reassign the parsed data back to the now loaded project
                if self.contents[0].variantCollection:
                    self.contents[0].variantCollection[i].energysystemRef = resource.contents[0]

        self._clean_registers()
        self.uri.close_stream()

    def __str__(self):
        return f'ProjectResource(type={self.type}, uri={self.uri}, content[0]={self.contents[0].name if len(self.contents) > 0 else None})'

