import hashlib
import hmac

def hmac_sha256(key: bytes, input_data: bytes) -> bytearray:
    '''
    Computes the HMAC-SHA-256 of the input data using the given key.
    
    :param key: The key to use for the HMAC, as bytes.
    :param input_data: The data to hash, as bytes.
    :return: The hexadecimal representation of the HMAC.
    '''
    return bytearray(hmac.new(key, input_data, hashlib.sha256).digest())

def hmac_sha224(key: bytes, input_data: bytes) -> bytearray:
    '''
    Computes the HMAC-SHA-224 of the input data using the given key.
    
    :param key: The key to use for the HMAC, as bytes.
    :param input_data: The data to hash, as bytes.
    :return: The hexadecimal representation of the HMAC.
    '''
    return bytearray(hmac.new(key, input_data, hashlib.sha224).digest())

# # Example usage
# if __name__ == '__main__':
#     # Input data and key must be in bytes
#     input_data = b'Hello, world!'
#     key = b'secret_key'

#     print('HMAC-SHA-256:', hmac_sha256(key, input_data))
#     print('HMAC-SHA-224:', hmac_sha224(key, input_data))
