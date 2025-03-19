import factory
from faker import Faker

from app.core.security import get_password_hash
from app.db.models.user import User

faker = Faker()


class UserFactory(factory.Factory):
    """
    Factory para criação de objetos User.
    """
    class Meta:
        model = User
    
    id = factory.Sequence(lambda n: n)
    email = factory.LazyFunction(lambda: faker.email())
    full_name = factory.LazyFunction(lambda: faker.name())
    hashed_password = factory.LazyFunction(
        lambda: get_password_hash("password123")
    )
    is_active = True
    is_superuser = False
