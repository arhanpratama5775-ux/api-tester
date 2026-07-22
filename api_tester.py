#!/usr/bin/env python3
"""
APITester - Simple REST API Testing Tool
A lightweight CLI tool for testing REST APIs with ease.

Usage:
    python api_tester.py <method> <url> [options]

Examples:
    python api_tester.py GET https://api.github.com/user
    python api_tester.py POST https://httpbin.org/post -d '{"name": "test"}'
    python api_tester.py PUT https://httpbin.org/put -d '{"id": 1}' -H "Content-Type: application/json"
    python api_tester.py DELETE https://httpbin.org/delete
"""

import sys
import json
import time
import argparse
from urllib import request, error, parse
from datetime import datetime


# ══════════════════════════════════════════════════
#  COLORS
# ══════════════════════════════════════════════════
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


def print_color(text, color):
    print(f"{color}{text}{Colors.ENDC}")


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'═' * 50}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'═' * 50}{Colors.ENDC}\n")


# ══════════════════════════════════════════════════
#  REQUEST BUILDER
# ══════════════════════════════════════════════════
def build_request(method, url, headers=None, data=None):
    """Build urllib Request object"""
    if headers is None:
        headers = {}
    
    # Auto-detect JSON content-type
    if data and isinstance(data, str):
        try:
            json.loads(data)
            if 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
        except json.JSONDecodeError:
            pass
    
    # Encode data if provided
    encoded_data = None
    if data:
        if isinstance(data, dict):
            encoded_data = json.dumps(data).encode('utf-8')
        elif isinstance(data, str):
            encoded_data = data.encode('utf-8')
    
    req = request.Request(url, data=encoded_data, headers=headers, method=method)
    return req


# ══════════════════════════════════════════════════
#  EXECUTE REQUEST
# ══════════════════════════════════════════════════
def execute_request(req):
    """Execute HTTP request and return response info"""
    result = {
        'status': None,
        'status_text': None,
        'headers': {},
        'body': None,
        'time_ms': 0,
        'size_bytes': 0,
        'error': None
    }
    
    try:
        start_time = time.time()
        with request.urlopen(req, timeout=30) as response:
            elapsed = (time.time() - start_time) * 1000
            
            body = response.read().decode('utf-8')
            
            result['status'] = response.status
            result['status_text'] = response.reason
            result['headers'] = dict(response.headers)
            result['body'] = body
            result['time_ms'] = round(elapsed, 2)
            result['size_bytes'] = len(body.encode('utf-8'))
            
    except error.HTTPError as e:
        elapsed = (time.time() - start_time) * 1000
        body = e.read().decode('utf-8') if e.fp else ''
        
        result['status'] = e.code
        result['status_text'] = e.reason
        result['headers'] = dict(e.headers)
        result['body'] = body
        result['time_ms'] = round(elapsed, 2)
        result['size_bytes'] = len(body.encode('utf-8'))
        
    except error.URLError as e:
        result['error'] = str(e.reason)
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


# ══════════════════════════════════════════════════
#  DISPLAY RESULTS
# ══════════════════════════════════════════════════
def display_results(req, result):
    """Display request/response in a nice format"""
    print_header("API Test Results")
    
    # Request info
    print_color("📤 REQUEST", Colors.BOLD)
    print_color(f"  Method:   {req.method}", Colors.BLUE)
    print_color(f"  URL:      {req.full_url}", Colors.BLUE)
    if req.headers:
        print_color(f"  Headers:", Colors.BLUE)
        for k, v in req.headers.items():
            print_color(f"    {k}: {v}", Colors.DIM)
    if req.data:
        print_color(f"  Body:     {req.data[:100]}{'...' if len(req.data) > 100 else ''}", Colors.DIM)
    print()
    
    # Error
    if result['error']:
        print_color("❌ ERROR", Colors.RED)
        print_color(f"  {result['error']}", Colors.RED)
        return
    
    # Status
    status = result['status']
    if 200 <= status < 300:
        status_color = Colors.GREEN
        status_icon = "✅"
    elif 300 <= status < 400:
        status_color = Colors.YELLOW
        status_icon = "↪️"
    elif 400 <= status < 500:
        status_color = Colors.YELLOW
        status_icon = "⚠️"
    else:
        status_color = Colors.RED
        status_icon = "❌"
    
    print_color(f"{status_icon} RESPONSE", Colors.BOLD)
    print_color(f"  Status:   {status} {result['status_text']}", status_color)
    print_color(f"  Time:     {result['time_ms']}ms", Colors.CYAN)
    print_color(f"  Size:     {format_size(result['size_bytes'])}", Colors.CYAN)
    print()
    
    # Response Headers
    print_color("📋 RESPONSE HEADERS", Colors.BOLD)
    for k, v in result['headers'].items():
        print_color(f"  {k}: {v}", Colors.DIM)
    print()
    
    # Response Body
    print_color("📦 RESPONSE BODY", Colors.BOLD)
    body = result['body']
    if body:
        try:
            # Try to format JSON
            json_body = json.loads(body)
            formatted = json.dumps(json_body, indent=2, ensure_ascii=False)
            print(formatted)
        except json.JSONDecodeError:
            # Not JSON, print as-is
            print(body)
    else:
        print_color("  (empty)", Colors.DIM)


def format_size(size_bytes):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} GB"


# ══════════════════════════════════════════════════
#  SAVE/LOAD REQUESTS
# ══════════════════════════════════════════════════
def save_request(name, method, url, headers=None, data=None):
    """Save a request to file"""
    history_file = 'request_history.json'
    
    history = []
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    entry = {
        'name': name,
        'method': method,
        'url': url,
        'headers': headers or {},
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    history.append(entry)
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    print_color(f"✅ Request '{name}' saved!", Colors.GREEN)


def list_saved_requests():
    """List all saved requests"""
    history_file = 'request_history.json'
    
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print_color("No saved requests found.", Colors.YELLOW)
        return
    
    if not history:
        print_color("No saved requests found.", Colors.YELLOW)
        return
    
    print_header("Saved Requests")
    for i, req in enumerate(history, 1):
        print_color(f"{i}. {req['name']}", Colors.BOLD)
        print_color(f"   {req['method']} {req['url']}", Colors.CYAN)
        print_color(f"   Saved: {req['timestamp'][:19]}", Colors.DIM)
        print()


# ══════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description='APITester - Simple REST API Testing Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s GET https://api.github.com/user
  %(prog)s POST https://httpbin.org/post -d '{"name": "test"}'
  %(prog)s PUT https://httpbin.org/put -d '{"id": 1}' -H "Authorization: Bearer token123"
  %(prog)s DELETE https://httpbin.org/delete
  %(prog)s --save myapi GET https://api.example.com/data
  %(prog)s --list
        """
    )
    
    parser.add_argument('method', nargs='?', choices=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'],
                        help='HTTP method')
    parser.add_argument('url', nargs='?', help='Request URL')
    parser.add_argument('-d', '--data', help='Request body (JSON string)')
    parser.add_argument('-H', '--header', action='append', help='Header (format: "Key: Value")')
    parser.add_argument('-s', '--save', help='Save request with name')
    parser.add_argument('-l', '--list', action='store_true', help='List saved requests')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds (default: 30)')
    
    args = parser.parse_args()
    
    # List saved requests
    if args.list:
        list_saved_requests()
        return
    
    # Validate required args
    if not args.method or not args.url:
        parser.print_help()
        return
    
    # Parse headers
    headers = {}
    if args.header:
        for h in args.header:
            if ':' in h:
                key, value = h.split(':', 1)
                headers[key.strip()] = value.strip()
    
    # Build and execute request
    print_header(f"Testing {args.method} {args.url}")
    
    req = build_request(args.method, args.url, headers, args.data)
    result = execute_request(req)
    
    # Display results
    display_results(req, result)
    
    # Save if requested
    if args.save:
        save_request(args.save, args.method, args.url, headers, args.data)


if __name__ == '__main__':
    main()
