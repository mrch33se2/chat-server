import tkinter as tk
import Client

Client.MASK = "ADMIN"
Client.IP = "localhost"

if __name__ == "__main__":
    root = tk.Tk()
    app = Client.ChatClient(root)
    app.run()