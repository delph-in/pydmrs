import xml.etree.ElementTree as ET

from pydmrs.core import Link, ListDmrs, Node
from pydmrs._exceptions import PydmrsValueError


def loads_xml(bytestring, encoding=None, cls=ListDmrs, convert_legacy_prontype=True, **kwargs):
    """
    Currently processes "<dmrs>...</dmrs>"
    To be updated for "<dmrslist>...</dmrslist>"...
    Expects a bytestring; to load from a string instead, specify encoding
    Produces a ListDmrs by default; for a different type, specify cls
    """
    if encoding:
        bytestring = bytestring.encode(encoding)
    xml = ET.XML(bytestring)

    dmrs = cls(**kwargs)

    dmrs.cfrom = int(xml.get('cfrom')) if 'cfrom' in xml.attrib else None
    dmrs.cto = int(xml.get('cto')) if 'cto' in xml.attrib else None
    dmrs.surface = xml.get('surface')
    dmrs.ident = int(xml.get('ident')) if 'ident' in xml.attrib else None
    index_id = int(xml.get('index')) if 'index' in xml.attrib else None
    top_id = None

    for elem in xml:
        if elem.tag == 'node':
            node = Node.from_xml(elem, convert_legacy_prontype)
            dmrs.add_node(node)

        elif elem.tag == 'link':
            link = Link.from_xml(elem)
            if link.start == 0:
                top_id = link.end
            else:
                dmrs.add_link(link)
        else:
            raise PydmrsValueError(elem.tag)

    if top_id:
        dmrs.top = dmrs[top_id]
    if index_id:
        dmrs.index = dmrs[index_id]

    return dmrs


def load_xml(filehandle, cls=ListDmrs, **kwargs):
    """
    Load a DMRS from a file
    NB: read file as bytes!
    Produces a ListDmrs by default; for a different type, specify cls
    """
    return cls.loads(filehandle.read(), cls=cls, **kwargs)


def dumps_xml(dmrs, encoding=None):
    """
    Currently creates "<dmrs>...</dmrs>"
    To be updated for "<dmrslist>...</dmrslist>"...
    Returns a bytestring; to return a string instead, specify encoding
    """
    xdmrs = ET.Element('dmrs')
    if dmrs.index is not None:
        xdmrs.set('index', str(dmrs.index.nodeid))
    if dmrs.cfrom is not None and dmrs.cto is not None:
        xdmrs.set('cfrom', str(dmrs.cfrom))
        xdmrs.set('cto', str(dmrs.cto))
    for nodeid in sorted(dmrs):
        node = dmrs[nodeid]
        xnode = node.to_xml()
        xdmrs.append(xnode)
    if dmrs.top is not None:
        xlink = ET.SubElement(xdmrs, 'link')
        xlink.set('from', '0')
        xlink.set('to', str(dmrs.top.nodeid))
        xrargname = ET.SubElement(xlink, 'rargname')
        xpost = ET.SubElement(xlink, 'post')
        xpost.text = 'H'
    for link in dmrs.iter_links():
        xlink = link.to_xml()
        xdmrs.append(xlink)
    bytestring = ET.tostring(xdmrs)
    if encoding:
        return bytestring.decode(encoding)
    return bytestring


def dump_xml(filehandle, dmrs):
    """
    Dump a DMRS to a file
    NB: write as a bytestring!
    """
    filehandle.write(dumps_xml(dmrs))


def visualise(dmrs, format):
    """
    Returns the bytestring of the chosen visualisation representation.
    Supported formats: dot
    """
    if format == 'dot':
        dot_strs = []
        dot_strs.append('digraph g {\n')
        if dmrs.top is not None:
            dot_strs.append('NodeTop [label="top",style=bold];\n')
        dot_strs.append('node[shape=box];\n')
        for nodeid in dmrs:
            node = dmrs[nodeid]
            dot_strs.append('Node{} [label=<{}{}<BR /><FONT POINT-SIZE="10">{}</FONT>>];\n'.format(str(nodeid).replace('-', 'M'), node.pred, '("{}")'.format(node.carg) if node.carg else '', node.sortinfo))
        dot_strs.append('edge[fontsize=10];\n')
        if dmrs.top is not None:
            dot_strs.append('NodeTop -> Node{} [style=dotted];\n'.format(str(dmrs.top.nodeid).replace('-', 'M')))
        for link in dmrs.links:
            dot_strs.append('Node{} -> Node{} [label="{}"];\n'.format(str(link.start).replace('-', 'M'), str(link.end).replace('-', 'M'), link.labelstring))
        dot_strs.append('}\n')
        dot_str = ''.join(dot_strs)
        return dot_str.encode()
    else:
        raise PydmrsValueError('Visualisation format not supported')
