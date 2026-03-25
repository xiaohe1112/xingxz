from flask import Flask, request, jsonify
import requests
import json
import re

app = Flask(__name__)

# 已帮你填入所有配置（直接用）
COZE_API = "https://59vdfgwcgw.coze.site/stream_run"  # 你的扣子流式API
COZE_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjhkMjgyYTVkLWJlMmUtNDViOS1hODFkLWM4ZGI3MTU5MmExOSJ9.eyJpc3MiOiJodHRwczovL2FwaS5jb3plLmNuIiwiYXVkIjpbInBxMHFuR2dtaXBQVlFVdzJvQk5OQ0dpaXNScTd5dDVsIl0sImV4cCI6ODIxMDI2Njg3Njc5OSwiaWF0IjoxNzc0NDAxODU2LCJzdWIiOiJzcGlmZmU6Ly9hcGkuY296ZS5jbi93b3JrbG9hZF9pZGVudGl0eS9pZDo3NjIwNzAyMjIxMTkzMTgzMjk1Iiwic3JjIjoiaW5ib3VuZF9hdXRoX2FjY2Vzc190b2tlbl9pZDo3NjIwOTk3OTQyNTU1NDQzMjI2In0.gmUSEGTWaoBBnZuYo6mMf0yzzeb-kcCDFl52gey1lRl7AvJzIB305VRQolukpE2qSsBExOxEiHkAileKv4eXAcHkq4IoKBPK3U7wyG6wlF33bF_Xk-SSdHd2oGADHMKiNRPdQSFyTwf-R0Ey-UfzZlozbHH0YxqFoBcdDgIbjzt5tqRZG27-vMLP79LiXRtV8D6M81kMpwvUrE-RRx5I9GpJIGpJtEGwjGol0XRGcJ3amDKDViFm-lTKdMtENRnJO2adhoJDBcjqxLLajiugt-n3yGSmTCYJMIuZaIzSUGKyvtoxq9SxCb7g6In1OZN8H6or0M6r_L19nDUH8XBFeQ"  # 你的扣子Token
WECHAT_WEBHOOK = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8e998fa8-966b-46c3-b617-7b6d52596079"  # 你的企业微信Webhook


# 适配扣子流式API，提取图片URL
def call_coze_stream(query):
    headers = {
        "Authorization": f"Bearer {COZE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {"content": [{"type": "query", "content": query}]}
    # 流式请求获取响应
    response = requests.post(COZE_API, headers=headers, json=data, stream=True)
    image_url = ""
    # 解析流式返回的内容，提取图片URL
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8').strip()
            # 匹配图片URL（适配http/https开头的图片链接）
            url_pattern = re.compile(r'https?://[^\s"]+\.(png|jpg|jpeg|webp|gif)')
            url_match = url_pattern.search(line_str)
            if url_match:
                image_url = url_match.group(0)
                break
    return image_url


# 按企业微信官方规范发送图文消息（解决93017报错）
def send_wechat_news(pic_url):
    if not pic_url:
        # 无图片URL时发送提示
        data = {
            "msgtype": "text",
            "text": {"content": "未生成有效形象照，请重新尝试～"}
        }
    else:
        # 企业微信官方news格式（必按此写，否则报93017）
        data = {
            "msgtype": "news",
            "news": {
                "articles": [{
                    "title": "员工形象照",
                    "description": "点击查看高清形象照",
                    "picurl": pic_url,
                    "url": pic_url
                }]
            }
        }
    # 发送请求，指定JSON格式（解决格式错误）
    res = requests.post(WECHAT_WEBHOOK, json=data, headers={"Content-Type": "application/json"})
    return res.json()


# 企业微信消息接收接口
@app.route("/", methods=["POST"])
def wechat_callback():
    try:
        # 解析企业微信发送的消息
        wechat_data = request.get_json()
        # 提取用户发送的文本内容（企业微信机器人默认推送格式）
        user_query = wechat_data.get("text", {}).get("content", "")
        if not user_query:
            return jsonify({"errcode": 0, "errmsg": "ok"})

        # 1. 调用扣子API获取图片URL
        image_url = call_coze_stream(user_query)
        # 2. 按官方格式推送给企业微信
        send_wechat_news(image_url)
        return jsonify({"errcode": 0, "errmsg": "ok"})
    except Exception as e:
        return jsonify({"errcode": -1, "errmsg": str(e)})


# 测试接口（可选，部署后可访问根地址测试）
@app.route("/", methods=["GET"])
def test():
    return "中转服务部署成功！"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)