#include <ChaChaPoly.h>

// Adapted from https://platformio.org/lib/show/1168/Crypto

#define MAX_PLAINTEXT_LEN 300

// Pager-specific pre-shared key
const uint8_t KEY[32]  = {0x12, 0xC0, 0x00, 0xEF, 0x88, 0x06, 0x8E, 0x07,
                          0x77, 0x11, 0x8C, 0x20, 0xDE, 0xEB, 0x27, 0x02,
                          0xF2, 0x2A, 0x06, 0x04, 0x2E, 0x35, 0x34, 0xDB,
                          0xCD, 0x9C, 0xE1, 0xEA, 0xC9, 0x17, 0x5D, 0xE9};

// Struct for encryption info
struct MsgVector {
  uint8_t ciphertext[MAX_PLAINTEXT_LEN];
  uint8_t authdata[16];
  uint8_t iv[16];
  uint8_t tag[16];
  size_t datasize;
  size_t authsize;
  size_t ivsize;
  size_t tagsize;
};

// Incoming encrypted msg, from encrypt.py
static MsgVector const encryptedMsg PROGMEM = {
  .ciphertext  = {0x0E, 0xE7, 0x64, 0x21, 0x90, 0x49, 0x04, 0x07, 0xB8, 0x21, 0x48, 0x9B, 0x34, 0x38, 0x86, 0x06, 0x9D, 0x51, 0xA6, 0xD0, 0xCF, 0x90, 0x0A, 0x66, 0x5D, 0x32, 0xF8, 0x4F, 0x44, 0xAD, 0xF0, 0x96, 0x16, 0xA9, 0xE3, 0x98, 0xA7, 0x62, 0x4A, 0x71, 0x03, 0xD9, 0xBE, 0x3D, 0x2F, 0x12, 0xD4, 0xCA, 0x13, 0xC6, 0x76, 0xE7, 0xAA, 0xC0, 0xF5, 0x01, 0xC9, 0x5F, 0x40, 0x10, 0x54, 0x14, 0x6B, 0x4C, 0x15, 0xA6, 0xE9, 0x9C, 0x4F, 0xCE, 0xA8, 0x90, 0x6E, 0xEC, 0x0E, 0x8F, 0xEB},
  .authdata    = {},
  .iv          = {0xF8, 0x63, 0x0F, 0xAA, 0xA6, 0x3D, 0xBD, 0x61, 0x21, 0xEC, 0x9B, 0xA3},
  .tag         = {0x2E, 0xF3, 0x88, 0x0B, 0xA6, 0x6C, 0x5D, 0x85, 0x82, 0xA1, 0x4C, 0x5C, 0x64, 0x0A, 0xF5, 0x62},
  .datasize    = 77,
  .authsize    = 0,
  .ivsize      = 12,
  .tagsize     = 16
};

ChaChaPoly chachapoly;

MsgVector msgVector;
byte buffer[MAX_PLAINTEXT_LEN];

bool decrypt(ChaChaPoly *cipher, const struct MsgVector *msg) {
  /*
   * Decrypt a ChaChaPoly message.
   * 
   * Args:
   *   cipher: ChaChaPoly cipher
   *   msg: MsgVector of encrypted msg and associated info
   * Returns:
   *   Did decryption  succeed?
   */
 
  size_t posn;
  memset(buffer, 0x00, sizeof(buffer));

  // Initialize cipher
  cipher->clear();
  if (!cipher->setKey(KEY, 32)) {
    Serial.println("setKey Failed");
    return false;
  }
  if (!cipher->setIV(msg->iv, msg->ivsize)) {
    Serial.println("setIV Failed");
    return false;
  }

  // Decrypt data
  cipher->addAuthData(msg->authdata, msg->authsize);
  cipher->decrypt(buffer, msg->ciphertext, msg->datasize);

  // Print decrypted msg
  if (cipher->checkTag(msg->tag, msg->tagsize)) {
    for (posn = 0; posn < msg->datasize; posn++) {
      Serial.print((char)buffer[posn]);
    }
    Serial.println();
  } else {
    Serial.println("checkTag Failed");
    return false;
  }

  return true;
}

void decryptCipher(ChaChaPoly *cipher, const struct MsgVector *msg) {
  /*
   * Wrapper for decrypt.
   * 
   * Args:
   *   cipher: ChaChaPoly cipher
   *   msg: MsgVector of encrypted msg and associated info
   */
 
  // Fetch from PROGMEM
  memcpy_P(&msgVector, msg, sizeof(MsgVector));
  msg = &msgVector;

  if (decrypt(cipher, msg)) {
    Serial.println("Decryption succeeded");
  } else {
    Serial.println("Decryption failed");
  }
}

void setup() {
  /*
   * Set up sketch.
   */
 
  // Set up serial connection
  Serial.begin(9600);

  Serial.println("Incoming Encrypted Message");

  // Decrypt msg
  decryptCipher(&chachapoly, &encryptedMsg);
  Serial.println();
}

void loop() {
  /*
   * Loop sketch.
   */
 }
 
