# MidJourney-微信群机器人
> 知数云 MJ 微信群机器人,调用 Midjourney Imagine API 进行画图。

> 市面上价值6000元的 MidJourney 微信群机器人，且用且珍惜。

> 需求请咨询 立早-知数云（微信：mytimerun）。

<img src="https://i.postimg.cc/vBPm2zv2/code2.jpg"   width="30%">

## 安装依赖

```
pip install -r requirements.txt
```
## 修改config.py 28 29 30 行
- wechaty_puppet_service_token = "环境变量-可联系我们"
- zhishuyun_chatgpt_35_token = "知数云注册后申请 GPT API 接口的 token"
- zhishuyun_midjourney_token = "知数云注册后申请 MJ API 接口的 token"

- 执行代码前先设置环境变量
 ```
$env:WECHATY_PUPPET_SERVICE_TOKEN = "xxxxx"
```

- 或者将下一句加在28行前
```
os.environ['WECHATY_PUPPET_SERVICE_TOKEN'] = 'xxxxx'
```
## 执行
```
python main.py
```


## 小智 MJ WEB and BOT
- [知数云：MJ接口申请](https://auth.zhishuyun.com/auth/login?inviter_id=b01a5684-a3e4-43d6-a7c1-61105ccf9a8c&redirect=https://data.zhishuyun.com)
- [小智同学MJ线上地址](https://mj.lz300.cn/)
- [github 地址 web版](https://github.com/hbqjzx/mjxiaozhi)
- [github 地址 机器人版](https://github.com/hbqjzx/mjbot)


## 知数云-<a href="https://auth.zhishuyun.com/auth/login?inviter_id=b01a5684-a3e4-43d6-a7c1-61105ccf9a8c&redirect=https://data.zhishuyun.com">点击申请知数云 GPT & MJ API</a>
<img src="https://i.postimg.cc/h4zJZkH9/my-Zhishuyun.jpg" width="30%">

## 预览
![](https://i.postimg.cc/1zB6PDHw/2.jpg)



## 赞助我们
<img src="https://i.postimg.cc/N0q2RpN1/code.jpg"   width="30%">
