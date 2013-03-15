#!/usr/bin/env python
#
# Copyright 2011 Anton Romanov

from lxml import etree
#import xml.etree.ElementTree as etree

class Manifest:
    def __init__(self,xml=None,os=None,arch=None):
        if not xml:
            self.os = os
            self.arch = arch
            self.files = {}
            self.version = '0.0.0'
        else:
            if xml is not None:
                root = etree.parse(xml).getroot()
            self.version = root.attrib['version']
            self.arch = root.attrib['arch']
            self.os = root.attrib['os']
            files = {}
            for e in root:
                if e.tag == 'file':
                    files[e.attrib['path']] = e.attrib
            self.files = files


