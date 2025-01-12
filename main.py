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
    client = initialize_openai() 

    pets = fetch_pets_from_db()

    email = session.get("user", {}).get("userinfo", {}).get("email")
    user_pet = get_user_pet(email)

    pets = match_pets(client, user_pet, pets)
    
    species_filter = request.form.get("species_filter", "").strip()
    location_filter = request.form.get("location_filter", "").strip()
    pet_filter = PetFilter(pets)
    if species_filter:
        pet_filter.set_filter("species", species_filter)
    if location_filter:
        pet_filter.set_filter("location", location_filter)
    pets = pet_filter.filter()

    search_query = request.form.get("search_query", "").strip()
    if search_query:
        pets = search_pets(client, pets, search_query)

    return render_template("display.html", pets=pets)



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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(env.get("PORT", 8080)))
