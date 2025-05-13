from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, password, pasta_id):
        self.id = id
        self.username = username
        self.password = password
        self.pasta_id = pasta_id

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

USUARIOS = {
    'comercialuiza@gmail.com': {'senha': '33241990', 'pasta_id': '17BhKhWYRF45ygQevd-tv5AdSSztGD9yO'},
    'andersonbuzelli01@gmail.com': {'senha': '33241990', 'pasta_id': '1wjDMahSNCtCFhk6f5Z1LQEE-_7CkVjQV'}
    # Adicione mais clientes de teste conforme necessário
}