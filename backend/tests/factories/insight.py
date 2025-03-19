import random
from datetime import datetime, timedelta

import factory
from faker import Faker

from app.db.models.insight import Insight
from tests.factories.user import UserFactory

faker = Faker()


class InsightFactory(factory.Factory):
    """
    Factory para criação de objetos Insight.
    """
    class Meta:
        model = Insight
    
    id = factory.Sequence(lambda n: n)
    title = factory.LazyFunction(lambda: faker.sentence(nb_words=5))
    content = factory.LazyFunction(lambda: faker.text(max_nb_chars=500))
    tags = factory.LazyFunction(
        lambda: [faker.word() for _ in range(random.randint(1, 5))]
    )
    created_at = factory.LazyFunction(
        lambda: datetime.now() - timedelta(days=random.randint(1, 30))
    )
    updated_at = factory.LazyFunction(lambda: datetime.now())
    user_id = factory.SubFactory(UserFactory).id
    is_active = True
