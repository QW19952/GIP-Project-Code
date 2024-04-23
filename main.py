import time
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import socket
import json
import threading
import csv
from datetime import datetime

# --------------------------------Sever Setup-----------------------------------------
serverAddress = ('192.168.137.128', 2222)
bufferSize = 1048576
UDPClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Declare global variables
secondary_window = None
fig, ax = None, None
canvas = None
toolbar = None
lines = None

window_is_open = False

root_state = False

command = 'None'
error_code = 'None'
selected_file = 'No Selection'

Pi_setup = 'Not Ready'
Pi_safety = 'Not Safe'
setup = False
safety = False
stop_i = 1

# Initial States
selected = False

selected_batteries = 0
selected_days = 0
selected_hours = 0
selected_minutes = 0
selected_safety_temp = 55
selected_time_step = 1
selected_runtime = 0

# Setup_json = None
all_rows = []
global_largest_values_list = []
global_largest_values = []
global_smallest_values_list = []
global_smallest_values = []
global_last_values_list = []
global_last_values = []
graph_rows = []
graph_headers = []

old_columns = None

last_time = 0
last_ah = [0]
Ah_i = 0

Graph_1 = False
Graph_2 = False
Graph_3 = False
Graph_4 = False

start_flag = False

data_entry = 0
# Time Selector


def show_selected():
    global selected_file
    global selected_batteries
    global selected_days
    global selected_hours
    global selected_minutes
    global selected_time_step
    global selected_safety_temp
    global selected

    selected_batteries = battery.get()
    selected_days = days.get()
    selected_hours = hours.get()
    selected_minutes = minutes.get()
    selected_time_step = time_step.get()
    selected_safety_temp = safety_temp.get()

    if checkbox_var.get():
        selected_days = 'N/A'
        selected_hours = 'N/A'
        selected_minutes = 'N/A'

    # Display the selected time
    battery_str = f"Selected Battery Quantity: {selected_batteries}\n"
    csv_str = f"Selected CSV File: {selected_file}\n"
    time_str = f"Selected Test Duration: {selected_days} days, {selected_hours} hours, {selected_minutes} minutes\n"
    temp_str = f"Selected Safety Temperature (°C): {selected_safety_temp}\n"
    step_str = f"Selected Time Step (s): {selected_time_step}\n"
    result_label.config(text=battery_str + csv_str + time_str + temp_str + step_str)

    if selected_batteries != '0':
        if selected_days != '0' or selected_hours != '0' or selected_minutes != '0':
            if selected_file != 'No Selection':
                selected = True
    else:
        selected = False


# File selector
def select_file():
    global selected_file

    file_path = filedialog.askopenfilename(
        initialdir="/",  # Initial directory (you can set it to any starting directory)
        title="Select CSV File",
        filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        # multiple=False  # Allow multiple file selection (set it to True if needed)
    )
    if file_path:
        selected_file = file_path
    print(file_path)


def generate_data_headers(count):
    headers = [f"V{i}" for i in range(1, count + 1)]  # V 1-4
    headers += [f"I{i}" for i in range(1, count + 1)]  # I 1-4
    headers += [f"T{i}" for i in range(1, count + 1)]  # T 1-4
    headers += [f"Time"]  # Time (s)
    return headers


def generate_headers(inputs):
    global selected_batteries
    selected_batteries_int = int(selected_batteries)
    default_headers = ["No. Batteries", "Timestep", "Safety Temp.", "Test Duration", "Start Time"]
    test_headers = generate_data_headers(selected_batteries_int)
    headers = [default_headers, inputs, test_headers]
    return headers


def set_up_CSV(start_time):
    global selected_runtime
    inputs = [selected_batteries, selected_time_step, selected_safety_temp, selected_runtime, start_time]
    csv_header = generate_headers(inputs)
    write_data(csv_header, 'a')


def write_data(data, style='a'):
    global selected_file

    with open(selected_file, style, newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(data)


def confirm_start():
    global Setup_json
    global start_flag
    global root_state
    global selected_runtime

    if selected:
        result = messagebox.askquestion("Confirmation 1", "Are you sure you want to start?")
        if result == 'yes':

            if selected_days == 'N/A' or selected_hours == 'N/A' or selected_minutes == 'N/A':
                selected_runtime = -1
            else:
                # Convert strings to integers
                selected_days_int = int(selected_days)
                selected_hours_int = int(selected_hours)
                selected_minutes_int = int(selected_minutes)

                selected_runtime_int = selected_days_int * 86400 + selected_hours_int * 3600 + selected_minutes_int * 60
                selected_runtime = str(selected_runtime_int)

            # Create a dictionary to store the variables
            setup_data = {
                "batteries": selected_batteries,
                "runtime": selected_runtime,
                "time_step": selected_time_step,
                "safety_temp": selected_safety_temp

            }

            # Convert the dictionary to JSON
            Setup_json = json.dumps(setup_data)
            check_setup(Setup_json)

            root_state = True
            start_flag = True
            open_secondary_window()

        else:
            root.focus_set()  # Set focus back to the root window
    else:
        messagebox.showinfo("Error", "Selection Incomplete")


def check_setup(setup_json):
    global Pi_setup
    global command
    global setup

    command = 'Setup'
    cmd = command.encode('utf-8')
    UDPClient.sendto(cmd, serverAddress)

    time.sleep(0.5)

    print(setup_json)
    # Send the JSON data
    s_json = setup_json.encode('utf-8')
    UDPClient.sendto(s_json, serverAddress)
    time.sleep(0.5)

    try:
        # Receive data from the server
        # Receive response from server
        Pi_setup, _ = UDPClient.recvfrom(bufferSize)
        Pi_setup = Pi_setup.decode('utf-8')
        if Pi_setup:
            print(Pi_setup)
            if Pi_setup == 'Ready':
                setup = True
            else:
                setup = False

    except Exception as e:  # Specify the exception type
        print("Error: Setting Up:", e)


def start(button1, button2, label):
    global setup
    global Setup_json
    global command
    global safety
    global error_code
    global stop_i
    global safety_button
    global start_flag

    result = messagebox.askquestion("Confirmation", "Are you sure you want to Start?")

    if result == 'yes':

        if not setup:
            check_setup(Setup_json)

        if setup and safety:
            command = 'Start'
            cmd = command.encode('utf-8')
            UDPClient.sendto(cmd, serverAddress)
            stop_i = 1
            update_duration_label(label)
            button1.configure(bg='grey')
            button2.configure(bg='red')

        else:
            error_code = "Unsafe - Please run safety check"
            messagebox.showinfo("Error", f"Setup Error: {error_code}")

    else:
        root.focus_set()  # Set focus back to the root window


def stop(button1, button2):
    global command
    global root_state

    result = messagebox.askquestion("Confirmation", "Are you sure you want to stop?")
    if result == 'yes':
        command = 'Stop'
        cmd = command.encode('utf-8')
        UDPClient.sendto(cmd, serverAddress)

        button1.configure(bg='grey')
        button2.configure(bg='light green')

    else:
        root.focus_set()  # Set focus back to the root window


def on_closing(root1, root2):
    global root_state
    global start_flag

    root_state = False
    start_flag = False

    root1.deiconify()
    root2.destroy()


def create_graph(frame, title, y_label):
    global selected_batteries

    fig, ax = plt.subplots(figsize=(4, 3))  # Adjust the figure size as needed

    lines_list = []

    ax.set_xlabel('Time (s)')
    ax.set_ylabel(y_label)
    ax.set_title(title)
    # ax.legend()

    # Adjust subplot parameters to make room for labels
    plt.subplots_adjust(top=0.90, bottom=0.15, left=0.15, right=0.95)

    # Create canvas and toolbar
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Place toolbar directly below the canvas
    toolbar_frame = ttk.Frame(frame)
    toolbar_frame.pack(side=tk.TOP, pady=5)  # Adjust pad_y as needed

    toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
    toolbar.update()

    canvas.draw()

    return fig, ax, canvas, toolbar, lines_list


def cancel_update(after_function):
    # Cancel the scheduled update
    root.after_cancel(after_function)
    print("Update canceled")


def on_safety_button_click(button):
    global command
    global safety
    global Pi_safety
    command = 'Safety'
    cmd = command.encode('utf-8')
    UDPClient.sendto(cmd, serverAddress)

    while True:
        try:
            # Receive data from the server
            # Receive response from server
            Pi_safety, _ = UDPClient.recvfrom(bufferSize)
            Pi_safety = Pi_safety.decode('utf-8')
            if Pi_safety:
                print(Pi_safety)
                if Pi_safety == 'System Safe':
                    messagebox.showinfo("Safety Setup", "Test is safe - continue to start")
                    safety = True
                    new_color = "light green"
                    button.configure(bg=new_color)
                else:
                    messagebox.showinfo("Safety Setup", "Test is unsafe -" + Pi_safety)
                    safety = False
                    new_color = "orange"
                    button.configure(bg=new_color)

                break
        except Exception as e:  # Specify the exception type
            print("Error: Setting Up:", e)


def create_treeview(parent):
    table = ttk.Treeview(parent, columns=("Battery No.", "Voltage", "Current", "Ext. Temp."),
                         show="headings", height=4)

    # Define column headings with anchor="center"
    table.heading("Battery No.", text="Battery No.", anchor="center")
    table.heading("Voltage", text="Voltage (V)", anchor="center")
    table.heading("Current", text="Current (A)", anchor="center")
    table.heading("Ext. Temp.", text="Temp. (°C)", anchor="center")

    # Specify column width
    table.column("Battery No.", width=100, anchor="center")
    table.column("Voltage", width=100, anchor="center")
    table.column("Current", width=100, anchor="center")
    table.column("Ext. Temp.", width=100, anchor="center")

    return table


def create_treeview_2(parent):
    # Create the Treeview widget
    table = ttk.Treeview(parent, columns=(
        "Battery No.", "Max Voltage", "Max Current", "Max Temp.", "Min Voltage", "Min Current", "Min Temp."),
                         show="headings", height=4)

    # Define column headings with anchor="center"
    table.heading("Battery No.", text="Battery No.", anchor="center")
    table.heading("Max Voltage", text="Max Voltage (V)", anchor="center")
    table.heading("Max Current", text="Max Current (A)", anchor="center")
    table.heading("Max Temp.", text="Max Temp. (°C)", anchor="center")
    table.heading("Min Voltage", text="Min Voltage (V)", anchor="center")
    table.heading("Min Current", text="Min Current (A)", anchor="center")
    table.heading("Min Temp.", text="Min Temp. (°C)", anchor="center")

    # Specify column width
    table.column("Battery No.", width=80, anchor="center")
    table.column("Max Voltage", width=100, anchor="center")
    table.column("Max Current", width=100, anchor="center")
    table.column("Max Temp.", width=100, anchor="center")
    table.column("Min Voltage", width=100, anchor="center")
    table.column("Min Current", width=100, anchor="center")
    table.column("Min Temp.", width=100, anchor="center")

    return table


def populate_max_table(table):
    global global_largest_values_list

    # Clear existing data
    table.delete(*table.get_children())

    # Populate the table with global last row values
    for sublist in global_largest_values_list:
        # Insert each sublist as a new row in the table
        table.insert("", tk.END, values=sublist)


def populate_last_table(table):
    global global_last_values_list

    # Clear existing data
    table.delete(*table.get_children())

    # Populate the table with global last row values
    for sublist in global_last_values_list:
        # Insert each sublist as a new row in the table
        table.insert("", tk.END, values=sublist)


# Function to repeatedly call populate_table
def repeat_max_table_populate(table):
    # Call populate_table
    populate_max_table(table)
    # Schedule the next call to repeat_populate after 1000 milliseconds (1 second)
    secondary_window.after(1000, repeat_max_table_populate, table)


def repeat_last_table_populate(table):
    # Call populate_table
    populate_last_table(table)
    # Schedule the next call to repeat_populate after 1000 milliseconds (1 second)
    secondary_window.after(1000, repeat_last_table_populate, table)


def update_data_periodically(fig, ax, lines, canvas, mode):
    global root_state
    global graph_rows
    global secondary_window
    global Graph_1, Graph_2, Graph_3, Graph_4

    if root_state and graph_rows:
        if Graph_1 or Graph_2 or Graph_3 or Graph_4:
            print('graphing')
            update_data(fig, ax, lines, mode)
            secondary_window.update()

    # Call the function again after 2000 milliseconds (2 seconds)
    secondary_window.after(2000, update_data_periodically, fig, ax, lines, canvas, mode)


def update_data(fig, ax, lines_list, mode):
    x, y = generate_data(mode)

    # Get current color cycle
    prop_cycle = plt.rcParams['axes.prop_cycle']
    colors = prop_cycle.by_key()['color']

    # Clear existing lines
    for line in lines_list:
        line.remove()

    # Create new lines and add them to lines_list
    lines_list.clear()
    for i, y_i in enumerate(y):
        line = ax.plot(x, y_i, color=colors[i % len(colors)], label=f'Battery {i + 1}')[0]
        lines_list.append(line)

    # Add legend
    ax.legend()

    ax.relim()
    ax.autoscale_view()
    fig.canvas.draw_idle()


def generate_data(mode):
    global selected_batteries
    global graph_headers
    global graph_rows
    global Graph_1, Graph_2, Graph_3, Graph_4

    selected_batteries_int = int(selected_batteries)

    i1 = selected_batteries_int
    i2 = i1 + i1
    i3 = i2 + i1

    selected_y_headers = []
    selected_y_columns = []

    # Get the data rows from generate_data()
    # data_rows = generate_data()

    # Extract the selected x-columns
    selected_x_columns = graph_rows[-1]  # Assuming the last column is for x-axis data

    if mode == 'V':
        selected_y_columns = graph_rows[:i1]
        Graph_1 = False
    elif mode == 'C':
        selected_y_columns = graph_rows[i1:i2]
        Graph_2 = False
    elif mode == 'T':
        selected_y_columns = graph_rows[i2:i3]
        Graph_3 = False
    elif mode == 'H':
        selected_y_columns = graph_rows[i1:i2]
        Graph_4 = False

    x_data_list = list(selected_x_columns)
    y_data_list = [list(t) for t in selected_y_columns]

    if mode == 'H':
        x_data_list, y_data_list = calculateAh(y_data_list, x_data_list)

    print('x and y')

    print(x_data_list)
    print(y_data_list)

    return x_data_list, y_data_list


def calculateAh(current_data_list, time_data):
    global last_time, last_ah, Ah_i

    if Ah_i == 0:
        last_time = 0
        last_ah = [0] * len(current_data_list)  # Initialize last Ah for each battery
        Ah_i = 1

    y_data_list = []  # List of Ampere-hours for each battery

    x_data = time_data[1:]  # Exclude the first time point

    for current_data, last_ah_bat in zip(current_data_list, last_ah):
        ampere_hours = last_ah_bat
        y_data = []
        for i in range(1, len(current_data)):
            delta_time = time_data[i] - time_data[i - 1]
            avg_current = (current_data[i] + current_data[i - 1]) / 2
            ampere_hour = avg_current * delta_time / 3600  # Convert time from seconds to hours
            ampere_hours += ampere_hour
            y_data.append(ampere_hours)

        y_data_list.append(y_data)

    last_time = time_data[-1]  # Update last time
    last_ah = [y_data[-1] for y_data in y_data_list]  # Update last Ah for each battery

    return x_data, y_data_list


def start_listening_thread(UDPClient, bufferSize):
    # Start a thread to listen for data
    listen_thread = threading.Thread(target=listen_for_data, args=(UDPClient, bufferSize))
    listen_thread.daemon = True  # Daemonize the thread to close it when the main thread exits
    listen_thread.start()


def listen_for_data(UDPClient, bufferSize):
    # Continuously listen for data
    global start_flag
    while start_flag:
        try:
            # Receive data from the server
            data, _ = UDPClient.recvfrom(bufferSize)
            data = data.decode('utf-8')

            # Try to parse the data as JSON
            try:
                json_data = json.loads(data)
                # If parsing succeeds, then `data` is JSON
                print("Data is JSON.")
                # Now you can work with the JSON data in `json_data` variable
                # Perform actions specific to JSON data
                process_json_data(json_data)

            except json.JSONDecodeError:
                # If parsing fails, then `data` is not JSON
                #print("Data is not JSON.")
                # Perform actions specific to non-JSON data
                check_command(data)

        except OSError as e:
            print("Error receiving data:", e)
        except Exception as e:
            print("Unexpected error:", e)


def update_duration_label(label):
    # Get the current time
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Update the label text with the current time
    label.config(text=f"Test Start Time:\n{current_time}")


def open_secondary_window():
    global secondary_window, fig, ax, canvas, toolbar, lines

    # Create a secondary window
    secondary_window = tk.Tk()
    secondary_window.title("Test Window")
    secondary_window.geometry("1500x770")

    # Buttons
    start_button = tk.Button(secondary_window, text="Start",
                             command=lambda: start(start_button, stop_button, duration_label),
                             bg="light green", width=10, height=2)
    stop_button = tk.Button(secondary_window, text="Stop",
                            command=lambda: stop(stop_button, start_button),
                            bg="grey", width=10, height=2)
    safety_button = tk.Button(secondary_window, text="Safety Check",
                              command=lambda: on_safety_button_click(safety_button),
                              bg="orange", width=10, height=2)
    start_button.grid(row=0, column=0, padx=5, pady=5)
    stop_button.grid(row=0, column=1, padx=5, pady=5)
    safety_button.grid(row=0, column=2, padx=5, pady=5)

    # Create frames for each graph
    graph_frame1 = ttk.Frame(secondary_window)
    graph_frame2 = ttk.Frame(secondary_window)
    graph_frame3 = ttk.Frame(secondary_window)
    graph_frame4 = ttk.Frame(secondary_window)

    # Grid layout for frames
    graph_frame1.grid(row=1, column=0, padx=10, pady=10)
    graph_frame2.grid(row=1, column=1, padx=10, pady=10)
    graph_frame3.grid(row=2, column=1, padx=10, pady=10)
    graph_frame4.grid(row=2, column=0, padx=10, pady=10)

    # Create four smaller graphs with different titles
    fig1, ax1, canvas1, toolbar1, lines1 = create_graph(graph_frame1, title="Voltage", y_label="V")
    fig2, ax2, canvas2, toolbar2, lines2 = create_graph(graph_frame2, title="Current", y_label="C")
    fig3, ax3, canvas3, toolbar3, lines3 = create_graph(graph_frame3, title="Ampere-hour", y_label="Ah")
    fig4, ax4, canvas4, toolbar4, lines4 = create_graph(graph_frame4, title="Surface Temperature", y_label="°C")

    canvas = [canvas1, canvas2, canvas3, canvas4]
    toolbar = [toolbar1, toolbar2, toolbar3, toolbar4]
    lines = [lines1, lines2, lines3, lines4]

    update_data_periodically(fig1, ax1, lines1, canvas1, 'V')
    update_data_periodically(fig2, ax2, lines2, canvas2, 'C')
    update_data_periodically(fig3, ax3, lines3, canvas3, 'H')
    update_data_periodically(fig4, ax4, lines4, canvas4, 'T')

    # Create a Treeview widget using the function
    data_table = create_treeview(secondary_window)
    data_table.grid(row=1, column=2, padx=10, pady=5, sticky="s")
    # Call this function when you want to populate the table with data
    repeat_last_table_populate(data_table)

    # Add title or label for the Treeview
    table_label = tk.Label(secondary_window, text="Latest Recorded Values", font=("Arial", 14))
    table_label.grid(row=1, column=2, padx=10, pady=75)

    # Test duration label
    duration_label = tk.Label(secondary_window, text="Test Duration", font=("Arial", 14))
    duration_label.grid(row=1, column=2, padx=10, pady=75, sticky="n")

    # Create a second Treeview widget using the function
    data_table_2 = create_treeview_2(secondary_window)
    data_table_2.grid(row=2, column=2, padx=10, pady=5)
    # Call this function when you want to populate the table with data
    repeat_max_table_populate(data_table_2)

    # Add title or label for the Treeview
    table_label_2 = tk.Label(secondary_window, text="Min and Max Recorded Values", font=("Arial", 14))
    table_label_2.grid(row=2, column=2, padx=10, pady=75, sticky="n")

    start_listening_thread(UDPClient, bufferSize)

    secondary_window.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, secondary_window))  # Closing event
    root.withdraw()  # Withdraw the main root window


def check_command(data):
    global safety
    global setup
    global stop_i

    print(data)

    if data == 'Stopped':
        safety = False
        if stop_i == 1:
            messagebox.showinfo("STOPPED", "Test has been stopped")
            stop_i = 0

    if data == 'Unsafe Temp':
        messagebox.showinfo("STOP", "Test temperature is unsafe - trying to stop")
        safety = False

    if data == 'Unsafe':
        messagebox.showinfo("STOP", "Test is unsafe - trying to stop")
        safety = False

    if data == 'CSV':
        while True:
            try:
                # Receive data from the server
                data, _ = UDPClient.recvfrom(bufferSize)
                data = data.decode('utf-8')
                print(data)
                if data != 'CSV':
                    set_up_CSV(data)

                csv_check = 'Done'
                csv_cmd = csv_check.encode('utf-8')
                UDPClient.sendto(csv_cmd, serverAddress)

                break
            except Exception as e:
                print("Unexpected error:", e)


def process_json_data(json_data):
    global selected_file
    global all_rows
    global global_largest_values_list
    global global_largest_values
    global global_smallest_values_list
    global global_smallest_values
    global global_last_values_list
    global global_last_values
    global graph_rows
    global graph_headers
    global selected_batteries
    global old_columns
    global Graph_1, Graph_2, Graph_3, Graph_4
    global data_entry
    # Extract headers from the keys of the first dictionary
    headers = list(json_data[0].keys())

    # Extract rows of data
    rows = [[row[header] for header in headers] for row in json_data]

    all_rows = rows
    try:
        write_data(all_rows)
        print("All rows saved to the CSV file successfully.")
        all_rows = []
    except Exception as e:
        print("An error occurred while saving the CSV file:", e)

    # Extract Data
    # Convert rows to columns
    columns = list(zip(*rows))

    combined_columns = []

    if old_columns:
        # Iterate over each column in columns and append its data to the corresponding column in old_columns
        for i in range(len(columns)):
            combined_columns.append(old_columns[i] + columns[i])

        if data_entry < 100:
            old_columns = combined_columns
            data_entry += 1
        else:
            # Remove the first 10 rows from each column in old_columns
            old_columns = [column[10:] for column in combined_columns]

    else:
        old_columns = columns
        combined_columns = columns

    graph_rows = combined_columns
    Graph_1 = True
    Graph_2 = True
    Graph_3 = True
    Graph_4 = True

    # Print columns of data
    for i, column in enumerate(columns):
        print(f'Column {i + 1}: {column}')

    # Obtain the largest value in each column
    largest_values = [max(column[:-1]) for column in columns]

    # Initialize global_largest_values if it's None
    if not global_largest_values:
        global_largest_values = largest_values
    else:
        # Compare corresponding elements and find the maximum for each column
        global_largest_values = [max(val1, val2) for val1, val2 in zip(largest_values, global_largest_values)]

    # Split the flat list into three equal parts
    n_max = len(global_largest_values) // 3
    v_list_max = global_largest_values[:n_max]
    c_list_max = global_largest_values[n_max:2 * n_max]
    t_list_max = global_largest_values[2 * n_max:]

    # Combine the corresponding elements into sub-lists
    global_largest_values_list = [[v, c, t] for v, c, t in zip(v_list_max, c_list_max, t_list_max)]

    # Add a number at the front of each sublist
    for i, sublist in enumerate(global_largest_values_list, start=1):
        sublist.insert(0, i)

    # Obtain the smallest value in each column, excluding the last column
    smallest_values = [min(column[:-1]) for column in columns]

    # Initialize global_smallest_values if it's None
    if not global_smallest_values:
        global_smallest_values = smallest_values
    else:
        # Compare corresponding elements and find the minimum for each column
        global_smallest_values = [min(val1, val2) for val1, val2 in zip(smallest_values, global_smallest_values)]

    # Split the flat list into three equal parts
    n_min = len(global_smallest_values) // 3
    v_list_min = global_smallest_values[:n_min]
    c_list_min = global_smallest_values[n_min:2 * n_min]
    t_list_min = global_smallest_values[2 * n_min:]

    # Combine the corresponding elements into sub-lists
    global_smallest_values_list = [[v, c, t] for v, c, t in zip(v_list_min, c_list_min, t_list_min)]

    # Extend largest sublists with smallest sublists
    for i, sublist in enumerate(global_largest_values_list):
        sublist.extend(global_smallest_values_list[i])

    # Obtain the last row in each column
    last_values = [column[-1] for column in columns]

    # Split the flat list into three equal parts
    n = len(last_values) // 3
    v_list = last_values[:n]
    c_list = last_values[n:2 * n]
    t_list = last_values[2 * n:]

    # Combine the corresponding elements into sub-lists
    global_last_values_list = [[v, c, t] for v, c, t in zip(v_list, c_list, t_list)]

    # Add a number at the front of each sublist
    for i, sublist in enumerate(global_last_values_list, start=1):
        sublist.insert(0, i)


# -----------------------------Global Variables---------------------------------------
# Root Setup
root = tk.Tk()
root.title("Settings Window")
root.geometry("600x450")

# Variables to store the selected values
battery = tk.StringVar(root)
days = tk.StringVar(root)
hours = tk.StringVar(root)
minutes = tk.StringVar(root)
safety_temp = tk.StringVar(root)
time_step = tk.StringVar(root)

# Dropdown Options  # Change range as needed
battery_list = list(range(0, 5))
days_list = list(range(0, 31))
hours_list = list(range(0, 24))
minutes_list = list(range(0, 60))
safety_temp_list = list(range(55, 80, 5)) #list(range(15, 30, 1))
time_step_list = [0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 2, 3, 4, 5]
#time_step_list = [0.5 + i * 0.25 for i in range(int((10 - 0.5) / 0.25) + 1)]

# Set default values
battery.set(str(battery_list[0]))
days.set(str(days_list[0]))
hours.set(str(hours_list[0]))
minutes.set(str(minutes_list[0]))
safety_temp.set(str(safety_temp_list[0]))
time_step.set(str(time_step_list[24]))

# Create a Tkinter variable to hold the state of the checkbox
checkbox_var = tk.BooleanVar()

# -----------------------------Main Root Objects---------------------------------------

# Buttons
csv_button = tk.Button(root, text="Select CSV File", command=select_file)
show_button = tk.Button(root, text="Confirm Selection", command=show_selected)
confirm_button = tk.Button(root, text="Confirm Test", command=confirm_start)

csv_button.grid(row=2, column=2, sticky="w", pady=5)
show_button.grid(row=7, column=1, columnspan=4, pady=5)
confirm_button.grid(row=9, column=1, columnspan=4)

# Checkbox
checkbox = tk.Checkbutton(root, text="Check for a continuous testing duration", variable=checkbox_var)
checkbox.grid(row=4, column=2, pady=5, sticky="w",  columnspan=5)

# Dropdowns
battery_dropdown = tk.OptionMenu(root, battery, *battery_list)
days_dropdown = tk.OptionMenu(root, days, *days_list)
hours_dropdown = tk.OptionMenu(root, hours, *hours_list)
minutes_dropdown = tk.OptionMenu(root, minutes, *minutes_list)
safety_temp_dropdown = tk.OptionMenu(root, safety_temp, *safety_temp_list)
time_step_dropdown = tk.OptionMenu(root, time_step, *time_step_list)

battery_dropdown.grid(row=1, column=2, pady=5, sticky="w")
days_dropdown.grid(row=3, column=2, pady=5, sticky="w")
hours_dropdown.grid(row=3, column=3, pady=5, sticky="w")
minutes_dropdown.grid(row=3, column=4, pady=5, sticky="w")
safety_temp_dropdown.grid(row=5, column=2, pady=5, sticky="w")
time_step_dropdown.grid(row=6, column=2, pady=5, sticky="w")

# Labels
battery_label = tk.Label(root, text="Number of Batteries:")
csv_label = tk.Label(root, text="CSV File:")
time_label = tk.Label(root, text="Test Duration:")
days_label = tk.Label(root, text="Days")
hours_label = tk.Label(root, text="Hours")
minutes_label = tk.Label(root, text="Minutes")
safety_temp_label = tk.Label(root, text="Safety Temp (°C):")
time_step_label = tk.Label(root, text="Time Step (s):")
default_temp_label = tk.Label(root, text="Default - 55°C")
default_step_label = tk.Label(root, text="Default - 1s    Bit Precision: 18 > 0.655s > 16 > 0.155s > 14 > 0.055s > 12")
result_label = tk.Label(root, text="")

battery_label.grid(row=1, column=1, pady=5)
csv_label.grid(row=2, column=1, pady=5)
time_label.grid(row=3, column=1, pady=5)
days_label.grid(row=3, column=2, pady=5, padx=60, sticky='w')
hours_label.grid(row=3, column=3, pady=5, padx=60)
minutes_label.grid(row=3, column=4, pady=5, padx=60)
safety_temp_label.grid(row=5, column=1, pady=5, padx=5)
time_step_label.grid(row=6, column=1, pady=5, padx=5)
default_temp_label.grid(row=5, column=2, pady=5, padx=60, columnspan=5, sticky='w')
default_step_label.grid(row=6, column=2, pady=5, padx=60, columnspan=5)
result_label.grid(row=8, column=1, pady=5, columnspan=4)

root.mainloop()
