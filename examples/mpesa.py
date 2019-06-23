import asyncio
from aiompesa import Mpesa

CONSUMER_KEY = "nF4OwB2XiuYZwmdMz3bovnzw2qMls1b7"
CONSUMER_SECRET = "biIImmaAX9dYD4Pw"
SHORT_CODE_1 = "601376"

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    mpesa = Mpesa(True, CONSUMER_KEY, CONSUMER_SECRET)

    print("--- Getting the access token ---")
    token_response = loop.run_until_complete(mpesa.generate_token())
    access_token = token_response.get("access_token", None)
    expires_in = token_response.get("expires_in", None)
    if access_token is None:
        print("Error: Wrong credentials used to get the access_token")
    else:
        print(f"access_token = {access_token}, expires_in = {expires_in} secs")
    print("--- Done getting the access token ---")

    print("--- MPESA URL registration running ---")
    response = loop.run_until_complete(
        mpesa.register_url(
            response_type="Cancelled",
            shortcode=SHORT_CODE_1,
            confirmation_url="https://www.aio.co.ke/confirm",
            validation_url="https://www.aio.co.ke/validate",
        )
    )
    error = response.get("errorMessage", None)
    if error is not None:
        print("An error occured during registration of urls")
    print(response)
    print("--- MPESA URL registation done ---")

    print("--- MPESA c2b running ---")
    c2b = loop.run_until_complete(
        mpesa.c2b(
            amount=100, shortcode=SHORT_CODE_1, phone_number="0705867162"
        )
    )
    print(c2b)
    print("--- MPESA c2b done running---")
