# 交大云评教

<http://xjtupj.qcloudapps.com/pj/>

基于Django Celery的后台挂机自动评教系统

> 本仓库代码可以直接在[腾讯蓝鲸智云](http://bk.tencent.com/campus/developer-center/)部署

## 安装

### 在开发环境下运行（请勿用于生产环境）

1. 要求使用`Python 2.x`
2. 按照`requirements.txt`中的需求使用`pip`进行安装，例如`pip install django==1.8.17`
3. 在`settings.py`中配置和数据库信息
4. 执行`manage.py runserver` `manage.py celery worker` `manage.py celery beat`即可在`http://127.0.0.1/pj/`访问

### 腾讯蓝鲸智云部署

1. 访问<http://bk.tencent.com/campus/developer-center/>
2. 新建应用，并进行`SVN Checkout` `trunk`
3. 直接删除`trunk`的所有数据，将本仓库的`master`分支文件解压到该文件夹
4. 执行`SVN Commit`。
5. 在腾讯蓝鲸智云页面勾选`启用celery`和`启用周期性任务`，点击一键部署应用即可

## 执行流程

### CAS登录流程

1. 访问`/cas/login/`
2. 如果Session中有`cas`，则显示已登录，并在1秒后跳转到service的网址
3. 如果Session中没有`cas`，则显示NetID、密码的输入框，这是一个简单的POST表单
4. (同步)使用`requests`登录`真·CAS`，如果成功则把用户名密码存到数据库，`requests.Session`中的cookie转换为dict存到Session
5. 如果登录成功，与数据库原来密码不同记录更新密码，与原来密码相同则记录登录，不同则记录更新密码，原来没有用户则记录创建用户

### 师生服务登录流程

1. 访问`/ssfw/login/`
2. 如果没有师生服务的cookie则使用Session中的`cas`的cookie登录，如果也没有cas的cookie那就跳转到`/cas/login/?redirect=/ssfw/login/`登录CAS
3. CAS登录成功之后，跳转回`/ssfw/login/`使用CAS登录师生服务，(同步)使用`requests`登录`真·师生服务`，返回一个跳转链接，使用新的`requests.Session`访问此链接，然后把cookie存到Session中的`ssfw`中
4. 登录成功后记录CAS授权登录和师生服务登录

### 云评教流程

1. 访问`/pj/login/`登录（并不是登录，而是爬取页面并缓存到Session中）
2. 访问`/pj/`显示缓存下来的爬取到的教学评价页面的信息
3. 后台登录之后会添加此用户自动评教的`celery task`
4. 另一个进程中`celery beat`会每天依次尝试登录评教用户表所有用户，如果登录失败则将用户标记为失效，如果成功则自动评教（只评还没评的课程）
5. 用户自动评教有锁。防止两个线程同时评教

## LICENSE

本项目仅供学习交流使用，代码采用AGPL-3.0开放源代码协议，欢迎Fork或发送Pull Request，如果喜欢可以点一下Star。

[AGPL 3.0](https://www.gnu.org/licenses/agpl.txt)

    Django XJTU Teaching Evalution
    Copyright (C) 2017 Ganlv

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
