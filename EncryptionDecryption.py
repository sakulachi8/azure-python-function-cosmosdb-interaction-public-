
from cryptography.fernet import Fernet

def generate_new_key():
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

def load_key():
    """
    Load the previously generated key
    """
    return open("secret.key", "rb").read()


def encrypt_message(message):
    """
    Encrypts a message
    """
    try:
        key = load_key()
        if not key:
            generate_new_key()
            key = load_key()

        encoded_message = str(message).encode()
        f = Fernet(key)
        encrypted_message = f.encrypt(encoded_message)
    except Exception as ex:
        print("encrypt_message Exception" + str(ex))


    return encrypted_message.decode()



def decrypt_message(encrypted_message):
    """
    Decrypts an encrypted message
    """
    try:
        key = load_key()
        f = Fernet(key)
        encrypted_message = str.encode(encrypted_message)
        decrypted_message = f.decrypt(encrypted_message)
    except Exception as ex:
        print("decrypt_message Exception" + str(ex))
    return decrypted_message.decode()