from flask import Flask

app = Flask(__name__)

# Flask의 route decorator를 사용하여 endpoint를 등록한다.
# 이 경우에는 그 다음에 나오는 ping 함수를 endpoint 함수로 등록하였으며, 고유 주소는 "ping"이며
# HTTP method는 GET으로 설정되어 등록되었다.
@app.route("/ping", methods=['GET'])
def ping():
    return "pong"
