# APITester

A command-line tool for testing REST APIs. No dependencies, no setup. Just run it.

## What it does

Sends HTTP requests and shows you the response. That's basically it. It handles GET, POST, PUT, PATCH, DELETE, HEAD, and OPTIONS. If you send JSON, it figures out the content-type automatically. Response times get printed along with the status code and body.

## Getting started

You need Python 3.6 or newer. That's the only requirement.

```
python api_tester.py
```

## Examples

Basic GET request:

```
python api_tester.py GET https://api.github.com/user
```

POST with a JSON body:

```
python api_tester.py POST https://httpbin.org/post -d '{"name": "test"}'
```

Adding custom headers:

```
python api_tester.py GET https://api.github.com/user -H "Authorization: Bearer YOUR_TOKEN"
```

Saving a request for later:

```
python api_tester.py --save myapi GET https://api.example.com/data
python api_tester.py --list
```

## Output

The response shows the status code, how long it took, the response headers, and the body (formatted if it's JSON).

## License

MIT
