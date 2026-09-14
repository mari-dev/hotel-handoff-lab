"""Manage private local accounts from a trusted terminal. Never print passwords."""
import argparse
import getpass
import os
from pathlib import Path
import secrets
from authentication import Auth
from invoice_store import Store

ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('--name',required=True)
    parser.add_argument('--database',type=Path,default=ROOT/'results/invoices.sqlite3')
    parser.add_argument('--bootstrap',action='store_true',help='Create first account and save random password to a private local file')
    args=parser.parse_args();args.database.parent.mkdir(parents=True,exist_ok=True)
    auth=Auth(Store(args.database))
    if args.bootstrap:
        if auth.has_users(): raise SystemExit('Accounts already exist; use the interactive command to change a password.')
        output=args.database.parent/'local-login.txt'
        # Exclusive creation avoids replacing another credential file.
        fd=os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        password=secrets.token_urlsafe(24)
        with os.fdopen(fd,'w') as file:
            auth.set_password(args.username,password,args.name)
            file.write(f'Private local login — do not share or commit\nURL: http://localhost:8765/login\nUsername: {args.username}\nPassword: {password}\n')
        print(f'First account created. Private credentials: {output}')
    else:
        password=getpass.getpass('New password (at least 12 characters): ')
        if password!=getpass.getpass('Repeat password: '): raise SystemExit('Passwords do not match')
        auth.set_password(args.username,password,args.name)
        print('Account updated; previous sessions revoked.')

if __name__=='__main__': main()
