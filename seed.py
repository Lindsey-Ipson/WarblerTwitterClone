# """Seed database with sample data from CSV Files."""

# from csv import DictReader
# from app import db, app
# # just added app
# from models import User, Message, Follows


# # db.drop_all()
# # db.create_all()

# # just added
# with app.app_context():
#     db.drop_all()
#     db.create_all()


# with open('generator/users.csv') as users:
#     db.session.bulk_insert_mappings(User, DictReader(users))

# with open('generator/messages.csv') as messages:
#     db.session.bulk_insert_mappings(Message, DictReader(messages))

# with open('generator/follows.csv') as follows:
#     db.session.bulk_insert_mappings(Follows, DictReader(follows))

# db.session.commit()



"""Seed database with sample data from CSV Files."""

from csv import DictReader
from app import db, app
from models import User, Message, Follows

# Create the database tables
with app.app_context():
    db.drop_all()
    db.create_all()

    # Seed the database with data from CSV files
    with open('generator/users.csv') as users:
        db.session.bulk_insert_mappings(User, DictReader(users))

    with open('generator/messages.csv') as messages:
        db.session.bulk_insert_mappings(Message, DictReader(messages))

    with open('generator/follows.csv') as follows:
        db.session.bulk_insert_mappings(Follows, DictReader(follows))

    # Commit the changes to the database
    db.session.commit()
