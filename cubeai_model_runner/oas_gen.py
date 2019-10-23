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
Provides utilities for generating an Open API specification from protobuf IDL and model metadata
"""
import yaml
from collections import namedtuple

from jinja2 import Environment, FileSystemLoader

from .proto_parser import Message, RepeatedField, MapField, Enum, parse_proto
from .utils import data_path


class TemplateError(Exception):
    pass


_OasFormat = namedtuple('_OasFormat', 'type, format, description')
_OasFormat.__new__.__defaults__ = (None, None, None)

_64NOTE = 'Note: 64-bit integers are string-encoded when using application/json'

_PROTO_OAS_MAP = {
    'double': _OasFormat('number', 'double'),
    'float': _OasFormat('number', 'float'),
    'int32': _OasFormat('integer', 'int32'),
    'int64': _OasFormat('integer', 'int64', _64NOTE),
    'uint32': _OasFormat('integer', 'int32'),
    'uint64': _OasFormat('integer', 'int64', _64NOTE),
    'sint32': _OasFormat('integer', 'int32'),
    'sint64': _OasFormat('integer', 'int64', _64NOTE),
    'fixed32': _OasFormat('integer', 'int32'),
    'fixed64': _OasFormat('integer', 'int64', _64NOTE),
    'sfixed32': _OasFormat('integer', 'int32'),
    'sfixed64': _OasFormat('integer', 'int64', _64NOTE),
    'bool': _OasFormat('boolean'),
    'string': _OasFormat('string'),
    'bytes': _OasFormat('string', 'byte')}


def create_oas(metadata, protobuf):
    '''Returns an OAS YAML string'''
    top_level = parse_proto(protobuf)
    defs = _create_definitions(top_level)

    defs_yaml = yaml.dump(defs, default_flow_style=False)
    methods = [_format_method(name, method) for name, method in metadata['methods'].items()]

    env = Environment(loader=FileSystemLoader(data_path('templates')), trim_blocks=True)
    return env.get_template('base.yaml').render(model=metadata, methods=methods, definitions=defs_yaml)


def _format_method(name, method):
    '''Returns a method dict to be used in the method template'''
    method_fmt = dict(name=name, **method)
    for key in ('input', 'output'):
        method_fmt[key] = _prefix_name(method[key])
    return method_fmt


def _create_definitions(top_level):
    '''Returns OAS definitions for all protobuf top-level definitions'''
    refs = {ref for item in top_level for ref in _find_refs(item)}
    defs = {name: definition for item in top_level for name, definition in _find_definitions(item, refs)}
    defs_prefixed = {_prefix_name(key): val for key, val in defs.items()}
    return defs_prefixed


def _find_refs(item, root=()):
    '''Yields tuples representing a hierarchy of custom named types'''
    yield root + (item.name, )
    if isinstance(item, Message):
        child_root = root + (item.name, )
        for enum in item.enums:
            yield child_root + (enum.name, )
        for msg in item.messages:
            yield from _find_refs(msg, child_root)


def _find_definitions(item, refs, prefix=()):
    '''Yields OAS definitions contained within a top-level protobuf definition'''
    if isinstance(item, Message):
        yield from _find_message_definitions(item, refs, prefix)
    elif isinstance(item, Enum):
        yield _define_enum(item, prefix)
    else:
        raise TemplateError("Cannot create definition item {}".format(item))


def _find_message_definitions(message, refs, prefix):
    '''Yields OAS definitions contained within to a protobuf message'''
    scope = prefix + (message.name, )

    for enum in message.enums:
        yield _define_enum(enum, scope)

    for msg in message.messages:
        yield from _find_message_definitions(msg, refs, scope)

    properties = {field.name: _define_field(field, refs, scope) for field in message.fields}

    def_obj = {'type': 'object', 'properties': properties, 'required': sorted(properties.keys())}
    def_name = ".".join(scope)
    yield def_name, def_obj


def _define_enum(enum, prefix):
    '''Returns an OAS object corresponding to a protobuf enum'''
    def_name = ".".join(prefix + (enum.name, ))
    return def_name, {'type': 'string', 'enum': enum.enums}


def _define_field(field, refs, prefix):
    '''Returns an OAS object corresponding to a protobuf field'''
    if isinstance(field, MapField):
        field_type = _resolve_type(field.val_type, refs, prefix)
        return {'type': 'object', 'additionalProperties': field_type}
    else:
        field_type = _resolve_type(field.type, refs, prefix)
        if isinstance(field, RepeatedField):
            return {'type': 'array', 'items': field_type}
        else:
            return field_type


def _resolve_type(type_name, refs, prefix):
    '''Returns an OAS object corresponding to a protobuf type. Returns a reference for named types'''
    if type_name in _PROTO_OAS_MAP:
        oas_type = _PROTO_OAS_MAP[type_name]
        return {k: v for k, v in oas_type._asdict().items() if v is not None}
    else:
        ref_tuple = _resolve_named_type(type_name, refs, prefix)
        ref_str = "#/definitions/{}".format(_prefix_name(".".join(ref_tuple)))
        return {'$ref': ref_str}


def _resolve_named_type(type_name, refs, prefix):
    '''Returns the full identifier for a given named type'''
    type_idents = tuple(type_name.split('.'))

    # look within the most local scope first, and gradually move towards global scope
    for i in reversed(range(len(prefix) + 1)):
        full_ident = prefix[:i] + type_idents
        if full_ident in refs:
            return full_ident
    else:
        raise TemplateError("Failed to find a reference for named type {}".format('/'.join(prefix + type_idents)))


def _prefix_name(name):
    '''Adds a "Model" prefix to type names to avoid naming collisions'''
    return "Model.{}".format(name)
