# cubeai-model-runner

CubeAI模型运行器。

[CubeAI平台](https://cubeai.dimpt.com)中生成的模型docker镜像在部署运行后，首先会调用cubeai-model-runner，启动一个web容器，将模型内部函数映射成为RESTful API接口对外提供服务。

依赖包地址： https://pypi.org/project/cubeai-model-runner

使用pip安装:

    $ pip install cubeai_model_runner

基于[acumos-model-runner](https://pypi.org/project/acumos-model-runner)改编。
