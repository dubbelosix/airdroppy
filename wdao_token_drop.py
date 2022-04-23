import time
import json
import argparse

from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solana.transaction import Transaction


from spl.token.core import _TokenCore
from spl.token.client import Token
from spl.token.instructions import get_associated_token_address, transfer, TransferParams

from instruction_builder import mint_new_edition_from_master_edition_instruction, create_metadata_instruction, update_metadata_instruction
from metadata import get_create_metadata_instruction, get_update_metadata_instruction

TESTNET = "https://api.testnet.solana.com"
MAINNET = "https://ssc-dao.genesysgo.net/"
DEVNET = "https://api.devnet.solana.com"

USENET = TESTNET

def get_address_list(address_file):
    with open(address_file) as f:
        lines = filter(lambda x: len(x) > 1, f.read().split("\n"))
    addr_amounts = [l.split("\t") for l in lines]
    addr_amounts = [(PublicKey(x[0]),int(x[1])*3) for x in addr_amounts]
    return addr_amounts

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

def get_instruction_batch_xfer(conn, mint_key, dest, source_ta, payer, amount):
    token = Token(conn, mint_key, PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),payer)
    assoc_addr, txn, _,_ = token._create_associated_token_account_args(dest, False)
    params = TransferParams(
        amount=amount,
        dest=assoc_addr,
        owner=payer.public_key,
        program_id=PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
        source=source_ta,
        )
    txn_instruction = transfer(params)
    txn.add(txn_instruction)
    return txn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='candy machine configurations')
    parser.add_argument('--usenet', action="store", choices=["devnet", "testnet", "mainnet"],
                        help='path to the keypair used for payments')
    parser.add_argument('--customnet', action="store",
                        help='custom rpc endpoint to hit')

    parser.add_argument('payment_key', action="store", help='path to the keypair used for payments')
    parser.add_argument('mint_key', action="store", help='master edition must already be created and owned by payment_key')
    parser.add_argument('airdrop_file', action="store", help='file containing addresses')

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
    mint_key = PublicKey(args.mint_key)

    airdrop_file = args.airdrop_file
    addresses = get_address_list(airdrop_file)
    source_ta = get_associated_token_address(source_account.public_key, mint_key)

    for (dest_address, amount) in addresses:
        txn = get_instruction_batch_xfer(http_client, mint_key, dest_address, source_ta, source_account, amount)
        signers = [source_account]
        print(execute(use_network, txn, signers, True))



