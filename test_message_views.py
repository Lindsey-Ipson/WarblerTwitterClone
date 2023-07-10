"""Message View tests."""

# run these tests like:
# FLASK_ENV=production python -m unittest test_message_views.py


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

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test
app.config['WTF_CSRF_ENABLED'] = False

# Make Flask errors be real errors, not HTML pages with error info
app.config['TESTING'] = True

# Don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()


    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "test message for test_add_message"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "test message for test_add_message")


    def test_add_msg_not_logged_in(self):
        """When logged out, is user prohibited from adding messages?"""

        with self.client as c:
            resp = c.post('/messages/new', data={'text': 'test message for test_add_msg_not_logged_in'}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    
    def test_add_msg_invalid_user(self):
        """With invalid CURR_USER_KEY, is user prohibited from adding messages?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 1111111111111111 # user does not exist

            resp = c.post("/messages/new", data={"text": "test message for test_add_msg_invalid_user"},follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))


    def test_delete_msg_valid(self):
        
        m = Message(
            id=2345,
            text="Test message for test_delete_msg",
            user_id=self.testuser.id
        )
        db.session.add(m)
        db.session.commit()

        self.assertIsNotNone(m)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/2345/delete")
            self.assertEqual(resp.status_code, 302)

            m = Message.query.get(2345)
            self.assertIsNone(m)


    def test_delete_msg_not_logged_in(self):
        """When you’re logged out, are you prohibited from deleting messages?"""

        with self.client as c:
            resp = c.post('/messages/new', data={'text': 'test message for test_delete_msg_not_logged_in'}, follow_redirects=True)

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

        # Message is owned by testuser
        m = Message(
            id=1234,
            text="test message for test_delete_msg_other_user",
            user_id=self.testuser.id
        )
        db.session.add_all([u, m])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 76543

            resp = c.post("/messages/1234/delete", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(1234)


    def test_show_msg_valid(self):

        m = Message(
            id=1234,
            text="Message from test test_show_message",
            user_id=self.testuser.id
        )

        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            m = Message.query.get(1234)

            resp = c.get(f'/messages/{m.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(m.text, str(resp.data))


    def test_show_msg_invalid(self):
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get('/messages/8888888') # message doesn't exist

            self.assertEqual(resp.status_code, 404)

