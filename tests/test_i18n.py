"""Test SQLAlchemy i18n."""
import pytest

from sqlalchemy import Column, Integer, UnicodeText
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


import traduki


Base = declarative_base()


@pytest.fixture(scope='session')
def languages():
    """Supported languages."""
    return ['en', 'pt']


@pytest.fixture(scope='session')
def i18n_attributes(languages):
    """i18n attributes"""
    return traduki.initialize(Base, languages, lambda: 'en', lambda: {})


@pytest.fixture(scope='session')
def model_class(i18n_attributes):
    """Create test model class."""

    class TestModel(Base):
        __tablename__ = 'test_table'

        id = Column(Integer, primary_key=True, autoincrement=True)

        title_id = i18n_attributes.i18n_column(nullable=False, unique=False)
        title = i18n_attributes.i18n_relation(title_id)
        """Title."""

        def save():
            pass

    return TestModel


@pytest.fixture
def query(model_class, session):
    """Create SQLAlchemy Query for model_class."""
    return session.query(model_class)


@pytest.fixture
def session(request, engine):
    """SQLAlchemy session."""
    session = sessionmaker(bind=engine)()
    return session


@pytest.fixture(scope='session')
def engine(request, model_class):
    """SQLAlchemy engine."""
    engine = create_engine('sqlite:///:memory:')
    model_class.metadata.create_all(engine)
    return engine


@pytest.fixture
def model_title():
    """Model title."""
    return {'en': 'En Title', 'pt': 'Pt Title'}


@pytest.fixture
def model(session, model_class, model_title):
    """Model instance."""
    model = model_class(title=model_title)
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def test_language_fields(model_class, languages, i18n_attributes):
    """Check that Translation class is properly generated during initialize."""
    assert set(dir(i18n_attributes.Translation)).issuperset(languages)
    for lang in languages:
        assert getattr(i18n_attributes.Translation, lang).type.__class__ == UnicodeText


def test_i18n_field(query, model, model_title):
    """Test i18n field."""
    assert model.title.get_dict() == model_title
    assert model.title.get_text() == 'En Title'


def test_class_custom_table(languages):
    """Test initialization with custom table."""
    Base = declarative_base()

    i18n_attributes = traduki.initialize(
        Base, languages, lambda: 'en', lambda: {}, attributes={'__tablename__': 'custom_table'})

    assert i18n_attributes.Translation.__tablename__ == 'custom_table'


def test_set(model):
    """Test changing of the field value."""
    model.title = {'en': 'New'}
    assert model.title.get_dict() == {'en': 'New'}


def test_comparator(session, model, model_class):
    """Test field comparator."""
    assert model in session.query(model_class).filter(model_class.title.startswith('En Title'))
    assert model in session.query(model_class).filter(model_class.title.startswith('Pt Title'))
    assert model in session.query(model_class).filter(model_class.title.contains('En'))
    assert model in session.query(model_class).filter(model_class.title.contains('Pt'))
