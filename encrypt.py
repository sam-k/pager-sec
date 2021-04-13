#!/usr/bin/env python3

from base64 import b16decode, b16encode

from Crypto.Cipher import ChaCha20_Poly1305
from Crypto.Random import get_random_bytes


def encrypt(key, plaintext, authdata):
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


def b16arduino(s):
    if len(s) % 2 != 0:
        print("Invalid base-16")
        return None

    b16arr = [f"0x{s[i:i+2]}" for i in range(0, len(s), 2)]
    return f"{{{', '.join(b16arr)}}}"


def main():
    # key = get_random_bytes(32)
    key = b16decode(b"12C000EF88068E0777118C20DEEB2702F22A06042E3534DBCD9CE1EAC9175DE9")
    plaintext = (
        b"PT IN 413 DOE, JANE 37F DILAUDID 0.5MG 1HR AGO STILL C/O PAIN, INCREASE DOSE?"
    )
    authdata = b""

    print(f"Key: {b16encode(key).decode()}")
    print(f"Msg: {plaintext.decode()}")
    print()

    print("Encrypting...")
    encrypted = encrypt(key, plaintext, authdata)
    print(f"Encrypted msg: {encrypted['ciphertext']}")
    print(f"Auth data: {encrypted['auth']}")
    print(f"IV: {encrypted['iv']}")
    print(f"Tag: {encrypted['tag']}")
    print()

    print("Decrypting...")
    decrypted = decrypt(key, *encrypted.values())
    if decrypted:
        print(f"Decrypted msg: {decrypted.decode()}")
    print()

    print("Arduino input:")
    print(f".key         = {b16arduino(b16encode(key).decode())},")
    print(f".ciphertext  = {b16arduino(encrypted['ciphertext'])},")
    print(f".authdata    = {b16arduino(encrypted['auth'])},")
    print(f".iv          = {b16arduino(encrypted['iv'])},")
    print(f".tag         = {b16arduino(encrypted['tag'])},")
    print(f".datasize    = {int(len(encrypted['ciphertext']) / 2)},")
    print(f".authsize    = {int(len(encrypted['auth']) / 2)},")
    print(f".ivsize      = {int(len(encrypted['iv']) / 2)},")
    print(f".tagsize     = {int(len(encrypted['tag']) / 2)}")

    return


if __name__ == "__main__":
    main()
