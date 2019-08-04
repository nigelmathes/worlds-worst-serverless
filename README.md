# worlds-worst-serverless
This is the world's worst serverless setup. It doesn't even start out as serverless - 
it creates it own damned API gateway and expects that to drive all interactions with 
some random serverless backend thing. 

- Uses ```FastAPI``` for the API gateway.
- Uses ```Docker``` to containerize the gateway.

- Uses ```Black``` for code formatting.
- Uses ```Poetry``` for packaging.
- Uses ```pytest``` for testing.
- Uses ```Tox``` without setup.py to standardize testing (or something).
- Uses ```travisCI``` for continuous integration.

That's right, we're going all in on ```pyproject.toml```.

#### From Project Directory:
```
poetry run uvicorn api.api:app --reload
```
