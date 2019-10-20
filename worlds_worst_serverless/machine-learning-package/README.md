# Commands to Run

## THIS DOES NOT WORK MODEL TOO BIG~~~~
```
serverless plugin install -n serverless-python-requirements

poetry run serverless invoke -f infer --data '{"body": {"input":"In a world, where dragons rule,"}}'

curl -d '{"input": "In a world, where dragons rule,"}' -H "Content-Type: application/json" -X POST https://pid3bmjeoi.execute-api.us-east-1.amazonaws.com/dev/infer

```