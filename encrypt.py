#!/usr/bin/env python3

from base64 import b16decode, b16encode

from Crypto.Cipher import ChaCha20_Poly1305
from Crypto.Random import get_random_bytes


def encrypt(key, plaintext, authdata):
    """
    Encrypts a message using ChaCha20-Poly1305.

    Args:
        key: 256-bit shared key
        plaintext: Plaintext to be encrypted, up to 300 chars
        authdata: Additional data for authentication
    Returns:
        Dict of ciphertext and associated encryption info
    """

    cipher = ChaCha20_Poly1305.new(key=key)
    cipher.update(authdata)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    k = ("ciphertext", "auth", "iv", "tag")
    v = (
        b16encode(x).decode("utf-8") for x in (ciphertext, authdata, cipher.nonce, tag)
    )
    result = dict(zip(k, v))
    return result


def decrypt(key, ciphertext, authdata, iv, tag):
    """
    Decrypts a message using ChaCha20-Poly1305.

    Args:
        key: 256-bit shared key
        ciphertext: Ciphertext to be decrypted
        authdata: Additional data for authentication
        iv: 96-bit initialization vector (nonce)
        tag: 128-bit authentication tag
    Returns:
        Plaintext if decryption succeeded, else None
    """

    k = ("ciphertext", "auth", "iv", "tag")
    v = (b16decode(x) for x in (ciphertext, authdata, iv, tag))
    result = dict(zip(k, v))

    try:
        cipher = ChaCha20_Poly1305.new(key=key, nonce=result["iv"])
        cipher.update(result["auth"])
        plaintext = cipher.decrypt_and_verify(result["ciphertext"], result["tag"])
        return plaintext
    except:
        print("Decryption failed")
        return None


def main():
    """
    Main.
    """

    # Pager-specific pre-shared key
    # key = get_random_bytes(32)
    key = b16decode(b"12C000EF88068E0777118C20DEEB2702F22A06042E3534DBCD9CE1EAC9175DE9")
    plaintext = (
        b"PT IN 413 DOE, JANE 37F DILAUDID 0.5MG 1HR AGO STILL C/O PAIN, INCREASE DOSE?"
    )
    authdata = b"08.103.C"

    print(f"Key: {b16encode(key).decode()}")
    print(f"Msg: {plaintext.decode()}")
    print()

    print("Encrypting...")
    encrypted = encrypt(key, plaintext, authdata)
    print(f"Msg: {encrypted['ciphertext']}")
    print(f"AD: {encrypted['auth']}")
    print(f"IV: {encrypted['iv']}")
    print(f"Tag: {encrypted['tag']}")
    print()

    # print("Decrypting...")
    # decrypted = decrypt(key, *encrypted.values())
    # if decrypted:
    #     print(f"Decrypted msg: {decrypted.decode()}")
    # print()

    return


if __name__ == "__main__":
    main()
