import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tests.conftest import SQLModel, engine

try:
    print("Tables before create_all:", SQLModel.metadata.tables.keys())
    SQLModel.metadata.create_all(engine)
    print("create_all succeeded.")
except Exception as e:
    import traceback
    traceback.print_exc()
