from twilio.rest import Client

def twilio_sender(message):
    TWILIO_ACCOUNT_SID='AC0dad26a0182a5f3947f8115ab00a0c77'
    TWILIO_AUTH_TOKEN = '405b4ab6edeb11c9c31274dd20bfe3da'
    
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    client.messages.create(
        to = '+8201066883225',
        from_ = '+12012926576',
        body = message
    )

if __name__ == '__main__':
    twilio_sender('test')
    print("message sended.\n")
