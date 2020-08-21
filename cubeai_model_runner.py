# -*- coding: utf-8 -*-
import json
import socket
import threading
import logging
import asyncio
import tornado.web
import tornado.ioloop
import tornado.httpserver

import os, sys
sys.path.append(os.getcwd())
from core.model_core import ModelCore


class GlobalData:
    def __init__(self):
        self.model_core = None

    def init_global_data(self):
        try:
            self.model_core = ModelCore()
            return True
        except Exception as e:
            logging.error(str(e))
            return False


g = GlobalData()


def model_runner(input, output):
    if not isinstance(input, dict):
        result = {
            'value': '错误： HTTP请求体不是JSON格式！',
            'status': 'err'
        }
        output['result'] = result
        output['finish'] = True
        return

    method = input.get('method')
    kwargs = input.get('kwargs')
    
    if method is None:
        result = {
            'value': '错误： HTTP请求体中未携带方法名！',
            'status': 'err'
        }
        output['result'] = result
        output['finish'] = True
        return

    public_methods = getattr(ModelCore, 'public_methods', None)
    if public_methods is not None:
        if method not in public_methods:
            result = {
                'value': '错误： 方法 {} 禁止访问！'.format(method),
                'status': 'err'
            }
            output['result'] = result
            output['finish'] = True
            return

    model = g.model_core
    method_obj = getattr(model, method, None)
    if method_obj is None:
        result = {
            'value': '错误： 方法 {} 未定义！'.format(method),
            'status': 'err'
        }
        output['result'] = result
        output['finish'] = True
        return

    result = {}
    try:
        result['value'] = method_obj(**kwargs) if kwargs else method_obj()  # kwargs为None或{}时，不带参数调用
        result['status'] = 'ok'
    except Exception as e:
        logging.error(str(e))
        result['value'] = str(e)
        result['status'] = 'err'

    output['result'] = result
    output['finish'] = True
    

def stream_runner(input, output):

    method = input.get('method')
    arg = input.get('arg')

    public_methods = getattr(ModelCore, 'public_methods', None)
    if public_methods is not None:
        if method not in public_methods:
            result = {
                'value': '错误： 方法 {} 禁止访问！'.format(method),
                'status': 'err'
            }
            output['result'] = result
            output['finish'] = True
            return

    model = g.model_core
    method_obj = getattr(model, method, None)
    if method_obj is None:
        result = {
            'value': '错误： 方法 {} 未定义！'.format(method),
            'status': 'err'
        }
        output['result'] = result
        output['finish'] = True
        return

    result = {}
    try:
        result['value'] = method_obj(arg)
        result['status'] = 'ok'
    except Exception as e:
        logging.error(str(e))
        result['value'] = str(e)
        result['status'] = 'err'

    output['result'] = result
    output['finish'] = True


class ModelApi(tornado.web.RequestHandler):

    async def post(self, *args, **kwargs):

        try:
            input = json.loads(str(self.request.body, encoding='utf-8'))
        except Exception as e:
            logging.error(str(e))
            result = {
                'status': 'err',
                'value': '错误： HTTP请求体错误！' + str(e)
            }
            res = json.dumps(result, ensure_ascii=False)
            self.set_header('Access-Control-Allow-Origin', '*')  # 允许跨域访问
            self.write(res)
            return 
            
        output = {
            'result': {},
            'finish': False
        }
        thread = threading.Thread(
            target=model_runner,
            args=(input, output)
        )
        thread.setDaemon(True)
        thread.start()

        while not output['finish']:
            await asyncio.sleep(0.05)

        result = output['result']

        if isinstance(result['value'], bytes):
            res = result['value']
        else:
            try:
                res = json.dumps(result, ensure_ascii=False)
            except Exception as e:
                logging.error(str(e))
                result = {
                    'status': 'err',
                    'value': '错误： 模型返回结果序列化失败！' + str(e)
                }
                res = json.dumps(result, ensure_ascii=False)

        self.set_header('Access-Control-Allow-Origin', '*')  # 允许跨域访问
        self.write(res)

    async def options(self, *args, **kwargs):
        self.set_status(204)
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'content-type')
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.finish()
        return


class StreamApi(tornado.web.RequestHandler):

    async def post(self, method, *args, **kwargs):

        input = {
            'method': method,
            'arg': self.request.body,
        }
        output = {
            'result': {},
            'finish': False
        }
        thread = threading.Thread(
            target=stream_runner,
            args=(input, output)
        )
        thread.setDaemon(True)
        thread.start()

        while not output['finish']:
            await asyncio.sleep(0.05)

        result = output['result']

        if isinstance(result['value'], bytes):
            res = result['value']
        else:
            try:
                res = json.dumps(result, ensure_ascii=False)
            except Exception as e:
                logging.error(str(e))
                result = {
                    'status': 'err',
                    'value': '错误： 模型返回结果序列化失败！' + str(e)
                }
                res = json.dumps(result, ensure_ascii=False)

        self.set_header('Access-Control-Allow-Origin', '*')  # 允许跨域访问
        self.write(res)

    async def options(self, *args, **kwargs):
        self.set_status(204)
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'content-type')
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.finish()
        return


class FileApi(tornado.web.RequestHandler):

    async def post(self, method, *args, **kwargs):
        
        try:
            file_obj = self.request.files.get(method)[0]
            file_body = file_obj.body
        except Exception as e:
            logging.error(str(e))
            result = {
                'status': 'err',
                'value': '错误： HTTP文件请求体错误！' + str(e)
            }
            res = json.dumps(result, ensure_ascii=False)
            self.set_header('Access-Control-Allow-Credentials', 'true')
            self.set_header('Access-Control-Allow-Origin', self.request.headers.get('Origin'))
            self.write(res)
            return 

        input = {
            'method': method,
            'arg': file_body,
        }
        output = {
            'result': {},
            'finish': False
        }
        thread = threading.Thread(
            target=stream_runner,
            args=(input, output)
        )
        thread.setDaemon(True)
        thread.start()

        while not output['finish']:
            await asyncio.sleep(0.05)

        result = output['result']

        if isinstance(result['value'], bytes):
            res = result['value']
        else:
            try:
                res = json.dumps(result, ensure_ascii=False)
            except Exception as e:
                logging.error(str(e))
                result = {
                    'status': 'err',
                    'value': '错误： 模型返回结果序列化失败！' + str(e)
                }
                res = json.dumps(result, ensure_ascii=False)

        self.set_header('Access-Control-Allow-Credentials', 'true')
        self.set_header('Access-Control-Allow-Origin', self.request.headers.get('Origin'))
        self.write(res)

    async def options(self, *args, **kwargs):
        self.set_status(204)
        self.set_header('Access-Control-Allow-Credentials', 'true')
        self.set_header('Access-Control-Allow-Origin', self.request.headers.get('Origin'))
        self.set_header('Access-Control-Allow-Headers', 'content-type')
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.finish()
        return
    

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def start():
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

    if not g.init_global_data():
        logging.error('错误： 模型初始化失败！')
        return

    app_profile = os.environ.get('APP_PROFILE', 'dev').lower()
    app = tornado.web.Application(
        handlers=[
            (r'/api/model', ModelApi),
            (r'/api/stream/(\w+)', StreamApi),
            (r'/api/file/(\w+)', FileApi),
            (r'/web/(.*)', tornado.web.StaticFileHandler, {'path': 'webapp/www', 'default_filename': 'index.html'}),
        ],
        debug=('dev' == app_profile)
    )
    http_server = tornado.httpserver.HTTPServer(app, max_buffer_size=800*1024*1024)
    http_server.listen(3330)

    logging.critical('##################################################')
    logging.critical('    CubeAI_Model_Runner started ...')
    logging.critical('    Listening at: {}:3330'.format(get_local_ip()))
    logging.critical('    Web access: http://{}:3330/web/'.format(get_local_ip()))
    logging.critical('    App profile: {}'.format(app_profile))
    logging.critical('##################################################')
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    start()
