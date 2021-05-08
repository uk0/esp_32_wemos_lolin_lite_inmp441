import asyncio
import binascii
import os
import random
import time
import wave

import websockets
from websockets.exceptions import ConnectionClosedError

i2s_sample_rate = 16000
i2s_sample_bits = 32
i2s_ch = 1


def gen_wav_header(samples):
    rate = i2s_sample_rate
    channels = 1
    bits = i2s_sample_bits
    data_size = len(samples) * channels * bits // 8
    o = bytes("RIFF", 'ascii')  # (4byte) Marks file as RIFF
    o += (data_size + 36).to_bytes(4, 'little')  # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE", 'ascii')  # (4byte) File type
    o += bytes("fmt ", 'ascii')  # (4byte) Format Chunk Marker
    o += (16).to_bytes(4, 'little')  # (4byte) Length of above format data
    o += (1).to_bytes(2, 'little')  # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2, 'little')  # (2byte)
    o += (rate).to_bytes(4, 'little')  # (4byte)
    o += (rate * channels * bits // 8).to_bytes(4, 'little')  # (4byte)
    o += (channels * bits // 8).to_bytes(2, 'little')  # (2byte)
    o += (bits).to_bytes(2, 'little')  # (2byte)
    o += bytes("data", 'ascii')  # (4byte) Data Chunk Marker
    o += (data_size).to_bytes(4, 'little')  # (4byte) Data size in bytes
    return o


index = 0
data_all = []


def get_file_name():
    file_name = ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba', 12))
    return "wav_dir\\{}_{}".format(file_name, time.strftime('%Y/%m/%d %H:%M:%S')).replace(" ", "_").replace("-",
                                                                                                            "_").replace(
        "/", "_").replace(":", "_")


index = 0


def _write_wav(data):
    global index
    if index == 0:
        try:
            os.remove('temp.bin')
        except FileNotFoundError:
            print("delete successfully")

    with open('temp.bin', mode='ab') as filename:
        filename.write(data)
        filename.close()
        index = index + 1
    if index == 128:
        f_name = get_file_name()
        wavfile = wave.open(f_name + ".wav", 'wb')
        wavfile.setnchannels(1)
        wavfile.setframerate(i2s_sample_rate)
        wavfile.setsampwidth(2)
        wavfile.setcomptype(compname='NONE', comptype='NONE')
        wavfile.writeframes(bytearray(open('temp.bin', "rb").read()))
        wavfile.close()
        os.remove('temp.bin')
        index = 0  # index rev 0
        print("file name = ", f_name)


def hex_to_char(data):
    output = binascii.unhexlify(data)
    return output


def char_to_hex(data):
    output = binascii.hexlify(data)
    return output


async def ws_rec(websocket, path):
    if path == "/":
        flag = True
        global data
        while True:
            try:
                data = await websocket.recv()
            except ConnectionClosedError:
                print("ConnectionClosedError pls wait 1s")
                time.sleep(1)
                continue
            if flag:
                _write_wav(data)
                print("recv data len = " + str(len(data)))


start_server = websockets.serve(ws_rec, "0.0.0.0", 10086)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
