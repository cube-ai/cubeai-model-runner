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
'''
Provides model runner API implementations
'''
from functools import partial

from flask import current_app, send_from_directory, request, abort, Response
from google.protobuf.message import DecodeError
from google.protobuf.json_format import ParseError


_PROTO = 'application/vnd.google.protobuf'
_JSON = 'application/json'
_VALID_MEDIA = {_PROTO, _JSON}


def methods(method_name):
    '''Generic handler for model methods'''
    content_type = _get_header('Content-Type')
    accept = _get_header('Accept')

    data = request.data
    method = current_app.model.methods[method_name]

    try:
        wrapped_resp = method.from_pb_bytes(data) if content_type == _PROTO else method.from_json(data)
    except DecodeError as err:
        abort(Response("Could not decode input protobuf message: {}".format(err), 400))
    except ParseError as err:
        abort(Response("Could not parse input JSON message: {}".format(err), 400))
    except Exception as err:
        abort(Response("Could not invoke method due to runtime error: {}".format(err), 400))

    resp_data = wrapped_resp.as_pb_bytes() if accept == _PROTO else wrapped_resp.as_json()
    return Response(resp_data, status=200, content_type=accept)


def _get_header(name):
    '''Returns a given request header'''
    header = request.headers.get(name)
    if header is None:
        abort(Response("Header '{}' is required".format(name), 400))
    if header not in _VALID_MEDIA:
        abort(Response("Header '{}' must be one of {}".format(name, _VALID_MEDIA), 415))
    return header


def artifacts(filename, mimetype=None):
    '''Generic handler for model artifacts'''
    return send_from_directory(current_app.model_dir, filename, mimetype=mimetype)


metadata = partial(artifacts, filename='metadata.json', mimetype=_JSON)
protobuf = partial(artifacts, filename='model.proto', mimetype='text/plain')
