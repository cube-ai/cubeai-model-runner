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
Provides model runner utilities
"""
from os.path import dirname, join as path_join


_DATA_DIR = path_join(dirname(__file__), 'data')


def data_path(*path, prefix=_DATA_DIR):
    '''Returns an absolute path given a relative path from the cubeai_model_runner/data/ dir'''
    return path_join(prefix, *path)


def load_data(*path, prefix=_DATA_DIR, mode='r', loader=lambda file: file.read()):
    '''Loads and returns the contents of a file in the cubeai_model_runner/data/ dir'''
    with open(data_path(*path, prefix=prefix), mode) as file:
        return loader(file)
