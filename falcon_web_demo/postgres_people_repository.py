from contextlib import contextmanager
from typing import Sequence

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from people.repositories import PeopleRepository
from people.values import Person

Base = declarative_base()


class PostgresPerson(Base):
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return "<PostgresPerson(name='{}')>".format(self.name)


class PostgresPeopleRepository(PeopleRepository):
    def __init__(self, session_provider):
        super().__init__()
        self._session_provider = session_provider

    def delete_person(self, identifier: int) -> Person:
        with self._isolated_transaction() as session:
            postgres_person = session.query(PostgresPerson).get(int(identifier))
            if postgres_person is None:
                raise PeopleRepository.NotFound()
            session.delete(postgres_person)
            identifier = postgres_person.id
            name = postgres_person.name
            return Person(identifier=identifier, name=name)

    def fetch_person(self, identifier: int) -> Person:
        with self._isolated_transaction() as session:
            postgres_person = session.query(PostgresPerson).get(int(identifier))
            if postgres_person is None:
                raise PeopleRepository.NotFound()
            identifier = postgres_person.id
            name = postgres_person.name
            return Person(identifier=identifier, name=name)

    def create_person(self, name: str) -> int:
        session = self._session_provider.get_session()
        postgres_person = PostgresPerson(name=name)
        session.add(postgres_person)
        session.commit()
        identifier = postgres_person.id
        session.close()  # untested
        return identifier

    def fetch_people(self) -> Sequence[Person]:
        session = self._session_provider.get_session()
        person_list = [Person(identifier=p.id, name=p.name) for p in session.query(PostgresPerson, PostgresPerson.id,
                                                                                   PostgresPerson.name).all()]
        session.close()  # untested

        return person_list

    @contextmanager
    def _isolated_transaction(self):
        session = self._session_provider.get_session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()