import serial
import time


class Lfc(object):
    WAIT = 0.07         # Transmission interval, s

    # Special characters
    STX = chr(0x02)     # Start transmission
    ETX = chr(0x03)     # End transmission
    ENQ = chr(0x05)     # Enquiry (???)
    ACK = chr(0x06)     # Acknowledge
    NAK = chr(0x15)     # Not-acknowledge

    @staticmethod
    def id_to_str(id):
        if isinstance(id, int):
            id = str(id).zfill(2)
        return id

    def __init__(self,
                 port,
                 id='02',   # Factory default
                 baud=38400,
                 bits=7,
                 parity=serial.PARITY_ODD,
                 stopbits=serial.STOPBITS_ONE,
                 timeout=1,
                 debug=False):
        self.id = self.id_to_str(id)
        self.debug = debug
        self.ser = serial.Serial(port, baud, bits, parity, stopbits, timeout)

    def check_chr(self, msg):
        ''' Generate check character from message
            Expects to have STX and ETX already included, without BCC '''
        sum = 0
        for c in msg[msg.find(self.STX)+1:]:
            sum += ord(c)
        return chr(sum % 128)

    def send(self, cmd, read=False):
        time.sleep(self.WAIT)
        msg = '@' + self.id + self.STX + cmd + self.ETX
        bcc = self.check_chr(msg)
        msg += bcc

        # Handle cases where bcc collides with a special character
        if bcc == '@':
            msg += self.ETX * 3
        elif bcc == '*':
            msg += self.ETX * 9

        # Send msg
        if self.debug:
            print('> ' + msg)
        written = self.ser.write(msg.encode('ascii'))

        # Read msg if requested
        if read:
            ret = False
            while ret is False:
                ret = self.read()
        else:
            ret = bool(written)

        return ret

    def read(self):
        # Read response
        chars = []
        char = None
        while char not in (self.ETX, self.NAK):
            char = self.ser.read().decode()
            chars.append(char)
        if char == self.NAK:
            # Failed
            return False

        # char == self.ETX, probable success
        msg = ''.join(chars)

        # Verify checksum (next character)
        bcc = self.ser.read().decode()
        if self.debug:
            print('< ' + msg + bcc)
        if bcc != self.check_chr(msg):
            print("Warning: Received bad checksum")
            return False

        # Extract return value
        msg = msg[msg.find(self.STX)+1 : msg.find(self.ETX)]
        return msg

    def close(self):
        return self.ser.close()

    def get_serial_number(self):
        return self.send('RSN', True)

    def get_id(self):
        id = self.send('*)&', True)

        # Apparently replies 'OK' to the first get_id after a set_id
        if id == 'OK':
            id = self.send('*)&', True)

        # If not convertable to an int, consider it a failure
        try:
            id = int(id)
        except:
            print("LFT: ERROR - Couldn't understand id " + str(id))
            id = False
        return id

    def set_id(self, new_id):
        # Convert int to string
        new_id = self.id_to_str(new_id)
        # Set ID
        ret = self.send("'*$" + new_id)
        # Save new id if successful
        if ret:
            self.id = new_id
        return ret


if __name__ == '__main__':

     lfc = Lfc('COM8', debug=False)
     id = lfc.get_id()
     print('ID is: ', id)
     #ret = lfc.set_id(id + 1)
     #print('Set new id? ', ret)
     #print('new id: ', lfc.get_id())
     #ret = lfc.set_id(id)
     #print('Set old id? ', ret)
     #print('new id: ', lfc.get_id())
     lfc.close()
