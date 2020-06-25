from twilio.rest import Client

def twilio_sender(message):
    TWILIO_ACCOUNT_SID='your_twilio_account_cid'
    TWILIO_AUTH_TOKEN = 'your_twilio_auth_token'
    
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    client.messages.create(
        to = 'user_phone_num',
        from_ = 'your_twilio_num',
        body = message
    )

if __name__ == '__main__':
    twilio_sender('test')
    print("message sended.\n")
