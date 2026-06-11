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

import logging

from lxml.etree import QName, Element, ElementTree
from pyecore.ecore import EObject, EProxy
from pyecore.resources.xmi import XMIResource, XMIOptions, XMI_URL, XSI_URL, XSI, XMI

from esdl.resources.resource_type import ProjectManagerResourceType
from utils.utils import timed

logger = logging.getLogger(__name__)



"""
Extension of pyecore's XMIResource to support the XMLResource in EMF.
It basically removes the xmi:version stuff from the serialization.
It also adds parse_information that can be inspected for errors when reading an ESDL file.
"""
class XMLResource(XMIResource):
    type: ProjectManagerResourceType = ProjectManagerResourceType.UNKNOWN

    def __init__(self, uri=None, use_uuid=False):
        super().__init__(uri, use_uuid)
        self._later = []
        self.prefixes = {}
        self.reverse_nsmap = {}
        self.parse_information = []

    def set_content(self, root):
        if not isinstance(root, EObject):
            raise ValueError('The resource requires an EObject type, '
                             f'but received {type(root)} instead.')
        if len(self.contents) > 0 and self.contents[0]:
            self.remove(self.contents[0])
        self.contents.insert(0, root)
        root._eresource = self
        if root._container is not None:
            container = root._container
            feature = root._containment_feature
            if feature.many:
                container.eGet(feature).remove(root)
            else:
                container.eSet(feature, None)
            root._container = None # as root is added to the resource, there is no container anymore

    def set_content_without_detaching(self, root: EObject):
        """
        This function sets the content 'root' to an eObject in that is contained in another resource, but does
        not move the eObject to this resource.
        This function allows to serialize parts of an ESDL without deepcopying it to avoid moving it to a different resource
        Parameters
        ----------
        root: EObject to seralize

        Returns
        -------

        """
        if not isinstance(root, EObject):
            raise ValueError('The resource requires an EObject type, '
                             f'but received {type(root)} instead.')
        self.contents.clear()
        self.contents.insert(0, root)

    def __str__(self):
        return f'XMLResource(type={self.type}, uri={self.uri}, content[0]={self.contents[0].name if len(self.contents) > 0 else None})'

    def get_parse_information(self):
        return self.parse_information

    def load_subtree(self, original_root, sub_tree, options=None):
        """
        Loads a subtree of an XML as a resource, e.g. the energysystems in a Project's variant collection
        See Also ProjectResource that uses this function
        """
        self.type = ProjectManagerResourceType.VARIANT_COLLECTION
        self.options = options or {}
        self.cache_enabled = True
        self.prefixes.update(original_root.nsmap)
        self.reverse_nsmap = {v: k for k, v in self.prefixes.items()}

        self.xsitype = f'{{{self.prefixes.get(XSI)}}}type'
        self.xmiid = f'{{{self.prefixes.get(XMI)}}}id'
        self.schema_tag = f'{{{self.prefixes.get(XSI)}}}schemaLocation'

        # Decode the XMI
        # if f'{{{self.prefixes.get(XMI)}}}XMI' == xmlroot.tag:
        #     real_roots = xmlroot
        # else:
        #     real_roots = [xmlroot]
        real_roots = [sub_tree]

        def grouper(iterable):
            args = [iter(iterable)] * 2
            return zip(*args)

        self.schema_locations = {}
        schema_tag_list = original_root.attrib.get(self.schema_tag, '')
        for prefix, path in grouper(schema_tag_list.split()):
            if '#' not in path:
                path = path + '#'
            self.schema_locations[prefix] = EProxy(path, self)

        for root in real_roots:
            modelroot = self._init_modelroot(root)
            for child in root:
                self._decode_eobject(child, modelroot)

        if self.contents:
            self._decode_ereferences()

        self._clean_registers()
        self.uri.close_stream()


    def save(self, output=None, options=None):
        self.options = options or {}
        output = self.open_out_stream(output)
        self.prefixes.clear()
        self.reverse_nsmap.clear()

        serialize_default = \
            self.options.get(XMIOptions.SERIALIZE_DEFAULT_VALUES,
                             False)
        nsmap = {XSI: XSI_URL} # remove XMI for XML serialization

        if len(self.contents) == 1:
            root = self.contents[0]
            self.register_eobject_epackage(root)
            tmp_xmi_root = self._go_across(root, serialize_default)
        else:
            # this case hasn't been verified for XML serialization
            tag = QName(XMI_URL, 'XMI')
            tmp_xmi_root = Element(tag)
            for root in self.contents:
                root_node = self._go_across(root, serialize_default)
                tmp_xmi_root.append(root_node)

        # update nsmap with prefixes register during the nodes creation
        nsmap.update(self.prefixes)
        xmi_root = Element(tmp_xmi_root.tag, nsmap=nsmap)
        xmi_root[:] = tmp_xmi_root[:]
        xmi_root.attrib.update(tmp_xmi_root.attrib)
        #xmi_version = etree.QName(XMI_URL, 'version') # remove XMI version in XML serialization
        #xmi_root.attrib[xmi_version] = '2.0'
        tree = ElementTree(xmi_root)
        tree.write(output,
                   pretty_print=True,
                   xml_declaration=True,
                   encoding=tree.docinfo.encoding)
        output.flush()
        return self.uri.close_stream()

    """
    This function has been overriden XMIResource, to make it a little more robust for ESDL's that
    are 'older' and do not have a certain feature. By default XMIResource throws an exception when 
    an unknown attribute is found for a class. This version prints a warning and continues.
    """
    def _decode_attribute(self, owner, key, value, node):
        namespace, att_name = self.extract_namespace(key)
        prefix = self.reverse_nsmap[namespace] if namespace else None
        # This is a special case, we are working with uuids
        if key == self.xmiid:
            owner._internal_id = value
            self.uuid_dict[value] = owner
        elif prefix in ('xsi', 'xmi') and att_name == 'type':
            # type has already been handled
            pass
        # elif namespace:
        #     pass
        elif not namespace:
            if att_name == 'href':
                return
            feature = self._find_feature(owner.eClass, att_name)
            if not feature:
                #raise ValueError(f'Feature {att_name} does not exists for '
                #                 f'type {owner.eClass.name} '
                #                 f'({node.tag} line {node.sourceline})')
                s = 'Attribute \'{0}\' does not exists for type {1} and is ignored ({2} line {3}).'\
                    .format(att_name, owner.eClass.name, node.tag, node.sourceline)
                logger.warning(s)
                self.parse_information.append(s)
            return feature

