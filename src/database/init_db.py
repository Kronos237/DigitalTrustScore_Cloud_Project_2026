"""Initialize the configured database without deleting existing data."""

from .session import DATABASE_URL, initialize_database


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized: {DATABASE_URL}")