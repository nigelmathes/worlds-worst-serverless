[![Build Status](https://travis-ci.org/nigelmathes/worlds-worst-serverless.svg?branch=master)](https://travis-ci.org/nigelmathes/worlds-worst-serverless)
[![codecov](https://codecov.io/gh/nigelmathes/worlds-worst-serverless/branch/master/graph/badge.svg)](https://codecov.io/gh/nigelmathes/worlds-worst-serverless)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/ambv/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# worlds-worst-serverless
This is the world's worst serverless setup. It doesn't even start out as serverless - 
it has its own API gateway, running on a server, and drives all interactions with some
 random serverless backend thing. 

- Uses ```FastAPI``` for the API gateway.
- Uses ```Docker``` to containerize the gateway.

- Uses ```Black``` for code formatting.
- Uses ```Poetry``` for packaging.
- Uses ```pytest``` for testing.
- Uses ```Tox``` without setup.py to standardize testing (or something).
- Uses ```travisCI``` for continuous integration.
- Uses ```codecov``` for coverage reporting.

That's right, we're going all in on ```pyproject.toml```.

#### From Project Directory:
```
poetry run uvicorn worlds_worst_serverless.api_gateway.api:app --reload
```
