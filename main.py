from customtkinter import CTk, CTkLabel, CTkEntry, CTkButton, CTkOptionMenu, CTkToplevel, StringVar
from os.path import isfile, join
from sys import path
from re import match
from json import load as json_decode
from json import dump as json_encode
from json.decoder import JSONDecodeError
import socket

# That way ezwol.json will be saved in same directory as main.py
PATH_TO_SAVED_DEVICES = join(path[0], 'ezwol.json')
PORT = 9


class Message(CTkToplevel):
    def __init__(self, message: str, title: str = "Error"):
        super().__init__()

        # Handing old customtkinter bug with CTkToplevel on Windows. I want to believe it is already fixed
        self.after(250, self.lift)

        self.title(title)
        CTkLabel(self, text=message).pack(padx=20, pady=(20, 10))
        CTkButton(self, text="Exit", command=lambda: self.destroy()).pack(padx=20, pady=(10, 20))


class App(CTk):
    def __init__(self):
        super().__init__()
        self.title("Ez WoL")
        self.storage = []

        # ----- LEFT -----
        select_device = CTkLabel(self, text="Select device")
        select_device.grid(row=0, column=0, padx=20, pady=(5, 2), sticky="news")

        self.device_menu = CTkOptionMenu(self, variable=StringVar(value="Empty"))
        self.device_menu.configure(state="disabled")
        self.device_menu.grid(row=1, column=0, padx=20, pady=(5, 2), sticky="news")

        delete_device = CTkButton(self, text="Delete device", command=lambda: self.delete_device())
        delete_device.grid(row=2, column=0, padx=20, pady=(5, 2), sticky="news")

        view_mac = CTkButton(self, text="View MAC", command=lambda: self.view_mac())
        view_mac.grid(row=3, column=0, padx=20, pady=(5, 2), sticky="news")

        # ----- RIGHT -----
        save_device = CTkLabel(self, text="Save device")
        save_device.grid(row=0, column=1, padx=20, pady=(5, 2), sticky="new")

        self.device_name = CTkEntry(self, placeholder_text="Device name")
        self.device_name.grid(row=1, column=1, padx=20, pady=(5, 2), sticky="news")

        self.mac_entry = CTkEntry(self, placeholder_text="MAC address")
        self.mac_entry.grid(row=2, column=1, padx=20, pady=(5, 2), sticky="news")

        save = CTkButton(self, text="Save", command=lambda: self.save_device(self.device_name.get(),
                                                                             self.mac_entry.get()))
        save.grid(row=3, column=1, padx=20, pady=(5, 2), sticky="news")

        wake = CTkButton(self, text="Wake", command=lambda: self.wake())
        wake.grid(row=4, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="news")

        self.load_devices()

    def save_device(self, device, mac):
        if len(device) == 0:
            Message(message="Device name couldn't be empty.")
            print("Device name couldn't be empty.")
            return

        if device in [i["Device Name"] for i in self.storage]:
            Message(message="That device already exists in storage.")
            print("That device already exists in storage.")
            return

        if not match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()):
            Message(message="MAC address is wrong.")
            print("MAC address is wrong.")
            return
        else:
            self.storage.append({"Device Name": device, "MAC": mac})
            with open(PATH_TO_SAVED_DEVICES, 'w', encoding='utf-8') as file:
                json_encode(self.storage, file)
            self.load_devices()

    def load_devices(self):
        if isfile(PATH_TO_SAVED_DEVICES):
            try:
                with open(PATH_TO_SAVED_DEVICES, 'r', encoding='utf-8') as file1:
                    self.storage = json_decode(file1)
            except (JSONDecodeError, UnicodeDecodeError) as e:
                Message("Saved devices file is corrupted and will be cleared.")
                print("Saved devices file is corrupted and will be cleared.", e)
                with open(PATH_TO_SAVED_DEVICES, 'w', encoding='utf-8') as file_:
                    json_encode(self.storage, file_)

            if len(self.storage) == 0:
                print("Storage is empty.")
                self.device_menu.set("Empty")
                self.device_menu.configure(state="disabled")
                return

            values = [i["Device Name"] for i in self.storage]
            self.device_menu.configure(state="normal")
            self.device_menu.configure(values=values)
            self.device_menu.set(values[0])
        else:
            with open(PATH_TO_SAVED_DEVICES, 'w', encoding='utf-8') as file:
                json_encode(self.storage, file)

    def delete_device(self):
        if self.device_menu.cget("state") == "disabled":
            Message("Device is not selected.")
            print("Device is not selected.")
            return

        device = self.device_menu.get()
        for i in range(0, len(self.storage)):
            if self.storage[i]['Device Name'] == device:
                del self.storage[i]
                break
        with open(PATH_TO_SAVED_DEVICES, 'w', encoding='utf-8') as file:
            json_encode(self.storage, file)
        self.load_devices()

    def wake(self):
        if self.device_menu.cget("state") == "disabled":
            Message("Device is not selected.")
            print("Device is not selected.")
            return

        device = self.device_menu.get()

        mac = [i["MAC"] for i in self.storage if i["Device Name"] == device][0]

        # Removing : or - from MAC
        mac_address = mac.replace(mac[2], '')
        # Creating magic packet
        payload = bytes.fromhex("FFFFFFFFFFFF" + mac_address * 16)
        # Creating UDP socket for sending magic packet
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Obtaining ability to send broadcast packets
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Sending payload
        sock.sendto(payload, ("255.255.255.255", PORT))

    def view_mac(self):
        if self.device_menu.cget("state") == "disabled":
            Message("Device is not selected.")
            print("Device is not selected.")
            return

        device = self.device_menu.get()
        mac = [i["MAC"] for i in self.storage if i["Device Name"] == device][0]
        Message(f"MAC: {mac}", title=device)


if __name__ == "__main__":
    App().mainloop()
