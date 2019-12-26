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
Provides a model runner based on a connexion application and gunicorn server
'''
import os
import json
import argparse
from functools import partial
from os.path import abspath, join as path_join

from gunicorn.app.base import BaseApplication
from connexion import App
from connexion.resolver import Resolver
from swagger_ui_bundle import swagger_ui_3_path as swagger_ui_path
from flask import redirect, Blueprint, render_template
from flask_cors import CORS
from ucumos.wrapped import load_model

from .api import methods
from .oas_gen import create_oas


def run_app_cli():
    '''CLI entry point for starting the model runner'''
    parser = argparse.ArgumentParser()
    parser.add_argument('model_dir', type=str, help='Directory containing a dumped CubeAI Python model')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='The interface to bind to')
    parser.add_argument('--port', type=int, default=3330, help='The port to bind to')
    parser.add_argument('--workers', type=int, default=1, help='The number of gunicorn workers to spawn')
    parser.add_argument('--timeout', type=int, default=120, help='Time to wait (seconds) before a frozen worker is restarted')
    parser.add_argument('--cors', type=str, default=None, help="Enables CORS if provided. Can be a domain, comma-separated list of domains, or '*'")

    pargs = parser.parse_args()

    app = create_app(**vars(pargs))
    app.run()


def create_app(model_dir, host, port, workers=1, timeout=120, cors=None):
    '''Creates and returns the model runner gunicorn application

    Parameters
    ----------
    model_dir : str
        Directory containing a dumped CubeAI Python model
    host : str
        The interface to bind to
    port : int
        The port to bind to
    workers : int, optional
        The number of gunicorn workers to spawn
    timeout : int, optional
        Time to wait (seconds) before a frozen worker is restarted
    cors : str, optional
        Enables CORS if provided. Can be a domain, comma-separated list of domains, or '*'
    '''
    model_dir = abspath(model_dir)
    _write_oas(model_dir)
    return StandaloneApplication(model_dir, host, port, workers, timeout, cors)


def _write_oas(model_dir):
    '''Writes an Open API specification file the model directory'''
    with open(path_join(model_dir, 'metadata.json')) as file:
        metadata = json.load(file)

    with open(path_join(model_dir, 'model.proto')) as file:
        proto = file.read()

    oas_yaml = create_oas(metadata, proto)
    with open(path_join(model_dir, 'oas.yaml'), 'w') as file:
        file.write(oas_yaml)


class StandaloneApplication(BaseApplication):
    '''Custom gunicorn app. Modified from http://docs.gunicorn.org/en/stable/custom.html'''

    def __init__(self, model_dir, host, port, workers, timeout, cors):
        self.model_dir = model_dir
        self.cors = cors
        self.options = {'bind': "{}:{}".format(host, port), 'workers': workers, 'timeout': timeout}
        super().__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in self.options.items()
                       if key in self.cfg.settings and value is not None])
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return _build_app(self.model_dir, self.cors)


def _build_app(model_dir, cors):
    '''Builds and returns a Flask app'''
    connexion_app = App(__name__, specification_dir=model_dir, swagger_ui=False)
    connexion_app.add_api('oas.yaml', resolver=_CustomResolver())

    flask_app = connexion_app.app
    flask_app.model = load_model(model_dir)
    flask_app.model_dir = model_dir

    os.system('mv /app/model/model/scripts/user_provided/* /app')  # 将用户文件移动到/app目录下

    try:
        flask_app.model.init_model_data._func.inner('')  # 初始化模型数据，例如从文件中装载预训练好的模型参数
    except:
        pass  # 之前的模型没有定义init_model_data接口，则忽略

    @flask_app.route('/')
    def redirect_ui():
        return redirect('/ui')

    _add_swagger(flask_app)
    _apply_cors(flask_app, cors)

    return flask_app


class _CustomResolver(Resolver):

    def resolve_function_from_operation_id(self, operation_id):
        '''Routes model methods to a generic handler so that methods can be enumerated in the OAS'''
        if operation_id.startswith('methods'):
            _, method_name = operation_id.split('.')
            return partial(methods, method_name=method_name)
        else:
            return super().resolve_function_from_operation_id(operation_id)


def _add_swagger(app):
    '''Manually adds a Swagger v3 UI to the Flask app (until connexion 2.0 is released)'''
    swagger_bp = Blueprint('swagger_ui', __name__, static_url_path='', static_folder=swagger_ui_path, template_folder=swagger_ui_path)

    @swagger_bp.route('/')
    def swagger_ui_index():
        return render_template('index.j2', openapi_spec_url='/swagger.json')

    app.register_blueprint(swagger_bp, url_prefix='/ui')


def _apply_cors(app, cors):
    '''Configures a Flask app with CORS'''
    if isinstance(cors, str):
        origins = cors if cors == '*' else cors.split(',')
        CORS(app, origins=origins)
