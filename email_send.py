from mailjet_rest import Client

# Mailjet API credentials
API_KEY = 'd15542b03747edc4a204de289c8f24e5'
SECRET_KEY = 'b89b9157e8d1b4a0f3a9e075c298adee'

# Initialize Mailjet client
mailjet = Client(auth=(API_KEY, SECRET_KEY), version='v3.1')

# Email data
data = {
    'Messages': [
        {
            "From": {
                "Email": "fetchadate123@gmail.com",  # Verified email address
                "Name": "FetchADate"
            },
            "To": [
                {
                    "Email": "alafifhams@gmail.com",
                    "Name": "Hams"
                }
            ],
            "TemplateID": 6629892,
            "TemplateLanguage": True,
            "Subject": "Welcome to Our Service!",
            "Variables": {  # Pass dynamic variables here
                "pet_name": "charlie",
            }
        }
    ]
}

# Send the email
result = mailjet.send.create(data=data)
print(result.status_code)
print(result.json())