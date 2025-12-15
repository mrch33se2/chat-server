import socket
import threading
import tkinter as tk
from tkinter import scrolledtext

IP = "192.168.39.39"
PORT = 5001
MASK = "Geddings" #input("What Is Your Name: ")

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Test")
        self.root.geometry("600x500")
        self.sock = None
        self.connected = False
        self.setupUi()

    def setupUi(self):
        # Chat display (read-only, scrollable)
        self.chatDisplay = scrolledtext.ScrolledText(
            self.root, height=20, width=70, state=tk.DISABLED, wrap=tk.WORD
        )
        self.chatDisplay.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Input frame
        inputFrame = tk.Frame(self.root)
        inputFrame.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.messageEntry = tk.Entry(inputFrame, font=("Arial", 12))
        self.messageEntry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.messageEntry.bind("<Return>", self.sendMessage)
        sendBtn = tk.Button(inputFrame, text="Send", command=self.sendMessage, bg="#4CAF50", fg="black")
        sendBtn.pack(side=tk.RIGHT, padx=(5, 0))
        quitBtn = tk.Button(self.root, text="QUIT", command=self.quit_app, bg="#f44336", fg="black")
        quitBtn.pack(pady=5)

    def addMessage(self, sender, message):
        # Add message to chat display
        self.chatDisplay.config(state=tk.NORMAL)
        self.chatDisplay.insert(tk.END, f"{sender}: {message}\n")
        self.chatDisplay.see(tk.END)
        self.chatDisplay.config(state=tk.DISABLED)

    def connect(self):
        global MASK
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((IP, PORT))
            self.connected = True

            # Handle mask exchange
            entry = self.sock.recv(8)
            if entry == b"GETMASK":
                self.sock.send(MASK.encode())
                self.addMessage("System", "Sent Mask")
            else:
                MASK = entry

            # Start receiver thread first
            self.receiverThread = threading.Thread(target=self.receiveMessages, daemon=True)
            self.receiverThread.start()

            # Then send MSGS to get chat history
            self.sock.send(b"MSGS")

            self.addMessage("System", "Connected to server! Fetching chat history...")

        except Exception as e:
            self.addMessage("Error", f"Connection failed: {e}")

    def receiveMessages(self):
        # Receive messages from server in background thread
        buffer = b''
        while self.connected:
            try:
                receivedBinary = self.sock.recv(1024)
                if not receivedBinary:
                    self.addMessage("System", "Server disconnected")
                    self.connected = False
                    break

                buffer += receivedBinary

                # Parse ID and message (your format: ID\x00message\x01)
                while b'\x00' in buffer:
                    nullIdx = buffer.find(b'\x00')

                    idPart = buffer[:nullIdx]
                    messagePart = buffer[nullIdx + 1:]
                    endIdx = messagePart.find(b'\x01')

                    messagePart = messagePart[:endIdx]
                    endIdx = buffer.find(b'\x01')
                    buffer = buffer[endIdx + 1:]

                    # Special case: END means chat history is done
                    if idPart != b"END":
                        self.addMessage(idPart.decode('utf-8', errors='replace'), messagePart.decode('utf-8', errors='replace'))

            except OSError:
                break
            except Exception as e:
                self.addMessage("Error", f"Receive error: {e}")
                break
        self.connected = False

    def sendMessage(self, event=None):
        message = self.messageEntry.get().strip()
        if message and self.connected:
            try:
                self.sock.send(message.encode())
                self.messageEntry.delete(0, tk.END)
            except Exception:
                self.addMessage("Error", "Send failed")
        elif not self.connected:
            # Auto-connect on first send if not connected
            self.connect()

    def quit_app(self):
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.root.quit()

    def run(self):
        # Connect automatically on start
        self.connect()
        self.root.mainloop()


# Create and run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    app.run()
