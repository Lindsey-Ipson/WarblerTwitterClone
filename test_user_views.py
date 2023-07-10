"""User View tests."""

# run these tests like:
#    FLASK_ENV=production python -m unittest test_user_views.py

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

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
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test
app.config['WTF_CSRF_ENABLED'] = False

# Make Flask errors be real errors, not HTML pages with error info
app.config['TESTING'] = True

# Don't use Flask DebugToolbar
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.u1 = User.signup(username="test_user_1",
                                    email="test_user_1@email.com",
                                    password="password",
                                    image_url=None)
        self.u1_id = 1111
        self.u1.id = self.u1_id

        self.u2 = User.signup("test_user_2", "test_user_2@email.com", "password", None)
        self.u2_id = 2222
        self.u2.id = self.u2_id
        self.u3 = User.signup("test_user_3", "test_user_3@email.com", "password", None)
        self.u3_id = 3333
        self.u3.id = self.u3_id
        self.u4 = User.signup("test_user_4", "test_user_4@email.com", "password", None)
        self.u5 = User.signup("test_user_5", "test_user_5@email.com", "password", None)

        db.session.commit()


    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        db.drop_all()
        return resp


    def test_show_list_users(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@test_user_1", str(resp.data))
            self.assertIn("@test_user_2", str(resp.data))
            self.assertIn("@test_user_3", str(resp.data))
            self.assertIn("@test_user_4", str(resp.data))
            self.assertIn("@test_user_5", str(resp.data))


    def test_search_users(self):
        with self.client as c:
            resp = c.get("/users?q=test_user_1")

            self.assertIn("@test_user_1", str(resp.data))          

            self.assertNotIn("@test_user_2", str(resp.data))
            self.assertNotIn("@test_user_3", str(resp.data))
            self.assertNotIn("@test_user_4", str(resp.data))
            self.assertNotIn("@test_user_5", str(resp.data))  


    def test_show_user(self):
        with self.client as c:
            resp = c.get(f"/users/{self.u1_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test_user_1", str(resp.data))


    def setup_likes(self):
        m1 = Message(text="Test msg 1 for setup_likes", user_id=self.u1_id)
        m2 = Message(text="Test msg 2 for setup_likes", user_id=self.u1_id)
        m3 = Message(id=2468, text="Test msg 3 for setup_likes", user_id=self.u2_id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.u1_id, message_id=2468)

        db.session.add(l1)
        db.session.commit()


    def test_show_user_with_likes(self):
        self.setup_likes()

        with self.client as c:
            resp = c.get(f"/users/{self.u1_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test_user_1", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 2 messages
            self.assertIn("2", found[0].text)

            # Test for a count of 0 followers
            self.assertIn("0", found[1].text)

            # Test for a count of 0 following
            self.assertIn("0", found[2].text)

            # Test for a count of 1 like
            self.assertIn("1", found[3].text)


    def test_add_like(self):
        m = Message(id=46810, text="Test msg 1 for  test_add_like", user_id=self.u2_id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post("/users/toggle_like/46810", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==46810).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.u1_id)


    def test_remove_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="Test msg 3 for setup_likes").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.u1_id)

        l = Likes.query.filter(
            Likes.user_id==self.u1_id and Likes.message_id==m.id
        ).one()

        # Now we are sure that test_user_1 likes the message "Test msg 3 for setup_likes"
        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/users/toggle_like/{m.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            # the like has been deleted
            self.assertEqual(len(likes), 0)


    def test_unauthenticated_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="Test msg 3 for setup_likes").one()
        self.assertIsNotNone(m)

        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/users/toggle_like/{m.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))

            # The number of likes has not changed since making the request
            self.assertEqual(like_count, Likes.query.count())


    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.u1_id)
        f2 = Follows(user_being_followed_id=self.u3_id, user_following_id=self.u1_id)
        f3 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.u2_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()


    def test_show_user_with_follows(self):

        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.u1_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@test_user_1", str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 0 messages
            self.assertIn("0", found[0].text)

            # Test for a count of 2 following
            self.assertIn("2", found[1].text)

            # Test for a count of 1 follower
            self.assertIn("1", found[2].text)

            # Test for a count of 0 likes
            self.assertIn("0", found[3].text)


    def test_show_following(self):
        self.setup_followers()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u1_id}/following")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@test_user_2", str(resp.data))
            self.assertIn("@test_user_3", str(resp.data))
            self.assertNotIn("@test_user_4", str(resp.data))
            self.assertNotIn("@test_user_5", str(resp.data))


    def test_show_followers_valid(self):
        self.setup_followers()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u1_id}/followers")

            self.assertIn("@test_user_2", str(resp.data))
            self.assertNotIn("@test_user_3", str(resp.data))
            self.assertNotIn("@test_user_4", str(resp.data))
            self.assertNotIn("@test_user_5", str(resp.data))


    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.u1_id}/following", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@test_user_2", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))


    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.u1_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@test_user_2", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))
