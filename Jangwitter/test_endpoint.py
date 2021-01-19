import config
import pytest
import bcrypt
from sqlalchemy import create_engine, text
from app import create_app
import json

database = create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)

# fixture decorator가 적용된 함수와 같은 이름의 인자가 다른 test 함수에 지정되어 있으면 pytest가 알아서 같은 이름의 함수의 리턴값을 해당 함수의
# 리턴 값을 해당 인자에 넣어준다.
@pytest.fixture
def api():
    app = create_app(config.test_config)
    app.config['TESTING'] = True
    api = app.test_client()

    return api

def setup_function():
    # Create a test user
    hashed_password = bcrypt.hashpw(
        b"test password",
        bcrypt.gensalt()
    )
    new_user = {
        'id' : 1,
        'name' : '테스트',
        'email' : 'test@gmail.com',
        'profile' : 'unit test profile',
        'hashed_password' : hashed_password
    }
    database.execute(text("""
        INSERT INTO users (
            id,
            name,
            email,
            profile,
            hashed_password
        ) VALUES (
            :id,
            :name,
            :email,
            :profile,
            :hashed_password
        )
    """), new_user)


def teardown_function():
    database.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    database.execute(text("TRUNCATE users"))
    database.execute(text("TRUNCATE tweets"))
    database.execute(text("TRUNCATE users_follow_list"))
    database.execute(text("SET FOREIGN_KEY_CHECKS=1"))


# pytest 커맨드를 실행해서 테스트들을 실행하므로 test 함수들에 인자를 넘겨주어 실행할 수 없다. 그런데도 인자가 지정되어 있는 이유는
# pytest가 자동으로 지정된 인자와 동일한 이름을 가지고 있고, 또한 pytest.fixture decorator가 적용되어 있는 함수를 찾아서 해당 함수의
# 리턴 값을 인자에 적용시켜 주기 때문이다.
def test_ping(api):
    resp = api.get('/ping')
    assert b'pong' in resp.data


def test_tweet(api):
    # Login
    resp = api.post(
        '/login',
        data = json.dumps({'email' : 'test@gmail.com', 'password' : 'test password'}),
        content_type = 'application/json'
    )
    resp_json = json.loads(resp.data.decode('utf-8'))
    access_token = resp_json['access_token']

    # tweet
    resp = api.post(
        '/tweet',
        data = json.dumps({'tweet' : "Hello World!"}),
        content_type = 'application/json',
        headers = {'Authorization' : access_token}
    )
    assert resp.status_code == 200

    # tweet 확인
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id' : 1,
        'timeline' : [
            {
                'user_id' : 1,
                'tweet' : "Hello World!"
            }
        ]
    }