import bcrypt
import pytest
import config

from model import UserDao, TweetDao
from sqlalchemy import create_engine, text


database = create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)

@pytest.fixture
def user_dao():
    return UserDao(database)


@pytest.fixture
def tweet_dao():
    return TweetDao(database)


def setup_function():
    # Create a test user
    hashed_password = bcrypt.hashpw(
        b"test password",
        bcrypt.gensalt()
    )
    new_users = [
        {
            'id' : 1001,
            'name' : '테스트1',
            'email' : 'test1001@gmail.com',
            'profile' : 'test1 profile',
            'hashed_password' : hashed_password
        }, {
            'id' : 1002,
            'name' : '테스트2',
            'email' : 'test1002@gmail.com',
            'profile' : 'test2 profile',
            'hashed_password' : hashed_password
        }
    ]
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
    """), new_users)

    # 사용자 2의 트윗 미리 생성해놓기
    database.execute(text("""
        INSERT INTO tweets (
            user_id,
            tweet
        ) VALUES (
            1002,
            "Hello World!"
        )
    """))


def teardown_funtion():
    database.execute(text("SET FORIGN_KEY_CHECKS=0"))
    database.execute(text("TRUNCATE users"))
    database.execute(text("TRUNCATE tweets"))
    database.execute(text("TRUNCATE users_follow_list"))
    database.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def get_user(user_id):
    row = database.execute(text("""
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
        'id' : row['id'],
        'name' : row['name'],
        'email' : row['email'],
        'profile' : row['profile']
    } if row else None


def get_follow_list(user_id):
    rows = database.execute(text("""
        SELECT follow_user_id as id
        FROM users_follow_list
        WHERE user_id = :user_id
    """), {
        'user_id' : user_id
    }).fetchall()

    return [int(row['id']) for row in rows]


def test_insert_user(user_dao):
    new_user = {
        'name' : '테스트3',
        'email' : 'test1003@gmail.com',
        'profile' : 'test3 profile',
        'password' : 'test1234'
    }

    new_user_id = user_dao.insert_user(new_user)
    user = get_user(new_user_id)

    assert user == {
        'id' : new_user_id,
        'name' : new_user['name'],
        'email' : new_user['email'],
        'profile' : new_user['profile']
    }


def test_get_user_id_and_password(user_dao):
    # get_user_id_and_password 메소드를 호출하여 사용자의 아이디와 비밀번호 해시 값을 읽어 들인다.
    # 사용자는 이미 setup_function에서 생성된 사용자를 사용한다.
    user_credential = user_dao.get_user_id_and_password(email = 'test1001@gmail.com')

    # 먼저 사용자가 아이디가 맞는지 확인한다.
    assert user_credential['id'] == 1001

    # 그리고 사용자 비밀번호가 맞는지 bcrypt와 checkpw 메소드를 사용해서 확인한다.
    assert bcrypt.checkpw('test password'.encode('UTF-8'), user_credential['hashed_password'].encode('UTF-8'))


def test_insert_follow(user_dao):
    # insert_follow 메소드를 사용하여 사용자 1이 사용자 2를 팔로우하도록 한다.
    # 사용자1과 2는 setup_function.에서 이미 생성되었다.
    user_dao.insert_follow(user_id = 1001, follow_id = 1002)
    follow_list = get_follow_list(1001)
    assert follow_list == [1002]


def test_insert_unfollow(user_dao):
    # insert_follow 메소드를 사용하여 사용자 1이 사용자 2를 팔로우한 후 언팔로우한다.
    # 사용자 1과 2는 setup_function에서 이미 생성되었다.
    user_dao.insert_follow(user_id = 1001, follow_id = 1002)
    user_dao.insert_unfollow(user_id = 1001, unfollow_id = 1002)
    follow_list = get_follow_list(1001)
    assert follow_list == [ ]


def test_insert_tweet(tweet_dao):
    tweet_dao.insert_tweet(1001, "tweet test")
    timeline = tweet_dao.get_timeline(1001)

    assert timeline == [
        {
            'user_id' : 1002,
            'tweet' : 'Hello World!'
        },
        {
            'user_id' : 1001,
            'tweet' : 'tweet test'
        },
        {
            'user_id' : 1002,
            'tweet' : 'tweet test 2'
        }
    ]
