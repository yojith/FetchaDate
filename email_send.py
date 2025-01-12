def email_send(email, pet_name):
    data = {
        'Messages': [
            {
                "From": {
                    "Email": "fetchadate123@gmail.com",
                    "Name": "FetchADate"
                },
                "To": [
                    {
                        "Email": email,
                    }
                ],
                "TemplateID": 6629892,
                "TemplateLanguage": True,
                "Subject": "Welcome to Our Service!",
                "Variables": {
                    "pet_name": pet_name,
                }
            }
        ]
    }
    return data