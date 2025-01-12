from flask import Flask, render_template, request, redirect, session, url_for, send_file
from urllib.parse import quote_plus, urlencode
from database import PetDatabase


from bson import Binary
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from os import environ as env
from os import path
import io

from search import initialize_openai, search_pets
from filter import fetch_pets_from_db, PetFilter
from match import match_pets, get_user_pet
from email_send import email_send
import requests

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


@app.route("/")
def landing():
    user = session.get("user")
    if user:
        if not PetDatabase.check_user(user["userinfo"]["email"]):
            return redirect("/signup")

    return render_template("landing.html", session=user)


@app.route("/profile")
def profile():
    user = session.get("user")
    if user:
        if not PetDatabase.check_user(user["userinfo"]["email"]):
            return redirect("/signup")

        email = user["userinfo"]["email"]
        user_info = PetDatabase.get_user_from_email(email)
        pet_name = user_info["pet_name"]
        pet_species = user_info["species_name"]
        owner_name = user_info["owner_name"]
        description = user_info["description"]
        
        profile_picture = user_info["profile_picture"]
        filepath = path.join("static", "profile_picture.jpg")
        with open(filepath, "wb") as file:
            file.write(profile_picture)

        
    else:
        pet_name, pet_species, owner_name, description = ("Pet Not Found!") * 3

    return render_template(
        "profile.html",
        pet_name=pet_name,
        pet_species=pet_species,
        owner_name=owner_name,
        description=description,
    )


@app.route("/matches", methods=["GET", "POST"])
def matches():
    user = session.get("user")
    email = user["userinfo"]["email"]
    user_pet = get_user_pet(email)

    pets = fetch_pets_from_db()
    client = initialize_openai()

    # Default sorting by matching
    pets = match_pets(client, user_pet, pets)

    # Handle search
    query = request.args.get("search", "").strip()
    if query:
        pets = search_pets(client, pets, query)

    # Handle filters
    filter_species = request.args.get("species", "false")
    filter_location = request.args.get("location", "false")

    if filter_species == "true" or filter_location == "true":
        pet_filter = PetFilter(pets)
        if filter_species == "true":
            pet_filter.set_filter("species", user_pet["species_name"])
        if filter_location == "true":
            pet_filter.set_filter("location", user_pet["location"])
        pets = pet_filter.filter()

    # Pass current filters to the template
    return render_template(
        "matches.html",
        pets=pets,
        search=query,
        filter_species=filter_species,
        filter_location=filter_location,
    )
    

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/profile")


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("landing", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        pet_name = request.form["pet-name"]
        pet_species = request.form["pet-species"]
        owner_name = request.form["owner-name"]
        location = request.form["location"]
        description = request.form["pet-description"]

        profile_picture = request.files["profile-picture"]
        binary_image = Binary(profile_picture.read())

        data = {
            "email": session.get("user")["userinfo"]["email"],
            "pet_name": pet_name,
            "species_name": pet_species,
            "owner_name": owner_name,
            "location": location,
            "description": description,
            "profile_picture": binary_image,
        }
        PetDatabase.new_user(data)
        return redirect("/profile")

    return render_template("signup.html")

@app.route("/email", methods=["POST", "GET"])
def email():
    if request.method == "POST": 
        email = request.form["email"] 
        pet_name = request.form["pet-name"]
        print(email)
        print(pet_name)

        # API URL
        url = "https://api.mailjet.com/v3.1/send"

        # Mailjet credentials
        API_KEY = "d15542b03747edc4a204de289c8f24e5"
        SECRET_KEY = "b89b9157e8d1b4a0f3a9e075c298adee"

        # Send the email
        data = email_send(email, pet_name)
        response = requests.post(url, auth=(API_KEY, SECRET_KEY), json=data)

        if response.status_code == 200:
            return render_template("email.html", session=session["user"])

        else:
            print(f"Failed to send email. Status code: {response.status_code}")
            return "Email failed!" # take to some confirmation page


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(env.get("PORT", 8080)))