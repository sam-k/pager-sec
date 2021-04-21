#include <ChaChaPoly.h>

// Adapted from https://platformio.org/lib/show/1168/Crypto

// Max sizes in bytes
#define MAX_PLAINTEXT_LEN 300
#define MAX_AUTHDATA_LEN 32
#define MAX_IV_LEN 16
#define MAX_TAG_LEN 16

// Pager-specific pre-shared key
const uint8_t KEY[32]  = {0x12, 0xC0, 0x00, 0xEF, 0x88, 0x06, 0x8E, 0x07,
                          0x77, 0x11, 0x8C, 0x20, 0xDE, 0xEB, 0x27, 0x02,
                          0xF2, 0x2A, 0x06, 0x04, 0x2E, 0x35, 0x34, 0xDB,
                          0xCD, 0x9C, 0xE1, 0xEA, 0xC9, 0x17, 0x5D, 0xE9};

// Struct for encryption info
struct MsgVector {
  uint8_t ciphertext[MAX_PLAINTEXT_LEN];
  uint8_t authdata[MAX_AUTHDATA_LEN];
  uint8_t iv[MAX_IV_LEN];
  uint8_t tag[MAX_TAG_LEN];
  size_t datasize;
  size_t authsize;
  size_t ivsize;
  size_t tagsize;
};

// ChaCha20-Poly1305 cipher
ChaChaPoly chachapoly;

// Incoming encrypted msg
MsgVector msgVector;

// Generic buffer
byte buffer[MAX_PLAINTEXT_LEN];

bool decrypt(ChaChaPoly *cipher, MsgVector *msg) {
  /*
   * Decrypts a ChaChaPoly message.
   * 
   * Args:
   *   cipher: ChaChaPoly cipher
   *   msg: MsgVector of encrypted msg and associated info
   * Returns:
   *   Was decryption successful?
   */

  size_t posn;
  memset(buffer, 0x00, sizeof(buffer));

  // Initialize cipher
  cipher->clear();
  if (!cipher->setKey(KEY, 32)) {
    Serial.println("Failed to set key");
    return false;
  }
  if (!cipher->setIV(msg->iv, msg->ivsize)) {
    Serial.println("Failed to set IV");
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
    Serial.println("Failed to authenticate tag");
    return false;
  }

  return true;
}

bool readMsgVectorInput(uint8_t *buf, size_t *bufSize, int len) {
  /*
   * Reads input for a msgVector field.
   * 
   * Args:
   *   buf: Input buffer to write into
   *   bufSize: Address of input buffer size to write into
   *   len: Max number of bytes to read
   * Returns:
   *   Was reading input successful?
   */

  while (!Serial.available()); // block

  int inputSize = readSerialHexUntil('\n', buf, len);
  if (inputSize < 0) {
    Serial.println("Invalid input\n");
    return false;
  }
  *bufSize = inputSize;
  printBuffer(buf, inputSize, 0);
  return true;
}

int readSerialHexUntil(char term, uint8_t *buf, int len) {
  /*
   * Reads a hex string into buffer from Serial.
   * 
   * Args:
   *   delim: Terminating character of hex string
   *   buf: Buffer to read into
   *   len: Max number of bytes to read
   * Returns:
   *   Number of bytes read, or -1 if invalid input
   */

  int i;

  for (i = 0; i < len; i++) {
    int b, h;
    unsigned long hex;

    // 1st hex digit of byte
    while (!Serial.available()); // block
    b = Serial.read();
    if (b < 0 || b == (int)term) { break; }
    // Invalid 1st digit; destroy rest of input
    if ((h = htoi(b)) < 0) {
      while (b != (int)term) {
        b = Serial.read();
      }
      i = -1;
      break;
    }
    hex = h * 16L;

    // 2nd hex digit of byte
    while (!Serial.available()); // block
    b = Serial.read();
    // Invalid byte or invalid 2nd digit; destroy rest of input
    if (b < 0 || b == (int)term || (h = htoi(b)) < 0) {
      while (b >= 0 && b != (int)term) {
        b = Serial.read();
      }
      i = -1;
      break;
    }
    hex += h;

    buf[i] = hex;
  }

  destroySerialBuffer();
  return i;
}

void printBuffer(uint8_t *buf, int len, char delim) {
  /*
   * Prints buffer as hex.
   * 
   * Args:
   *   buf: Buffer to print
   *   len: Number of bytes to print
   *   delim: Delimiter between bytes
   */

  for (int i = 0; i < len; i++) {
    if (buf[i] < 0x10) {
      Serial.print('0');
    }
    Serial.print(buf[i], HEX);
    if (delim && i < len - 1) {
      Serial.print(delim);
    }
  }
  Serial.println();
}

void destroySerialBuffer() {
  /*
   * Destroys rest of input buffer.
   */

  while (Serial.available()) {
    Serial.read();
  }
}

int htoi(int ch) {
  /*
   * For a hex digit, converts ASCII representation to (decimal) int.
   * e.g., htoi('A') == 11
   * 
   * Args:
   *   ch: Hex digit as ASCII
   * Returns:
   *   Hex digit as int, or -1 if invalid hex
   */

  if (ch >= '0' && ch <= '9') {
    return ch - '0';
  }
  if (ch >= 'A' && ch <= 'F') {
    return ch - 'A' + 10;
  }
  if (ch >= 'a' && ch <= 'f') {
    return ch - 'a' + 10;
  }
  return -1;
}

void setup() {
  /*
   * Sets up sketch.
   */

  Serial.begin(9600);
  Serial.println("Starting pager...\n");
}

void loop() {
  /*
   * Loops sketch.
   */

  Serial.println(">>> Incoming encrypted message...");

  // Input: encrypted message
  Serial.print("Enter msg: ");
  if (!readMsgVectorInput(msgVector.ciphertext, &msgVector.datasize, MAX_PLAINTEXT_LEN)) {
    return;
  }

  // Input: additional data
  Serial.print("Enter AD: ");
  if (!readMsgVectorInput(msgVector.authdata, &msgVector.authsize, MAX_AUTHDATA_LEN)) {
    return;
  }

  // Input: initialization vector
  Serial.print("Enter IV: ");
  if (!readMsgVectorInput(msgVector.iv, &msgVector.ivsize, MAX_IV_LEN)) {
    return;
  }

  // Input: tag
  Serial.print("Enter tag: ");
  if (!readMsgVectorInput(msgVector.tag, &msgVector.tagsize, MAX_TAG_LEN)) {
    return;
  }

  // Decrypt message
  Serial.println("<<< Decrypting message...");
  decrypt(&chachapoly, &msgVector);

  Serial.println();
  destroySerialBuffer();
}
