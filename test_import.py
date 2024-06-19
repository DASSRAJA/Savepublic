# test_import.py
try:
    import flask_bcrypt
    print("flask_bcrypt is installed and can be imported.")
except ImportError as e:
    print("ImportError:", e)
