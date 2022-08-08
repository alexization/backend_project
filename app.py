# 데이터를 수정하는 기능의 엔드포인트는 POST, 데이터를 읽어 들이는 기능의 엔드포인트는 GET
# POST 엔드포인트에 데이터를 전송할 때는 body에 JSON 형식으로 데이터를 전송한다.
# 중복된 값이 없어야 하는 데이터라면 set(집합)을 사용하고 순서나 순차가 중요하다면 list를 사용하자
# key와 value를 표현하는 데이터는 dict를 사용하자

# Default JSON encoder는 set를 JSON으로 변환하지 못 한다.
# 따라서 커스텀 엔코더를 작성해서 set을 list로 변환해서 JSON으로 변환 가능하게 해준다.
from flask import Flask, request, jsonify
from flask.json import JSONEncoder

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)

        return JSONEncoder.default(self.obj)

app = Flask(__name__)
app.id_count = 1
app.users = {}
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
    app.id_count = app.id_count + 1

    return jsonify(new_user)

@app.route("/tweet", methods=['POST'])
def tweet():
    payload = request.json
    user_id = int(payload['id'])
    tweet = payload['tweet']

    if user_id not in app.users:
        return 'User not exist', 400

    if len(tweet) > 300:
        return 'Over 300', 400

    user_id = int(payload['id'])
    app.tweets.append({
        'user_id' : user_id,
        'tweet' : tweet
    })

    return '', 200

@app.route("/follow", methods=['POST'])
def follow():
    payload = request.json
    user_id = int(payload['id'])
    user_id_to_follow = int(payload['follow'])

    if user_id not in app.users or user_id_to_follow not in app.users:
        return 'Not exist User', 400

    user = app.users[user_id]
    user.setdefault('follow', set()).add(user_id_to_follow)

    return jsonify(user)

@app.route("/unfollow", methods=['POST'])
def unfollow():
    payload = request.json
    user_id = int(payload['id'])
    user_id_to_follow = int(payload['follow'])

    if user_id not in app.users or user_id_to_follow not in app.users:
        return 'Not exist User', 400

    user = app.users[user_id]
    user.setdefault('follow', set()).discard(user_id_to_follow)

    return jsonify(user)

# URL에 인자를 전송하고 싶을 때는 <type:value> 형식으로 URL을 구성한다.
@app.route("/timeline/<int:user_id>", methods=['GET'])
def timeline(user_id):
    if user_id not in app.users:
        return 'Not exist User', 400

    follow_list = app.users[user_id].get('follow', set())
    follow_list.add(user_id)
    timeline = [tweet for tweet in app.tweets if tweet['user_id'] in follow_list]

    return jsonify({
        'user_id'   : user_id,
        'timeline'  : timeline
    })