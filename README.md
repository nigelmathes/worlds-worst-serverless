[![Build Status](https://travis-ci.org/nigelmathes/worlds-worst-serverless.svg?branch=master)](https://travis-ci.org/nigelmathes/worlds-worst-serverless)
[![codecov](https://codecov.io/gh/nigelmathes/worlds-worst-serverless/branch/master/graph/badge.svg)](https://codecov.io/gh/nigelmathes/worlds-worst-serverless)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/ambv/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# worlds-worst-serverless
This is the world's worst serverless setup.

- Uses ```FastAPI``` for the API gateway (if you need one).
- Uses ```Docker``` to containerize the gateway.
- Uses ```Black``` for code formatting.
- Uses ```Poetry``` for packaging.
- Uses ```pytest``` for testing.
- Uses ```Tox``` without setup.py to standardize testing (or something).
- Uses ```travisCI``` for continuous integration.
- Uses ```codecov``` for coverage reporting.
- Uses ```Serverless Framework``` for testing and deploying serverless apps.

This repo will be all in on ```pyproject.toml```.

# Some good Serverless Framework commands
```
npm install -g serverless

serverless config credentials --provider aws --key KEY --secret
 SECRET

serverless install -u https://github.com/serverless/examples/tree/master/aws-python-simple-http-endpoint

serverless deploy -v

serverless invoke local -f myFunction -l
```