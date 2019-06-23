import asyncio

from aiompesa import Mpesa

CONSUMER_KEY = "nF4OwB2XiuYZwmdMz3bovnzw2qMls1b7"
CONSUMER_SECRET = "biIImmaAX9dYD4Pw"
SHORT_CODE_1 = "601376"
SHORT_CODE_2 = "600000"
LIPA_NA_MPESA = "174379"
LIPA_NA_MPESA_KEY = (
    "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
)
SEC_CREDENTIAL = (
    "fqW2kW0hNOoeSbh+sd0qrSfFwAHJcxy1VlCqPGuu2MtRYPITI35CQApGPg"
    "2mE8d9SMmvXSB/hTeyV6apg3sJyqSfe4HK0p1UelW1wVpER2yctyI+"
    "YMqgDUx+OK+Zu5dUACuXb9Cpf5FSCJ++yA/At0K8wDaBMlkaN4eAkZJpN"
    "80z7VMHTtuWvecnrtazdzvxnA0+2jIt7vd8PJSVrFX9WBw/KV1SKZHjx35xn"
    "Duv4EgQlgNk8MQwV4Er5ITvqQZmHSZpsUNjtaDrU6hGrhoDz0m3Y2y7THu7"
    "EzHJMAvzRoh6oo7ktvwzDRQRNgT7PzlUG6/eUuaJJTBUayEj6EbKBw=="
)
INITIATOR_NAME = "apitest376"

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

    print("--- Generate the initiator password ---")
    sec_cred = mpesa.generate_security_credential(
        cert_location="examples/cert.cer", initiator_password="whoas"
    )
    sec_cred = sec_cred.decode()
    print("--- Done generating secret credentials ---")
    print("--- MPESA b2c running ---")
    party_b = "254705867162"
    b2c = loop.run_until_complete(
        mpesa.b2c(
            initiator_name=INITIATOR_NAME,
            security_credential=sec_cred,
            command_id="BusinessPayment",
            amount=100,
            party_a=SHORT_CODE_1,
            party_b=party_b,
            remarks=f"Deposit to {party_b}",
            queue_timeout_url="https://www.aio.co.ke/queue/",
            result_url="https://www.aio.co.ke/result/",
        )
    )
    print(b2c)
    print("--- MPESA done running b2c ---")
    print("--- MPESA b2b running ---")
    b2b = loop.run_until_complete(
        mpesa.b2b(
            initiator_name=INITIATOR_NAME,
            security_credential=sec_cred,
            command_id="BusinessBuyGoods",
            amount=100,
            party_a=SHORT_CODE_1,
            party_b=SHORT_CODE_2,
            remarks=f"Deposit to {party_b}",
            queue_timeout_url="https://www.aio.co.ke/queue/",
            result_url="https://www.aio.co.ke/result/",
        )
    )
    print(b2b)
    print("--- MPESA b2b done running ---")

    print("--- MPESA b2b running ---")
    stk = loop.run_until_complete(
        mpesa.stk_push(
            lipa_na_mpesa_shortcode=LIPA_NA_MPESA,
            lipa_na_mpesa_passkey=LIPA_NA_MPESA_KEY,
            amount=100,
            party_a="0705867162",
            party_b=LIPA_NA_MPESA,
            transaction_desc=f"Deposit from {party_b}",
            callback_url="https://www.aio.co.ke/queue/",
        )
    )
    print(stk)
    print("--- MPESA stk done running ---")
