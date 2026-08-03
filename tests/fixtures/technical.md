The authorization server redirects the browser to `/oauth/callback`. That route serves as the OAuth callback and exchanges the temporary code exactly once. Store the verifier in the encrypted session, reject a missing state value, and expire the session after five minutes.

Do not log access tokens. Do not retry a rejected code. Do not accept a callback whose origin differs from the configured issuer. These three constraints protect distinct boundaries; the repetition is deliberate.

The worker records the status, latency, and issuer for each exchange. A status of 409 means another worker completed the exchange first, so the current request should return the stored result without contacting the issuer again.
