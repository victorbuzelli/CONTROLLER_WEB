from db import Session
from models import User

def load_user(user_id):
    with Session() as session:
        user = session.query(User).get(int(user_id))
        return user