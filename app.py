# 데이터를 수정하는 기능의 엔드포인트는 POST, 데이터를 읽어 들이는 기능의 엔드포인트는 GET
# POST 엔드포인트에 데이터를 전송할 때는 body에 JSON 형식으로 데이터를 전송한다.
# 중복된 값이 없어야 하는 데이터라면 set(집합)을 사용하고 순서나 순차가 중요하다면 list를 사용하자
# key와 value를 표현하는 데이터는 dict를 사용하자

# Default JSON encoder는 set를 JSON으로 변환하지 못 한다.
# 따라서 커스텀 엔코더를 작성해서 set을 list로 변환해서 JSON으로 변환 가능하게 해준다.
from flask import Flask, request, jsonify, current_app
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)

        return JSONEncoder.default(self.obj)

def get_user(user_id):
    user = current_app.database.execute(text("""
        SELECT
            id,
            name,
            email,
            profile
        FROM users
        WHERE id = :user_id
        """), {
            'user_id' : user_id
        }).fetchone()

    return {
        'id' : user['id'],
        'name' : user['name'],
        'email' : user['email'],
        'profile' : user['profile']
    } if user else None

def insert_user(user):
    return current_app.database.execute(text("""
        INSERT INTO users(
            name,
            email,
            profile,
            hashed_password
        ) VALUES (
            :name,
            :email,
            :profile,
            :password
        )
    """), user).lastrowid

def insert_tweet(user_tweet):
    return current_app.database.execute(text("""
        INSERT INTO tweets(
            user_id,
            tweet
        ) VALUES (
            :id,
            :tweet
        )
    """), user_tweet).rowcount

def insert_follow(user_follow):
    return current_app.database.execute(text("""
        INSERT INTO users_follow_list(
            user_id,
            follow_user_id
        ) VALUES (
            :id,
            :follow
        )
    """), user_follow).rowcount

def insert_unfollow(user_unfollow):
    return current_app.database.execute(text("""
        DELETE FROM users_follow_list
        WHERE user_id = :id
        AND follow_user_id = :unfollow
    """), user_unfollow).rowcount

def get_timeline(user_id):
    timeline = current_app.database.execute(text("""
        SELECT
            t.user_id,
            t.tweet
        FROM tweets t
        LEFT JOIN users_follow_list ufl ON ufl.user_id = :user_id
        WHERE t.user_id = :user_id
        OR t.user_id = ufl.follow_user_id
    """), {
        'user_id' : user_id
    }).fetchall()

    return [{
        'user_id' : tweet['user_id'],
        'tweet' : tweet['tweet']
    } for tweet in timeline]

def create_app(test_config = None):
    app = Flask(__name__)

    app.json_encoder = CustomJSONEncoder

    if test_config is None:
        app.config.from_pyfile("config.py")
    else:
        app.config.update(test_config)

    database = create_engine(app.config['DB_URL'], encoding = 'utf-8', max_overflow = 0)
    app.database = database

    @app.route("/ping", methods=['GET'])

    def ping():
        return "pong"

    @app.route("/sign-up", methods=['POST'])
    def sign_up():
        new_user = request.json
        new_user_id = insert_user(new_user)
        new_user = get_user(new_user_id)

        return jsonify(new_user)

    @app.route("/tweet", methods=['POST'])
    def tweet():
        user_tweet = request.json
        tweet = user_tweet['tweet']

        if len(tweet) > 300:
            return 'Over 300', 400

        insert_tweet(user_tweet)

        return '', 200

    @app.route("/follow", methods=['POST'])
    def follow():
        payload = request.json
        insert_follow(payload)

        return '', 200

    @app.route("/unfollow", methods=['POST'])
    def unfollow():
        payload = request.json
        insert_unfollow(payload)

        return '', 200

    # URL에 인자를 전송하고 싶을 때는 <type:value> 형식으로 URL을 구성한다.
    @app.route("/timeline/<int:user_id>", methods=['GET'])
    def timeline(user_id):
        return jsonify({
            'user_id' : user_id,
            'timeline' : get_timeline(user_id)
        })
        
    return app