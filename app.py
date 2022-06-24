import json
import logging

import flask
from flask import Flask, request, Response

import monitor

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False


def request_parse(req_data: request) -> dict:
    """解析请求数据并以json形式返回"""
    if req_data.method == 'POST':
        data = req_data.json
    elif req_data.method == 'GET':
        data = req_data.args
    else:
        raise Exception('请求方法不支持')
    return data


@app.route('/api', methods=["GET", "POST"])  # GET 和 POST 都可以
def get_data():
    data = request_parse(request)
    if 'query' not in data:
        return 'query is required', 400
    queryItem = data['query']
    if queryItem not in monitor.query_list:
        return 'query is not supported', 400
    if queryItem == 'all':
        _ = monitor.monitor()
        ret = {'status': _[0], 'msg': _[1]}
        return Response(response=json.dumps(ret), mimetype='application/json')
    if queryItem == 'cpu':
        return Response(response=json.dumps(monitor.backendIf(cpu=True)), mimetype='application/json')
    if queryItem == 'mem':
        return Response(response=json.dumps(monitor.backendIf(mem=True)), mimetype='application/json')
    if queryItem == 'user':
        return Response(response=json.dumps(monitor.backendIf(user=True)), mimetype='application/json')
    if queryItem == 'row':
        return Response(response=json.dumps(monitor.backendIf(row=True)), mimetype='application/json')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=11451, debug=False)
