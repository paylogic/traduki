"""Test SQLAlchemy i18n."""
import pytest

from sqlalchemy import Column, Integer, UnicodeText
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


import traduki


@pytest.fixture
def languages():
    """Supported languages."""
    return ['en', 'pt']


@pytest.fixture
def model_class(languages):
    """Create test model class."""
    Base = declarative_base()

    traduki.initialize(Base, languages, lambda: 'en', lambda: {})

    class TestModel(Base):
        __tablename__ = 'test_table'

        id = Column(Integer, primary_key=True)

        title_id = traduki.i18n_column(nullable=False, unique=False)
        title = traduki.i18n_relation(title_id)
        """Title."""

        def save():
            pass

    return TestModel


@pytest.fixture
def model(model_class):
    """Create test model instance."""
    return model_class(id=1)


@pytest.fixture
def model_form_class(model_class):
    """Create test model form class."""
    class TestModelForm(traduki.SAModelForm):
        class Meta:
            model = model_class

    return TestModelForm


@pytest.fixture
def query(model_class, session):
    """Create SQLAlchemy Query for model_class."""
    return session.query(model_class)


@pytest.fixture
def session(request, engine):
    """SQLAlchemy session."""
    session = sessionmaker(bind=engine)()
    return session


@pytest.fixture
def engine(request, model_class):
    """SQLAlchemy engine."""
    engine = create_engine('sqlite:///:memory:')
    model_class.metadata.create_all(engine)
    return engine


def test_language_fields(model_class, languages):
    """Check that Translation class is properly generated during initialize."""
    from traduki import sqla
    assert set(dir(sqla.Translation)).issuperset(languages)
    for lang in languages:
        assert getattr(sqla.Translation, lang).type.__class__ == UnicodeText


def test_i18n_field(query, model, session):
    """Test i18n field."""
    model.title = {'en': 'En Title', 'pt': 'Pt Title'}

    session.add(model)
    session.commit()
    session.refresh(model)

    assert model.title.get_dict() == {'en': 'En Title', 'pt': 'Pt Title'}
    assert model.title.get_text() == 'En Title'
