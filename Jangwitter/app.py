from flask import Flask, jsonify, request
# jsonify는 dictionary 객체를 JSON으로 변환하여 HTTP 응답으로 보낼 수 있게 된다.
# request를 통해 사용자가 HTTP 요청을 통해 전송한 JSON 데이터를 읽어 들일 수 있게 된다.
from flask.json import JSONEncoder


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)

        return JSONEncoder.default(self, obj)


app = Flask(__name__)
app.users = {}
app.id_count = 1
app.tweets = []
app.json_encoder = CustomJSONEncoder

@app.route("/ping", methods=['GET'])
def ping():
    return "pong"


@app.route("/sign-up", methods=['POST'])
def sign_up():
    new_user = request.json
    new_user["id"] = app.id_count
    app.users[app.id_count] = new_user
    app.id_count += 1

    return jsonify(new_user)

@app.route('/tweet', methods=['POST'])
def tweet():
    payload = request.json
    user_id = int(payload['id'])
    tweet = payload['tweet']

    if user_id not in app.users:
        return '사용자가 존재하지 않습니다.', 400

    if len(tweet) > 300:
        return '300자를 초과했습니다.', 400

    app.tweets.append({
        'user_id' : user_id,
        'tweet' : tweet
    })

    return '', 200


@app.route('/follow', methods=['POST'])
def follow():
    payload = request.json
    user_id = int(payload['id'])
    user_id_to_follow = int(payload['follow'])

    if user_id not in app.users or user_id_to_follow not in app.users:
        return '사용자가 존재하지 않습니다.', 400

    user = app.users[user_id]
    user.setdefault('follow', set()).add(user_id_to_follow)
    # 위의 user에서 읽어들인 사용자의 정보를 담고 있는 dictionary가 이미 "follow"라는 field를 가지고 있다면, 사용자의 "follow"
    # key와 연결되어 있는 set에 follow하고자 하는 사용자의 id를 추가한다.

    return jsonify(user)


@app.route('/unfollow', methods=['POST'])
def unfollow():
    payload = request.json
    user_id = int(payload["id"])
    user_id_to_unfollow = int(payload["unfollow"])

    if user_id not in app.users or user_id_to_unfollow not in app.users:
        return '사용자가 존재하지 않습니다.', 400

    user = app.users[user_id]
    user.setdefault('follow', set()).discard(user_id_to_unfollow)

    return jsonify(user)


@app.route('/timeline/<int:user_id>', methods=['GET'])
def timeline(user_id):
    if user_id not in app.users:
        return '사용자가 존재하지 않습니다.', 400

    follow_list = app.users[user_id].get('follow', set())
    follow_list.add(user_id)
    timeline = [tweet for tweet in app.tweets if tweet['user_id'] in follow_list]

    return jsonify({
        'user_id' : user_id,
        'timeline' : timeline
    })
