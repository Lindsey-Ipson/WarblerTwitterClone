"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

app.app_context().push()

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

with app.app_context():
    db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False

# just added
app.config['DEBUG'] = False
app.config['DEBUG_TB_ENABLED'] = False
from flask_debugtoolbar import DebugToolbarExtension


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        with app.app_context():
            print("drop all")
            db.drop_all()
            print("create all")
            db.create_all()

        print("user delete")
        User.query.delete()
        print("message delete")
        Message.query.delete()

        print("test_client")
        self.client = app.test_client()

        print("signup")
        self.testuser = User.signup(username="TestUser1",
                                    email="TestUser1@test.com",
                                    password="Test1Password",
                                    image_url=None)
        
        self.testuser_id = 1212
        self.testuser.id = self.testuser_id

        print("commit")
        db.session.commit()

    def test_add_message_valid(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True
            )

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")


    def test_add_msg_not_logged_in(self):
        """When logged out, is user prohibited from adding messages?"""

        with self.client as c:
            resp = c.post('/messages/new', data={'text': 'New message'}, follow_redirects=True)

            # print('STATUS CODE', resp.status_code)
            # print('RESP.DATA', str(resp.data))
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    
    def test_add_msg_invalid_user(self):

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1111111111111111 # user does not exist

            resp = c.post("/messages/new", data={"text": "New message"},follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))


    def test_delete_msg_valid(self):
        
        m = Message(
            id=2345,
            text="Test message for test_delete_msg",
            user_id=self.testuser_id
        )
        db.session.add(m)
        db.session.commit()

        self.assertIsNotNone(m)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/2345/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            m = Message.query.get(2345)
            self.assertIsNone(m)


    def test_delete_msg_not_logged_in(self):
        """When you’re logged out, are you prohibited from deleting messages?"""

        with self.client as c:
            resp = c.post('/messages/new', data={'text': 'New message'}, follow_redirects=True)

            # print('STATUS CODE', resp.status_code)
            # print('RESP.DATA', str(resp.data))
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))


    def test_delete_msg_other_user(self):
        """When you’re logged in, are you prohibiting from deleting a message as another user?"""

        # A second user that will try to delete the message
        u = User.signup(username="unauthorized-user",
                        email="unauthorized-user@test.com",
                        password="password",
                        image_url=None)
        u.id = 76543

        #Message is owned by testuser
        m = Message(
            id=1234,
            text="test message for test_delete_msg_other_user",
            user_id=self.testuser_id
        )
        db.session.add_all([u, m])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 76543

            resp = c.post("/messages/1234/delete", follow_redirects=True)
            print('resp.data---------------->>>>>>>>>>>>>>>>>>>>.', str(resp.data))
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(1234)


    def test_show_msg_valid(self):

        m = Message(
            id=1234,
            text="Message from test test_show_message",
            user_id=self.testuser_id
        )

        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            m = Message.query.get(1234)

            resp = c.get(f'/messages/{m.id}')

            # print('resp.data---------------->>>>>>>>>>>>>>>>>>>>.', str(resp.data))

            self.assertEqual(resp.status_code, 200)
            self.assertIn(m.text, str(resp.data))


    def test_show_msg_invalid(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get('/messages/8888888') # message doesn't exist

            # print('CURR_USER_KEY---------------->>>>>>>>>>>>>>>>>>>>.', sess[CURR_USER_KEY], self.testuser.id)
            # print('resp.data---------------->>>>>>>>>>>>>>>>>>>>.', str(resp.data))

            self.assertEqual(resp.status_code, 500)
