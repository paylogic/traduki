"""Test SQLAlchemy i18n."""
from __future__ import unicode_literals
import pytest
import six

from sqlalchemy import Column, Integer, UnicodeText, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import traduki


Base = declarative_base()


@pytest.fixture(scope='session')
def languages():
    """Supported languages."""
    return ['en', 'nl', 'pt']


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
    return {'en': 'En Title', 'nl': 'Nl Title', 'pt': 'Pt Title'}


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


@pytest.mark.parametrize(
    'model_title, expected',
    [
        ({'en': 'english title', 'nl': 'dutch title'}, 'english title'),
        ({'nl': 'dutch title'}, 'dutch title'),
        ({}, ''),
    ]
)
def test_stringification(model, expected):
    """Test that str(model) returns a string with the translated text."""
    assert six.text_type(model.title) == expected


def test_startswith(session, model, model_class):
    """Test startswith comparator."""
    assert model in session.query(model_class).filter(model_class.title.startswith('En Title'))
    assert model in session.query(model_class).filter(model_class.title.startswith('Pt Title'))
    assert model not in session.query(model_class).filter(model_class.title.startswith('Fr Title'))


def test_contains(session, model, model_class):
    """Test contains comparator."""
    assert model in session.query(model_class).filter(model_class.title.contains('En'))
    assert model in session.query(model_class).filter(model_class.title.contains('Pt'))
    assert model not in session.query(model_class).filter(model_class.title.contains('Fr'))


def test_inheritance(languages):
    Base = declarative_base()

    i18n_attributes = traduki.initialize(Base, languages, lambda: 'en', lambda: {})

    class Animal(Base):
        __tablename__ = 'animal'
        __mapper_args__ = {
            'polymorphic_on': 'type',
            'with_polymorphic': '*'
        }

        id = Column(Integer, primary_key=True, autoincrement=True)

        name_id = i18n_attributes.i18n_column(nullable=False, unique=False)
        name = i18n_attributes.i18n_relation(name_id)

        type = Column(String(255), nullable=False, index=True)

    class Dog(Animal):
        __mapper_args__ = {'polymorphic_identity': 'dog'}

    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)

    session = sessionmaker(bind=engine)()

    d = Dog()
    d.name = {'en': 'Bob'}
    assert d.name.get_dict()['en'] == 'Bob'

    session.add(d)
    session.commit()
    assert d.name.get_dict()['en'] == 'Bob'
