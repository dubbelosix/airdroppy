from borsh_construct import CStruct, Enum, String, U8, U16, U64, Vec, Option, Bool

# Constructs defined using the structs from spl-token-metadata from rustdocs
# https://docs.rs/spl-token-metadata/0.0.1/spl_token_metadata/instruction/index.html

InstructionType = Enum (
    "CreateMetadataAccount",
    "UpdateMetadataAccount",
    "DeprecatedCreateMasterEdition",
    "DeprecatedMintNewEditionFromMasterEditionViaPrintingToken",
    "UpdatePrimarySaleHappenedViaToken",
    "DeprecatedSetReservationList",
    "DeprecatedCreateReservationList",
    "SignMetadata",
    "DeprecatedMintPrintingTokensViaToken",
    "DeprecatedMintPrintingTokens",
    "CreateMasterEdition",
    "MintNewEditionFromMasterEditionViaToken",
    "ConvertMasterEditionV1ToV2",
    "MintNewEditionFromMasterEditionViaVaultProxy",
    "PuffMetadata",
    "UpdateMetadataAccountV2",
    "CreateMetadataAccountV2",
    "CreateMasterEditionV3",
    "VerifyCollection",
    "Utilize",
    "ApproveUseAuthority",
    "RevokeUseAuthority",
    "UnverifyCollection",
    "ApproveCollectionAuthority",
    "RevokeCollectionAuthority",
    enum_name="InstructionType"
)

PubKey = CStruct(
    "pub_key" / U8[32]
)

Creator = CStruct(
    "address" / PubKey,
    "verified" / Bool,
    "share" / U8
)

Data = CStruct(
    "name" / String,
    "symbol" / String,
    "uri" / String,
    "seller_fee_basis_points" / U16,
    "creators" / Option(Vec(Creator))
)

CreateMetadataAccountArgs = CStruct(
    "data" / Data,
    "is_mutable" / Bool,
)

CreateInstructionLayout = CStruct(
    "instruction_type" / InstructionType,
    "args" / CreateMetadataAccountArgs,
)

UpdateMetadataAccountArgs = CStruct(
    "data" / Option(Data),
    "update_authority" / Option(PubKey),
    "primary_sale_happened" / Option(Bool),
)

UpdateInstructionLayout = CStruct(
    "instruction_type" / InstructionType,
    "args" / UpdateMetadataAccountArgs,
)


CreateMasterEditionArgs = CStruct (
    "max_supply" / Option(U64)
)

CreateMasterEditionLayout = CStruct (
    "instruction_type" / InstructionType,
    "args" / CreateMasterEditionArgs,
)

MintNewEditionFromMasterEditionViaTokenArgs = CStruct (
    "edition" / U64
)

MintNewEditionFromMasterEditionViaTokenLayout = CStruct (
    "instruction_type" / InstructionType,
    "args" / MintNewEditionFromMasterEditionViaTokenArgs,
)

def get_create_metadata_instruction(name, symbol, uri, fee, is_mutable=False, creators=None):
    return CreateInstructionLayout.build(
        {
            "instruction_type": InstructionType.enum.CreateMetadataAccount(),
            "args": {
                "data":
                    {
                        "name": name,
                        "symbol": symbol,
                        "uri": uri,
                        "seller_fee_basis_points": fee,
                        "creators": creators
                    },
                "is_mutable": is_mutable
            }
        }
    )


def get_update_metadata_instruction(name, symbol, uri, fee, update_authority, primary_sale_happened=None, creators=None):
    return CreateMasterEditionLayout.build({
        "instruction_type": InstructionType.enum.UpdateMetadataAccount(),
        "args": {
            "data":
                {
                    "name": name,
                    "symbol": symbol,
                    "uri": uri,
                    "seller_fee_basis_points": fee,
                    "creators": creators
                },
            "update_authority": {"pub_key": update_authority},
            "primary_sale_happened": primary_sale_happened,
        }
    })

def get_create_master_edition_instruction(max_supply):
    return CreateMasterEditionLayout.build({
        "instruction_type": InstructionType.enum.CreateMasterEditionV3(),
        "args":
            {"max_supply":max_supply}
    })

def get_mint_new_edition_from_master_edition_instruction(edition_num):
    return MintNewEditionFromMasterEditionViaTokenLayout.build({
        "instruction_type": InstructionType.enum.MintNewEditionFromMasterEditionViaToken(),
        "args":
            {"edition": edition_num}
    })
