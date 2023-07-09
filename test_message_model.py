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

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

# db.create_all()
app.app_context().push()

# with app.app_context():
# db.drop_all()
# db.create_all()

# app.app_context().push()
# python -m unittest test_message_model.UserModelTestCase.test_user_model


class MessageModelTestCase(TestCase):
    """Test message model"""

    # def setUp(self):
    #     """Create test client, add sample data."""
    #     with app.app_context():
    #         db.drop_all()
    #         db.create_all()

    #         u1 = User.signup('TestUser1', 'TestUser1@gmail.com', 'TestPassword1', None)
    #         u1_id = 1000
    #         u1.id = u1_id
    #         db.session.commit()

    #         # print('u1!!!!!!!!!!!!!!', u1)

    #         u1 = User.query.get(u1.id)

    #         self.u1 = u1
    #         self.u1_id = u1_id

    #         self.client = app.test_client()

    #         self.u1 = User.query.get(self.u1_id)

    #         # print('self.u1!!!!!!!!!!!!!!', self.u1)

    #         self.client = app.test_client()

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
    


    

    # def test_message_model(self):
    #     """Test that basic model works"""
        
    #     m1 = Message(text='test message for test_message_model', user_id=self.u1_id)
    #     db.session.add(m1)
    #     db.session.commit()

    #     print('self.u1!!!!!!!!!!!!!!', self.u1)
    #     print('m1!!!!!!!!!!!!!!', m1)
    #     print('m1.user!!!!!!!!!!!!!!', m1.user)
    #     print('self.u1.messages!!!!!!!!!!!!!', self.u1.messages)

    #     self.assertEqual(len(self.u1.messages), 1)
    #     self.assertEqual(self.u1.messages[0].text, 'test message for test_message_model')

    def test_message_model(self):
        """Test that basic model works"""
    
        m1 = Message(text='test message for test_message_model', user_id=self.u1_id)
        db.session.add(m1)
        db.session.commit()
    
        db.session.refresh(self.u1)  # Refresh the instance from the database
    
        print('self.u1!!!!!!!!!!!!!!', self.u1)
        print('m1!!!!!!!!!!!!!!', m1)
        print('m1.user!!!!!!!!!!!!!!', m1.user)
        print('self.u1.messages!!!!!!!!!!!!!', self.u1.messages)
    
        self.assertEqual(len(self.u1.messages), 1)
        self.assertEqual(self.u1.messages[0].text, 'test message for test_message_model')



    def test_message_likes(self):
        """Test message likes functionality"""

        m1 = Message(text='test message for test_message_likes', user_id=self.u1_id)
        db.session.add(m1)

        self.u1.likes.append(m1)

        db.session.commit()

        like = Likes.query.filter(Likes.user_id == self.u1_id).all()
        # like = db.session.get(Likes).filter(Likes.u1_id == self.u1_id).all()
        self.assertEqual(len(like), 1)
        self.assertEqual(like[0].message_id, m1.id)


    def test_message_user(self):

        m1 = Message(text='test message for test_message_user', user_id=self.u1.id)
        db.session.add(m1)

        # print('m1.text==============>>>>>>>>>>', m1.text)
        # print('m1.user==============>>>>>>>>>>', m1.user)
        # print('m1.user.id==============>>>>>>>>>>', m1.user_id)

        self.assertEqual(m1.user_id, self.u1.id)


