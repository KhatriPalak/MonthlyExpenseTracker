from db import Base, engine
import models

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("All tables created successfully.")
