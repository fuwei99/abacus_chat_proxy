from flask import Flask, request, jsonify, Response
import requests
import time
import json
import uuid
import random
import io
import re
import os

app = Flask(__name__)

API_ENDPOINT_URL = "https://abacus.ai/api/v0/describeDeployment"
MODEL_LIST_URL = "https://abacus.ai/api/v0/listExternalApplications"
TARGET_URL = "https://pa002.abacus.ai/api/_chatLLMSendMessageSSE"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]
DEPLOYMENT_ID = ""
MODEL_MAP = {}

# below data should be updated by user
DYNAMIC_COOKIES = ""
CONVERSATION_ID = ""

session = requests.Session()

def init_session():
    global DYNAMIC_COOKIES, MODEL_MAP, CONVERSATION_ID, DEPLOYMENT_ID
    try:
        # 优先使用环境变量
        DYNAMIC_COOKIES = os.environ.get('COOKIES')
        CONVERSATION_ID = os.environ.get('CONVERSATION_ID')
        
        # 如果环境变量不存在，则尝试从配置文件加载
        if not DYNAMIC_COOKIES or not CONVERSATION_ID:
            config = {}
            with open("config.txt", 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        config[key] = value
            DYNAMIC_COOKIES = DYNAMIC_COOKIES or config['cookies']
            CONVERSATION_ID = CONVERSATION_ID or config['conversationId']
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        return None
    
    @app.route('/')
    def index():
        return jsonify({
            "status": "running",
            "endpoints": {
                "models": "/v1/models",
                "chat": "/v1/chat/completions"
            }
        })
    
    headers = {
        'authority': 'abacus.ai',
        'method': 'POST',
        'path': '/api/v0/listExternalApplications',
        'scheme': 'https',
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'cookie': DYNAMIC_COOKIES,
        'origin': 'https://apps.abacus.ai',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'reai-ui': '1',
        'referer': 'https://apps.abacus.ai/',
        'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': random.choice(USER_AGENTS),
        'x-abacus-org-host': 'apps'
    }
    payload = {"includeSearchLlm":True}
    try:
        response = session.post(MODEL_LIST_URL, headers=headers, json=payload)
        response.raise_for_status()
        update_cookie()
        print(f"Updated cookies: {DYNAMIC_COOKIES}")
        response_data = response.json()
        if response_data.get('success') is True:
            for data in response_data['result']:
                if DEPLOYMENT_ID == "":
                    DEPLOYMENT_ID = data['deploymentId']
                if data['deploymentId'] != DEPLOYMENT_ID:
                    continue
                MODEL_MAP[data['name']] = (data['externalApplicationId'], data['predictionOverrides']['llmName'])
            print("Model map updated")
        else:
            print(f"Failed to update model map: {response_data.get('error')}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to update model map: {e}")
        return None
    return True

def update_cookie():
    global DYNAMIC_COOKIES
    cookie_jar = {}
    for key, value in session.cookies.items():
        cookie_jar[key] = value
    cookie_dict = {}
    for item in DYNAMIC_COOKIES.split(';'):
        key, value = item.strip().split('=', 1)
        cookie_dict[key] = value
    cookie_dict.update(cookie_jar)
    DYNAMIC_COOKIES = '; '.join([f"{key}={value}" for key, value in cookie_dict.items()])

@app.route('/v1/models', methods=['GET'])
def get_models():
    if len(MODEL_MAP) == 0:
        return jsonify({"error": "No models available"}), 500
    model_list = []
    for model in MODEL_MAP:
        model_list.append({"id": model, "object": "model", "created": int(time.time()), "owned_by": "Elbert", "name": model})
    return jsonify({"object": "list", "data": model_list})

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    openai_request = request.get_json()
    stream = openai_request.get('stream', False)
    messages = openai_request.get('messages')
    if messages is None:
        return jsonify({"error": "Messages is required"}), 400
    model = openai_request.get('model')
    if_model_available = MODEL_MAP.get(model, False)
    if if_model_available is False:
        return jsonify({"error": "Model not available, check if it is configured properly"}), 500
    message = format_message(messages)
    return send_message(message, model) if stream else send_message_non_stream(message, model)

def send_message(message, model):
    headers = {
        'accept': 'text/event-stream',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'connection': 'keep-alive',
        'content-type': 'text/plain;charset=UTF-8',
        'cookie': DYNAMIC_COOKIES,
        'host': 'pa002.abacus.ai',
        'origin': 'https://apps.abacus.ai',
        'pragma': 'no-cache',
        'referer': 'https://apps.abacus.ai/',
        'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': random.choice(USER_AGENTS),
        'x-abacus-org-host': 'apps'
    }
    payload = {
        "requestId": str(uuid.uuid4()),
        "deploymentConversationId": CONVERSATION_ID,
        "message": message,
        "isDesktop": True,
        "chatConfig": {
            "timezone": "Asia/Shanghai",
            "language": "zh-CN"
        },
        "llmName": MODEL_MAP[model][1],
        "externalApplicationId": MODEL_MAP[model][0],
        "regenerate": True,
        "editPrompt": True,
    }
    try:
        response = session.post(TARGET_URL, headers=headers, json=payload, stream=True)
        response.raise_for_status()

        def generate():
            try:
                print("---------- Response ----------")
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        try:
                            data = json.loads(decoded_line)
                            segment = data.get('segment', '')
                            print(segment, end='')
                            openai_chunk = {
                                "id": "chatcmpl-" + str(uuid.uuid4()),
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": model,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {"content": segment},
                                        "finish_reason": None
                                    }
                                ]
                            }
                            yield f"data: {json.dumps(openai_chunk)}\n\n"
                        
                        except json.JSONDecodeError:
                            print(f"Failed to decode line: {decoded_line}")
                print("\n---------- Response End ----------")
                yield f"data: [DONE]\n\n"
            except Exception as e:
                print(f"Failed to send message: {e}")
                yield f"data: {{\"error\": \"{e}\"}}\n\n"

        return Response(generate(), content_type='text/event-stream')
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")
        return jsonify({"error": "Failed to send message"}), 500

def send_message_non_stream(message, model):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'cache-control': 'no-cache',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': DYNAMIC_COOKIES,
        'origin': 'https://apps.abacus.ai',
        'pragma': 'no-cache',
        'referer': 'https://apps.abacus.ai/',
        'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': random.choice(USER_AGENTS),
        'x-abacus-org-host': 'apps'
    }
    payload = {
        "requestId": str(uuid.uuid4()),
        "deploymentConversationId": CONVERSATION_ID,
        "message": message,
        "isDesktop": True,
        "chatConfig": {
            "timezone": "Asia/Shanghai",
            "language": "zh-CN"
        },
        "llmName": MODEL_MAP[model][1],
        "externalApplicationId": MODEL_MAP[model][0],
        "regenerate": True,
        "editPrompt": True,
    }
    try:
        response = session.post(TARGET_URL, headers=headers, json=payload, stream=True)
        response.raise_for_status()
        buffer = io.StringIO()
        try:
            print("---------- Response ----------")
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    try:
                        data = json.loads(decoded_line)
                        segment = data.get('segment', '')
                        print(segment, end='')
                        buffer.write(segment)
                    except json.JSONDecodeError:
                        print(f"Failed to decode line: {decoded_line}")
            print("\n---------- Response End ----------")
            openai_response = {
                "id": "chatcmpl-" + str(uuid.uuid4()),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": buffer.getvalue()
                        },
                        "finish_reason": "completed"
                    }
                ],
            }
            return jsonify(openai_response)
        except Exception as e:
            print(f"Failed to send message: {e}")
            return jsonify({"error": "Failed to send message"}), 500
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")
        return jsonify({"error": "Failed to send message"}), 500

def format_message(messages):
    buffer = io.StringIO()
    role_map, prefix, messages = extract_role(messages)
    for message in messages:
        role = message.get('role')
        role = '\b' + role_map[role] if prefix else role_map[role]
        content = message.get('content').replace("\\n", "\n")
        pattern = re.compile(r'<\|removeRole\|>\n')
        if pattern.match(content):
            content = pattern.sub("", content)
            buffer.write(f"{content}\n")
        else:
            buffer.write(f"{role}: {content}\n")
    formatted_message = buffer.getvalue()
    with open("message_log.txt", "w", encoding="utf-8") as f:
        f.write(formatted_message)
    return formatted_message


def extract_role(messages):
    role_map = {
        "user": "Human",
        "assistant": "Assistant",
        "system": "System"
    }
    prefix = False
    first_message = messages[0]['content']
    pattern = re.compile(r"""
        <roleInfo>\s*
        user:\s*(?P<user>[^\n]*)\s*
        assistant:\s*(?P<assistant>[^\n]*)\s*
        system:\s*(?P<system>[^\n]*)\s*
        prefix:\s*(?P<prefix>[^\n]*)\s*
        </roleInfo>\n
    """, re.VERBOSE)
    match = pattern.search(first_message)
    if match:
        role_map = {
            "user": match.group("user"),
            "assistant": match.group("assistant"),
            "system": match.group("system"),
        }
        prefix = match.group("prefix") == "1"
        messages[0]['content'] = pattern.sub("", first_message)
        print(f"Extracted role map:")
        print(f"User: {role_map['user']}, Assistant: {role_map['assistant']}, System: {role_map['system']}")
        print(f"Using prefix: {prefix}")
    return (role_map, prefix, messages)

init_session()

if __name__ == '__main__':
    init_session()
    # 支持本地运行和 Vercel 环境
    port = int(os.environ.get('PORT', 9876))
    app.run(host='0.0.0.0', port=port)
