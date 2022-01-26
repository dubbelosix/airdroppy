import time
import json
import argparse

from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.rpc.api import Client
from solana.rpc.types import TxOpts

from spl.token.core import _TokenCore
from spl.token.client import Token
from spl.token.instructions import get_associated_token_address

from instruction_builder import mint_new_edition_from_master_edition_instruction

TESTNET = "https://api.testnet.solana.com"
MAINNET = "https://api.mainnet-beta.solana.com"
DEVNET = "https://api.devnet.solana.com"

USENET = TESTNET

def get_addresses_edition_numbers(address_file):
    with open(address_file) as f:
        lines = filter(lambda x: "," in x, f.read().split("\n"))
    edition_number_addresses = [l.split(",") for l in lines]
    edition_number_addresses = [(PublicKey(l[0]),l[1]) for l in edition_number_addresses]
    return edition_number_addresses

def get_keypair(keypath):
    with open(keypath) as f:
        kpb = json.loads(f.read())
    return Keypair.from_secret_key(secret_key=bytes(kpb))

def await_confirmation(client, signatures, max_timeout=60, target=20, finalized=True):
    elapsed = 0
    while elapsed < max_timeout:
        sleep_time = 1
        time.sleep(sleep_time)
        elapsed += sleep_time
        resp = client.get_signature_statuses(signatures)
        if resp["result"]["value"][0] is not None:
            confirmations = resp["result"]["value"][0]["confirmations"]
            is_finalized = resp["result"]["value"][0]["confirmationStatus"] == "finalized"
        else:
            continue
        if not finalized:
            if confirmations >= target or is_finalized:
                print(f"Took {elapsed} seconds to confirm transaction")
                return
        elif is_finalized:
            print(f"Took {elapsed} seconds to confirm transaction")
            return


def execute(api_endpoint, tx, signers, skip_confirmation=True, max_timeout=60, target=20,
            finalized=True):
    client = Client(api_endpoint)
    try:
        result = client.send_transaction(tx, *signers, opts=TxOpts(skip_preflight=True))

        signatures = [x.signature for x in tx.signatures]
        if not skip_confirmation:
            await_confirmation(client, signatures, max_timeout, target, finalized)
        return result
    except Exception as e:
        import traceback
        print(traceback.format_exc())

def get_instruction_batch_fresh_mint(conn, min_balance_mint, dest, payer):
    token, txn, payer, mint_account, opts = _TokenCore._create_mint_args(
        conn, payer, payer.public_key, 0, PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"), payer.public_key, True, min_balance_mint, Token
    )
    new_mint_key = mint_account

    assoc_addr, txn2, _,_ = token._create_associated_token_account_args(dest, False)
    txn3, _, _ = token._mint_to_args(assoc_addr, payer.public_key, 1, None, TxOpts())

    txn.add(txn2).add(txn3)

    return new_mint_key, txn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='candy machine configurations')
    parser.add_argument('--usenet', action="store", choices=["devnet", "testnet", "mainnet"],
                        help='path to the keypair used for payments')
    parser.add_argument('--customnet', action="store",
                        help='custom rpc endpoint to hit')

    parser.add_argument('payment_key', action="store", help='path to the keypair used for payments')
    parser.add_argument('master_edition', action="store", help='master edition must already be created and owned by payment_key')
    parser.add_argument('airdrop_file', action="store", help='file containing addresses and edition numbers to drop. '
                                                             'Each line MUST be <address>,<edition_number>. '
                                                             'this file should not change. can be retried since edition numbers are bound to an address')

    args = parser.parse_args()
    use_network = USENET

    if args.usenet == "testnet":
        use_network = TESTNET
    elif args.usenet == "mainnet":
        use_network = MAINNET

    if args.customnet:
        use_network = args.customnet

    http_client = Client(use_network)

    source_account = get_keypair(args.payment_key)
    master_edition = PublicKey(args.master_edition)

    airdrop_file = args.airdrop_file
    address_edition_numbers = get_addresses_edition_numbers(airdrop_file)

    assoc_ta_of_master_mint = get_associated_token_address(source_account.public_key, master_edition)
    min_balance = Token.get_min_balance_rent_for_exempt_for_mint(http_client)

    for c, (dest_address, edition_number) in enumerate(address_edition_numbers):
        new_mint_token, txn = get_instruction_batch_fresh_mint(http_client, min_balance, dest_address, source_account)
        mint_new_edition_from_master_edition = mint_new_edition_from_master_edition_instruction(edition_number, master_edition,
                                                                                                new_mint_token.public_key,
                                                                                                source_account.public_key,
                                                                                                mint_authority = source_account.public_key,
                                                                                                new_mint_authority = source_account.public_key,
                                                                                                master_token_account_owner = source_account.public_key,
                                                                                                master_token_account =assoc_ta_of_master_mint,
                                                                                                payer = source_account.public_key)

        txn.add(mint_new_edition_from_master_edition)
        signers = [source_account, new_mint_token]
        print(execute(USENET, txn, signers))



