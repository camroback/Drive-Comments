import threading
import queue
import io
import pynmea2
import serial
import tkinter as tk
import os
import json
import csv

comments = []  

queue = queue.Queue(maxsize=1)

def gps_worker():
    ser = serial.Serial('COM5', 4800, timeout=1.0)
    sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

    with open('/Users/camer/OneDrive/Documents/Van/Comments/gps_data_2-2-24_BLUEROUTE_AUTONOMY.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["time", "latitude", "longitude"])
        while True:
            try:
                line = sio.readline()
                msg = pynmea2.parse(line)

                if(msg.sentence_type=='GGA'):
                    if queue.full():
                        queue.get_nowait()
                    queue.put(msg, block=False)
                    csv_writer.writerow([msg.timestamp, msg.latitude, msg.longitude])
                    csvfile.flush()
                    print(msg)
            except serial.SerialException as e:
                print('Device error: {}'.format(e))
                break
            except pynmea2.ParseError as e:
                print('Parse error: {}'.format(e))
                continue
            if(quit_event.is_set()):
                return

quit_event = threading.Event()
gpsthread = threading.Thread(target=gps_worker, daemon=True)
gpsthread.start()

def save_comment_and_close(comment_text, comment_window, gps_data, event=None):
    filename = "/Users/camer/OneDrive/Documents/Van/Comments/VanDrive_Comments_2-2-24_BLUEROUTE_AUTONOMY.json"

    new_comment = {"problem": comment_text.get("1.0", "end-1c")}
    comments.append({**gps_data, **new_comment})

    with open(filename, "w") as f:
        json.dump({"comments": comments}, f, indent=4)

    comment_window.destroy()

def open_comment_box():
    msg = queue.get()
    if msg.sentence_type == 'GGA':
        gps_data = {
            "talker": msg.talker,
            "sentence_type": msg.sentence_type,
            "data": [
                str(msg.timestamp),
                msg.lat,
                msg.lat_dir,
                msg.lon,
                msg.lon_dir,
                str(msg.gps_qual),
                str(msg.num_sats),
                str(msg.horizontal_dil),
                str(msg.altitude),
                msg.altitude_units,
                str(msg.geo_sep),
                msg.geo_sep_units,
                msg.age_gps_data,
                msg.ref_station_id
            ],
        }
        comment_window = tk.Toplevel(window)
        comment_screen_width = comment_window.winfo_screenwidth()
        comment_screen_height = comment_window.winfo_screenheight()
        comment_window_width = int(comment_screen_width * 0.25)
        comment_window_height = int(comment_screen_height * 0.25)
        x_comment = int(comment_screen_width * 0.7)
        y_comment = int(comment_screen_height * 0.2)
        comment_window.geometry("{}x{}+{}+{}".format(comment_window_width, comment_window_height, x_comment, y_comment))

        comment_label = tk.Label(comment_window, text="Write your comment below:")
        comment_label.pack()

        comment_text = tk.Text(comment_window, height=comment_window_height, width=comment_window_width)
        comment_text.pack()

        comment_text.bind("<Return>", lambda event: save_comment_and_close(comment_text, comment_window, gps_data, event))

        comment_text.focus_set()

def on_closing():
    quit_event.set()
    window.destroy()

window = tk.Tk()
window.title("Comment Box")
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
window_width = int(screen_width * 0.25)
window_height = int(screen_height * 0.25)
x = int(screen_width * 0.7)
y = int(screen_height * 0.2)
window.geometry("{}x{}+{}+{}".format(window_width, window_height, x, y))

open_comment_box_button = tk.Button(window, text="Open Comment Box", command=open_comment_box, width=window_width, height=window_height, font=("Arial", 24), bg="green")
open_comment_box_button.pack()

window.protocol("WM_DELETE_WINDOW", lambda: on_closing())

window.mainloop()