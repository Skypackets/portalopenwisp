#!/usr/bin/env python3
import argparse
import json
from connectors.cambium_cnmaestro import CambiumClient, CambiumError


def main():
    parser = argparse.ArgumentParser(description="Cambium cnMaestro guest utility")
    sub = parser.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create", help="Create guest user")
    c.add_argument("username")
    c.add_argument("password")
    c.add_argument("--minutes", type=int, default=60)

    d = sub.add_parser("delete", help="Delete guest user")
    d.add_argument("id", help="Guest account id")

    args = parser.parse_args()
    client = CambiumClient()

    try:
        if args.cmd == "create":
            data = client.create_guest_user(args.username, args.password, args.minutes)
            print(json.dumps(data))
        elif args.cmd == "delete":
            client.delete_guest_user(args.id)
            print(json.dumps({"status": "deleted", "id": args.id}))
    except CambiumError as exc:
        print(json.dumps({"error": str(exc)}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()

