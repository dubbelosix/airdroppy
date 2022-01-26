import math

from solana.publickey import PublicKey
from solana.transaction import AccountMeta, TransactionInstruction

from metadata import get_mint_new_edition_from_master_edition_instruction


METADATA_PROGRAM_ID = PublicKey('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')
SYSTEM_PROGRAM_ID = PublicKey('11111111111111111111111111111111')
SYSVAR_RENT_PUBKEY = PublicKey('SysvarRent111111111111111111111111111111111')
ASSOCIATED_TOKEN_ACCOUNT_PROGRAM_ID = PublicKey('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
TOKEN_PROGRAM_ID = PublicKey('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')

def get_metadata_account(mint_key):
    return PublicKey.find_program_address(
        [b'metadata', bytes(METADATA_PROGRAM_ID), bytes(PublicKey(mint_key))],
        METADATA_PROGRAM_ID
    )[0]

def get_edition(mint_key):
    return PublicKey.find_program_address(
        [b'metadata', bytes(METADATA_PROGRAM_ID), bytes(PublicKey(mint_key)), b"edition"],
        METADATA_PROGRAM_ID
    )[0]


def get_edition_number_pda(mint_key, edition_number):
    # EDITION_MARKER_BIT_SIZE = 248
    edition_number = math.floor(edition_number / 248)
    return PublicKey.find_program_address(
        [b'metadata', bytes(METADATA_PROGRAM_ID), bytes(PublicKey(mint_key)), b"edition", str(edition_number).encode()],
        METADATA_PROGRAM_ID
    )[0]


def create_metadata_instruction(data, update_authority, mint_key, mint_authority_key, payer):
    metadata_account = get_metadata_account(mint_key)
    keys = [
        AccountMeta(pubkey=metadata_account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=mint_key, is_signer=False, is_writable=False),
        AccountMeta(pubkey=mint_authority_key, is_signer=True, is_writable=False),
        AccountMeta(pubkey=payer, is_signer=True, is_writable=False),
        AccountMeta(pubkey=update_authority, is_signer=False, is_writable=False),
        AccountMeta(pubkey=SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
    ]
    return TransactionInstruction(keys=keys, program_id=METADATA_PROGRAM_ID, data=data)


def update_metadata_instruction(data, update_authority, mint_key):
    metadata_account = get_metadata_account(mint_key)
    keys = [
        AccountMeta(pubkey=metadata_account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=update_authority, is_signer=True, is_writable=False),
    ]
    return TransactionInstruction(keys=keys, program_id=METADATA_PROGRAM_ID, data=data)


def create_master_edition_instruction(data, mint, update_authority, mint_authority, payer):
    edition_account = get_edition(mint)
    metadata_account = get_metadata_account(mint)
    keys = [
        AccountMeta(pubkey=edition_account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=mint, is_signer=False, is_writable=True),
        AccountMeta(pubkey=update_authority, is_signer=True, is_writable=False),
        AccountMeta(pubkey=mint_authority, is_signer=True, is_writable=False),
        AccountMeta(pubkey=payer, is_signer=True, is_writable=False),
        AccountMeta(pubkey=metadata_account, is_signer=False, is_writable=False),
        AccountMeta(pubkey=PublicKey(TOKEN_PROGRAM_ID), is_signer=False, is_writable=False),
        AccountMeta(pubkey=PublicKey(SYSTEM_PROGRAM_ID), is_signer=False, is_writable=False),
        AccountMeta(pubkey=PublicKey(SYSVAR_RENT_PUBKEY), is_signer=False, is_writable=False),
    ]
    return TransactionInstruction(
        keys=keys,
        program_id=METADATA_PROGRAM_ID,
        data=data,
    )


    # ///   0. `[writable]` New Metadata key (pda of ['metadata', program id, mint id])
    # ///   1. `[writable]` New Edition (pda of ['metadata', program id, mint id, 'edition'])
    # ///   2. `[writable]` Master Record Edition V2 (pda of ['metadata', program id, master metadata mint id, 'edition'])
    # ///   3. `[writable]` Mint of new token - THIS WILL TRANSFER AUTHORITY AWAY FROM THIS KEY
    # ///   4. `[writable]` Edition pda to mark creation - will be checked for pre-existence. (pda of ['metadata', program id, master metadata mint id, 'edition', edition_number])
    # ///   where edition_number is NOT the edition number you pass in args but actually edition_number = floor(edition/EDITION_MARKER_BIT_SIZE).
    # ///   5. `[signer]` Mint authority of new mint
    # ///   6. `[signer]` payer
    # ///   7. `[signer]` owner of token account containing master token (#8)
    # ///   8. `[]` token account containing token from master metadata mint
    # ///   9. `[]` Update authority info for new metadata
    # ///   10. `[]` Master record metadata account
    # ///   11. `[]` Token program
    # ///   12. `[]` System program
    # ///   13. `[]` Rent info

def mint_new_edition_from_master_edition_instruction(edition_number, master_mint, new_mint, update_authority,
                                                     mint_authority,new_mint_authority,
                                                     master_token_account_owner,
                                                     master_token_account,
                                                     payer):
    new_edition_account = get_edition(new_mint)
    new_metadata_account = get_metadata_account(new_mint)

    master_edition_account = get_edition(master_mint)
    master_metadata_account = get_metadata_account(master_mint)
    edition_pda = get_edition_number_pda(master_mint,edition_number)
    data = get_mint_new_edition_from_master_edition_instruction(edition_number)

    keys = [
        AccountMeta(pubkey=new_metadata_account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=new_edition_account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=master_edition_account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=new_mint, is_signer=False, is_writable=True),
        AccountMeta(pubkey=edition_pda, is_signer=False, is_writable=True),

        AccountMeta(pubkey=new_mint_authority, is_signer=True, is_writable=False),
        AccountMeta(pubkey=payer, is_signer=True, is_writable=False),

        AccountMeta(pubkey=master_token_account_owner, is_signer=True, is_writable=False),
        AccountMeta(pubkey=master_token_account, is_signer=False, is_writable=False),

        AccountMeta(pubkey=update_authority, is_signer=False, is_writable=False),

        AccountMeta(pubkey=master_metadata_account, is_signer=False, is_writable=False),
        AccountMeta(pubkey=PublicKey(TOKEN_PROGRAM_ID), is_signer=False, is_writable=False),
        AccountMeta(pubkey=PublicKey(SYSTEM_PROGRAM_ID), is_signer=False, is_writable=False),
        AccountMeta(pubkey=PublicKey(SYSVAR_RENT_PUBKEY), is_signer=False, is_writable=False),
    ]
    return TransactionInstruction(
        keys=keys,
        program_id=METADATA_PROGRAM_ID,
        data=data,
    )
