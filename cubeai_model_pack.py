# -*- coding: utf-8 -*-
import os
import sys
import shutil
import yaml
from distutils.core import setup
from Cython.Build import cythonize


class SoBuilder(object):

    def __init__(self, app_path):
        self.app_path = app_path
        self.base_path = os.path.abspath('.')
        self.build_path = 'build'
        self.build_tmp_path = 'build/tmp'
        if os.path.exists(self.build_path):
            shutil.rmtree(self.build_path)

        py_ver = ''.join(sys.version[0:3].split('.'))
        self.gcc_suffix = '.cpython-{}m-x86_64-linux-gnu.so'.format(py_ver)

    def copy_other_file(self, src_file_path):
        if src_file_path.endswith('__init__.py'):
            if os.path.exists(self.build_path):
                shutil.rmtree(self.build_path)
            raise Exception(print('程序中存在“__init__.py”文件，编译时会出现异常。请删除所有“__init__.py”文件后再编译！'))

        dst_file_path = '{}/{}/{}'.format(self.base_path, self.build_path, src_file_path[len(self.base_path) + 1:])
        dst_path = dst_file_path[:dst_file_path.rfind('/')]
        if not os.path.isdir(dst_path):
            os.makedirs(dst_path)
        shutil.copyfile(src_file_path, dst_file_path)

    def yeild_py(self, path, copy_others=True):
        for file_name in os.listdir(path):
            file_path = os.path.join(path, file_name)
            if os.path.isdir(file_path) and not file_name.startswith('.'):
                for f in self.yeild_py(file_path, copy_others):
                    yield f
            elif os.path.isfile(file_path):
                ext = os.path.splitext(file_name)[1]
                if ext not in ('.pyc', '.pyx'):
                    if ext == '.py' and not file_name.startswith('__'):
                        yield os.path.join(path, file_name)
                    elif copy_others:
                        self.copy_other_file(file_path)
            else:
                pass

    def delete_c_files(self, path):
        for file_name in os.listdir(path):
            file_path = os.path.join(path, file_name)
            if os.path.isdir(file_path) and not file_name.startswith('.'):
                self.delete_c_files(file_path)
            elif os.path.isfile(file_path):
                ext = os.path.splitext(file_name)[1]
                if ext == '.c':
                    os.remove(file_path)
            else:
                pass

    def build_so(self):
        py_files = list(self.yeild_py(os.path.join(self.base_path, self.app_path)))

        try:
            for src_file_path in py_files:
                dst_file_path = '{}/{}/{}'.format(self.base_path, self.build_path,
                                                  src_file_path[len(self.base_path) + 1:])
                idx = dst_file_path.rfind('/')
                dst_path = dst_file_path[:idx]
                py_name = dst_file_path[idx + 1:].split('.')[0]
                setup(ext_modules=cythonize(src_file_path),
                      script_args=['build_ext', '-b', dst_path, '-t', self.build_tmp_path])
                src = dst_path + '/' + py_name + self.gcc_suffix
                dst = dst_path + '/' + py_name + '.so'
                os.rename(src, dst)
        except Exception as e:
            print(str(e))

        self.delete_c_files(os.path.join(self.base_path, self.app_path))
        if os.path.exists(self.build_tmp_path):
            shutil.rmtree(self.build_tmp_path)


def get_model_name():
    try:
        with open('./application.yml', 'r') as f:
            yml = yaml.load(f, Loader=yaml.SafeLoader)
    except:
        print('错误： 模型配置文件application.yml不存在！')
        return None

    try:
        name = yml['model']['name']
    except:
        print('错误： 未指定模型名称！')
        print('请在application.yml文件中编辑修改...')
        return None

    try:
        python = str(yml['python']['version'])
    except:
        print('错误： 未指定Python版本号！')
        print('请在application.yml文件中编辑修改...')
        return None


    if not python.startswith('3.'):
        print('错误： Python版本号必须是3且3.5以上！')
        print('请在application.yml文件中编辑修改...')
        return None

    if not sys.version.startswith(python):
        print('错误： 声明的Python版本号与当前运行环境（{}）不一致！'.format(sys.version[:sys.version.find(' ')]))
        print('请在application.yml文件中编辑修改...')
        return None

    try:
        model_runner = yml['model_runner']['version']
    except:
        print('错误： 未指定model_runner版本号！')
        print('请在application.yml文件中编辑修改...')
        return None

    if model_runner != 'v2':
        print('错误： model_runner版本号必须是“v2”！')
        print('请在application.yml文件中编辑修改...')
        return None

    if not os.path.exists('requirements.txt'):
        print('错误： requirements.txt文件不存在！')
        return None

    return name


def pack_model():
    name = get_model_name()
    if name is None:
        return

    os.system('rm -rf ./out')
    os.system('mkdir out')
    os.system('mkdir out/{}'.format(name))
    os.system('cp ./application.yml ./out/{}/'.format(name))
    os.system('cp ./requirements.txt ./out/{}/'.format(name))
    os.system('cp -rf ./core ./out/{}/'.format(name))

    if os.path.exists('./webapp/bpp'):
        cwd = os.getcwd()
        os.chdir(os.path.join(cwd, 'webapp'))
        if not os.path.exists('./node_modules'):
            os.system('yarn install')
        os.system('yarn webpack:prod')
        os.chdir(cwd)
    if os.path.exists('./webapp/www'):
        os.system('mkdir out/{}/webapp'.format(name))
        os.system('cp -rf ./webapp/www ./out/{}/webapp/'.format(name))

    dst_path = './out/{}'.format(name)
    shutil.make_archive(dst_path, 'zip', dst_path)  # 将目标文件夹自动压缩成.zip文件
    shutil.rmtree('./out/{}/'.format(name))
    print('模型打包完成！ 输出位置： ./out/{}.zip'.format(name))
    
    
def pack_model_bin():
    name = get_model_name()
    if name is None:
        return

    os.system('rm -rf ./out')
    os.system('mkdir out')
    os.system('mkdir out/{}'.format(name))
    os.system('cp ./application.yml ./out/{}/'.format(name))
    os.system('cp ./requirements.txt ./out/{}/'.format(name))
    
    so_builder = SoBuilder('core')
    so_builder.build_so()
    os.system('mv ./build/core ./out/{}/'.format(name))
    shutil.rmtree('build')

    if os.path.exists('./webapp/bpp'):
        cwd = os.getcwd()
        os.chdir(os.path.join(cwd, 'webapp'))
        if not os.path.exists('./node_modules'):
            os.system('yarn install')
        os.system('yarn webpack:prod')
        os.chdir(cwd)
    if os.path.exists('./webapp/www'):
        os.system('mkdir out/{}/webapp'.format(name))
        os.system('cp -rf ./webapp/www ./out/{}/webapp/'.format(name))
    
    dst_path = './out/{}'.format(name)
    shutil.make_archive(dst_path, 'zip', dst_path)  # 将目标文件夹自动压缩成.zip文件
    shutil.rmtree('./out/{}/'.format(name))
    print('模型打包完成！ 输出位置： ./out/{}.zip'.format(name))


if __name__ == '__main__':
    pack_model()
