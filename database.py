import pymongo

password = "yHxg7TBrCJPZF12t"
connection = f"mongodb+srv://yojith23:{password}@cluster0.phckh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


class PetDatabase:
    _myclient = pymongo.MongoClient(connection)
    _pet_database = _myclient["PetDatabase"]
    _user_database = _pet_database["UserDatabase"]

    @classmethod
    def check_user(cls, email: str):
        """
        Checks if a user exists in the database
        """
        check = cls._user_database.find_one({"_id": email})
        return check != None

    @classmethod
    def new_user(cls, data: dict):
        """
        Document in the format:
        {}
        """
        email = data["email"]
        data["_id"] = email
        check = cls._user_database.find_one({"_id": email})
        if check:
            return "User Already Exists!"
        document_id = cls._user_database.insert_one(data)
        return document_id

    @classmethod
    def get_pets_from_description(cls, description: str):
        """
        Returns a sequence of pets that include a particular description
        """
        query = {"description": {"$regex": f"^{description}"}}
        results = cls._user_database.find(query)
        return results

    @classmethod
    def get_pets_from_query(cls, query: dict):
        """
        Returns a sequence of pets that adhere to the provided query dictionary
        """
        results = cls._user_database.find(query)
        return results

    @classmethod
    def get_user_from_email(cls, email: str):
        """
        Gets a user from an email address
        """
        query = {"_id": email}
        result = cls._user_database.find_one(query)
        return result


if __name__ == "__main__":
    petdb = PetDatabase()
    print(
        petdb.new_user(
            {
                "name": "yojith",
                "email": "yojith23@gmail.com",
                "description": "blablabla",
            }
        )
    )
    print(
        petdb.new_user(
            {
                "name": "user123",
                "email": "someone@gmail.com",
                "description": "abcd",
            }
        )
    )
    print(
        petdb.new_user(
            {
                "name": "user456",
                "email": "someone_else@gmail.com",
                "description": "blabla 1234",
            }
        )
    )
    x = petdb.get_pets_from_description("blabla")
    for y in x:
        print(y["email"])

    print(petdb.check_user("johnny"))
    print(petdb.check_user("yojith23@gmail.com"))
