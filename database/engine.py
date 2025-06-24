from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession # Renamed to avoid conflict
from .models import Base # Assuming models.py is in the same directory

# Global engine variable, will be initialized by init_db
engine = None
SessionLocal = None

def init_db(db_url: str = "postgresql://user:password@localhost/dbname"):
    """
    Initializes the database engine and creates tables if they don't exist.
    """
    global engine
    global SessionLocal

    if engine is None: # Initialize only once
        engine = create_engine(db_url)
        Base.metadata.create_all(engine) # Create tables defined in models.py
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print(f"Database initialized with URL: {db_url}")
    else:
        print("Database engine already initialized.")


def get_session() -> SQLAlchemySession:
    """
    Provides a database session.
    init_db() must be called before this function can be used.
    """
    if SessionLocal is None:
        raise Exception("Database not initialized. Call init_db() first.")
    return SessionLocal()

# Example usage (optional, can be removed or kept for testing)
# if __name__ == '__main__':
#     # This is just for demonstration. 
#     # In a real app, init_db() would be called at startup.
#     # For this example, using a temporary SQLite in-memory DB.
#     DEFAULT_DB_URL = "sqlite:///:memory:"
#     init_db(DEFAULT_DB_URL)
#
#     # Get a session
#     db_session = get_session()
#
#     # You can now use db_session to interact with the database, e.g.,
#     # from .models import RuleSet
#     # new_ruleset = RuleSet(name="Test Rules", rules=[{"desc": "test rule"}])
#     # db_session.add(new_ruleset)
#     # db_session.commit()
#     # print("Test ruleset added.")
#
#     # Close the session when done (important in real applications)
#     db_session.close()
#     print("Session closed.")
