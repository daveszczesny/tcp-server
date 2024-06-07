import socket
import argparse
import json

def main(bot_name: str):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 9999))

    bot_name = bot_name
    client.send(bot_name.encode('utf-8'))


    try:
        while True:
            server_response = client.recv(1024).decode('utf-8')

            if not server_response:
                print('Connection with server lost')
                break

            print(server_response)
            if server_response.__contains__("Action required"):
                response = input()
                client.send(response.encode('utf-8'))


    except Exception as ex:
        print(ex)
    finally:
        client.close()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script desc')
    parser.add_argument('-name', type=str, help='Name Argument')

    args = parser.parse_args()
    if args.name:
        main(args.name)
    else:
        print("No name provided")
        exit(-1)