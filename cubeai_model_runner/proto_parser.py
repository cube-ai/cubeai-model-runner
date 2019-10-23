# -*- coding: utf-8 -*-
# ===============LICENSE_START=======================================================
# Acumos Apache-2.0
# ===================================================================================
# Copyright (C) 2017-2018 AT&T Intellectual Property & Tech Mahindra. All rights reserved.
# ===================================================================================
# This Acumos software file is distributed by AT&T and Tech Mahindra
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============LICENSE_END=========================================================
"""
Provides utilities for parsing protobuf IDL
"""
from collections import namedtuple

from lark import Lark, Transformer

from .utils import load_data


Enum = namedtuple('Enum', 'name, enums')
Message = namedtuple('Message', 'name, fields, messages, enums')
Field = namedtuple('Field', 'type, name, number')
RepeatedField = namedtuple('RepeatedField', 'type, name, number')
MapField = namedtuple('MapField', 'key_type, val_type, name, number')

_PROTO_GRAMMAR = load_data('proto3.ebnf')


class ProtoTransformer(Transformer):
    '''Converts syntax tree token into more easily usable namedtuple objects'''

    def message(self, tokens):
        '''Returns a Message namedtuple'''
        name_token, body = tokens
        return Message(name_token.value, *body)

    def messagebody(self, items):
        '''Returns a tuple of message body namedtuples'''
        messages = []
        enums = []
        fields = []
        for item in items:
            if isinstance(item, Message):
                messages.append(item)
            elif isinstance(item, Enum):
                enums.append(item)
            elif isinstance(item, (Field, RepeatedField, MapField)):
                fields.append(item)
        return fields, messages, enums

    def field(self, tokens):
        '''Returns a Field namedtuple'''
        type_, fieldname, fieldnumber = (token.value for token in tokens)
        return Field(type_, fieldname, int(fieldnumber))

    def repeatedfield(self, field):
        '''Returns a RepeatedField namedtuple'''
        return RepeatedField(*field[0])

    def mapfield(self, tokens):
        '''Returns a MapField namedtuple'''
        key_type, val_type, fieldname, fieldnumber = (token.value for token in tokens)
        return MapField(key_type, val_type, fieldname, int(fieldnumber))

    def enum(self, tokens):
        '''Returns an Enum namedtuple'''
        name, enums = tokens
        return Enum(name.value, enums)

    def enumbody(self, tokens):
        '''Returns a sequence of enum identifiers'''
        enums = [enumfield.children[0].value for enumfield in tokens if enumfield.data == 'enumfield']
        return enums


def parse_proto(proto_idl):
    '''Returns a sequence of top-level protobuf definitions, i.e. Message or Enum namedtuples'''
    parser = Lark(_PROTO_GRAMMAR, start='proto', parser='lalr')
    tree = parser.parse(proto_idl)
    trans_tree = ProtoTransformer().transform(tree)
    top_level = [child for top_level in trans_tree.find_data('topleveldef')
                 for child in top_level.children if isinstance(child, (Message, Enum))]
    return top_level
