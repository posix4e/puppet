from sqlalchemy import JSON, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "user_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, nullable=False)
    name = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return f"User(id={self.id}, name={self.name} uid={self.uid}"


class AndroidHistory(Base):
    __tablename__ = "android_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)

    def __repr__(self):
        return f"AndroidHistory(question={self.question}, answer={self.answer}"


class BrowserHistory(Base):
    __tablename__ = "browser_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    machineid = Column(String, nullable=False)
    uid = Column(String, nullable=False)
    url = Column(String, nullable=False)

    def __repr__(self):
        return f"BrowserHistory(machineid={self.machineid}, url={self.url}"


# Add a new table to store the commands
class Command(Base):
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, nullable=False)
    command = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")

    def __repr__(self):
        return f"self.command"
