"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

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
db.create_all()

# app.app_context().push()
# python -m unittest test_user_model.UserModelTestCase.test_user_model



class UserModelTestCase(TestCase):
    """Test user model"""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.drop_all()
            db.create_all()

            u1 = User.signup('TestUser1', 'TestUser1@gmail.com', 'TestPassword1', None)
            u1_id = 1000
            u1.id = u1_id

            u2 = User.signup('TestUser2', 'TestUser2@gmail.com', 'TestPassword2', None)
            u2_id = 2000
            u2.id = u2_id

            db.session.commit()

            u1 = User.query.get(u1.id)
            u2 = User.query.get(u2.id)

            self.u1 = u1
            self.u2 = u2
            self.u1_id = u1_id
            self.u2_id = u2_id

            self.client = app.test_client()


    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res


    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


    def test_repr_method(self):
        """Test that repr method returns correctly"""

        expected_repr = f"<User #{self.u1_id}: {self.u1.username}, {self.u1.email}>"

        self.assertEqual(repr(self.u1), expected_repr)


#________________________________Following Tests________________________________

    def test_user_follows(self):
        """Test that user can successfully follow other users"""

        with db.session.no_autoflush:
            self.u1 = User.query.get(self.u1_id)
            self.u2 = User.query.get(self.u2_id)

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u1.following), 1)

        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertEqual(self.u1.following[0].id, self.u2.id)


    def test_is_following_method(self):
        """Test that is_following() can successfully detect when a user is following another"""

        with db.session.no_autoflush:
            self.u1 = User.query.get(self.u1_id)
            self.u2 = User.query.get(self.u2_id)

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))


    def test_is_followed_by_method(self):
        """Test that is_followed() can successfully detect when a user is being followed by another"""

        with db.session.no_autoflush:
            self.u1 = User.query.get(self.u1_id)
            self.u2 = User.query.get(self.u2_id)

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))



#________________________________Signup Tests________________________________


    def test_user_signup_valid(self):
        """Test that a new user can be signed up given valid credentials"""

        with db.session.no_autoflush:
            self.u1 = User.query.get(self.u1_id)
            self.u2 = User.query.get(self.u2_id)

        u3 = User.signup('TestUser3', 'TestUser3@gmail.com', 'TestPassword3', None)
        u3_id = 3000
        u3.id = u3_id
        db.session.commit()

        u3 = User.query.get(u3_id)

        self.assertIsNotNone(u3)
        self.assertEqual(u3.id, 3000)
        self.assertEqual(u3.username, 'TestUser3')
        self.assertEqual(u3.email, 'TestUser3@gmail.com')
        self.assertNotEqual(u3.password, 'TestPassword3')
        # Bcrypt strings should start with $2b$
        self.assertTrue(u3.password.startswith("$2b$"))
        # '/static/images/default-pic.png' is the default image when none is specified
        self.assertEqual(u3.image_url, '/static/images/default-pic.png')


    def test_signup_invalid_username(self):
        """Test that a new user cannot be signed up given invalid username"""

        u3 = User.signup(None, 'TestUser3@gmail.com', 'TestPassword3', None)

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.add(u3)
            db.session.commit()


    def test_signup_invalid_email(self):
        """Test that a new user cannot be signed up given invalid email"""

        u3 = User.signup('TestUser3', None, 'TestPassword3', None)

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.add(u3)
            db.session.commit()


    def test_signup_invalid_password(self):
        with self.assertRaises(ValueError) as context:
            User.signup("TestUser3", "TestEmail3@email.com", "", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("TestUser3", "TestEmail3@email.com", None, None)


#________________________________Authenticate Tests________________________________


    def test_authenticate_valid(self):

        with db.session.no_autoflush:
            self.u1 = User.query.get(self.u1_id)

        auth_u = User.authenticate(self.u1.username, 'TestPassword1')

        self.assertEqual(auth_u, self.u1)


    def test_authenticate_invalid_username(self):

        with db.session.no_autoflush:
            self.u1 = User.query.get(self.u1_id)

        auth_u = User.authenticate('invalid_username', 'TestPassword1')
        self.assertFalse(auth_u)
            

    def test_authenticate_invalid_password(self):

        with db.session.no_autoflush:
            self.u1 = User.query.get(self.u1_id)

        auth_u = User.authenticate(self.u1.username, 'invalid_password')
        self.assertFalse(auth_u)
