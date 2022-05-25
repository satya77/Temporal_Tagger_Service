from app import app
from argparse import ArgumentParser

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("--port", type=int, default=5200, help="Choose port. (Default: 5000)")
    parser.add_argument("--values", action="store_true", help="Show values.")
    parser.add_argument("--temporal_api_host",type=str,default="http://localhost:8001", help="The address to temporal api.")
    args = parser.parse_args()
    app.run(host="localhost", port=args.port)