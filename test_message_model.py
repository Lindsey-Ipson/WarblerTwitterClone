"""Message model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Now we can import app
from app import app

app.app_context().push()


class MessageModelTestCase(TestCase):
    """Test message model"""

    def setUp(self):
        """Create test client, add sample data."""

        with app.app_context():
            db.drop_all()
            db.create_all()

        self.testuser = User.signup(username="TestUser12",
                                    email="TestUser12@test.com",
                                    password="Test1Password",
                                    image_url=None)

        self.testuser_id = 1212
        self.testuser.id = self.testuser_id

        db.session.add(self.testuser)
        db.session.commit()

        self.u1_id = self.testuser.id
        self.u1 = db.session.query(User).get(self.u1_id)  # Fetch the instance using the current session

        self.client = app.test_client()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        db.drop_all()
        return res
    

    def test_message_model(self):
        """Test that basic model works"""
    
        m1 = Message(text='test message for test_message_model', user_id=self.u1_id)
        db.session.add(m1)
        db.session.commit()
    
        db.session.refresh(self.u1)  # Refresh the instance from the database

        self.assertEqual(len(self.u1.messages), 1)
        self.assertEqual(self.u1.messages[0].text, 'test message for test_message_model')


    def test_message_likes(self):
        """Test message likes functionality"""

        m1 = Message(text='test message for test_message_likes', user_id=self.u1_id)
        db.session.add(m1)

        self.u1.likes.append(m1)

        db.session.commit()

        like = Likes.query.filter(Likes.user_id == self.u1_id).all()
        self.assertEqual(len(like), 1)
        self.assertEqual(like[0].message_id, m1.id)


    def test_message_user(self):

        m1 = Message(text='test message for test_message_user', user_id=self.u1.id)
        db.session.add(m1)

        self.assertEqual(m1.user_id, self.u1.id)


