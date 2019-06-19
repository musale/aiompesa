import asyncio
from aiompesa import Mpesa

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    mpesa = Mpesa(True, "51Bg1WQcZ9g0yq0DSjogNwLpsxxUQzD1", "roLeNZCP5BVcmXDa")
    token_response = loop.run_until_complete(mpesa.generate_token())
    access_token = token_response.get("access_token", None)
    expires_in = token_response.get("expires_in", None)
    if access_token is None:
        print("Error: Wrong credentials used to get the access_token")
    else:
        print(f"access_token = {access_token}, expires_in = {expires_in} secs")

    response = loop.run_until_complete(
        mpesa.register_url(
            response_type="Cancelled",
            shortcode="601376",
            confirmation_url="https://www.nisave.co.ke/confirm",
            validation_url="https://www.nisave.co.ke/validate",
        )
    )
    error = response.get("errorMessage", None)
    if error is not None:
        print("An error occured")
    print(response)
