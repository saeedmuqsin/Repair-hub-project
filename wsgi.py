from App.app import create_app

# This is the entry point for the Flask application.
# It creates the Flask app and runs it. 
app = create_app()

if __name__ == "__main__":
    app.run()
    