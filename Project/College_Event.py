import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
import threading
import time
from tkcalendar import DateEntry
import re
from twilio.rest import Client

class EventManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("College Event Management System")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # Initialize database connection
        self.conn = sqlite3.connect('college_events.db',check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        
        # Start with login page
        self.show_login_page()
        
        # Start notification system
        self.notification_thread = threading.Thread(target=self.check_notifications, daemon=True)
        self.notification_thread.start()

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users
                             (username TEXT PRIMARY KEY, password TEXT, role TEXT, phone TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS events
                             (event_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, date TEXT, location TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS participants
                             (event_id INTEGER, username TEXT, FOREIGN KEY(event_id) REFERENCES events(event_id),
                              FOREIGN KEY(username) REFERENCES users(username))''')
        self.conn.commit()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def create_styled_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command,
                        bg="#007bff", fg="white",
                        font=("Arial", 10, "bold"),
                        relief=tk.RAISED,
                        padx=20, pady=5)

    def create_styled_entry(self, parent):
        return tk.Entry(parent, font=("Arial", 10),
                       relief=tk.SOLID, bd=1)

    def show_login_page(self):
        self.clear_window()
        
        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(frame, text="College Event Management System",
                font=("Arial", 16, "bold"),
                bg="#f0f0f0").pack(pady=20)
        
        tk.Label(frame, text="Username:", bg="#f0f0f0").pack()
        username_entry = self.create_styled_entry(frame)
        username_entry.pack(pady=5)
        
        tk.Label(frame, text="Password:", bg="#f0f0f0").pack()
        password_entry = self.create_styled_entry(frame)
        password_entry.config(show="*")
        password_entry.pack(pady=5)
        
        self.create_styled_button(frame, "Login",
                                lambda: self.login(username_entry.get(),
                                                 password_entry.get())).pack(pady=10)
        
        self.create_styled_button(frame, "Register",
                                self.show_registration_page).pack(pady=5)

    def show_registration_page(self):
        self.clear_window()
        
        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(frame, text="Registration", font=("Arial", 16, "bold"),
                bg="#f0f0f0").pack(pady=20)
        
        tk.Label(frame, text="Username:", bg="#f0f0f0").pack()
        username_entry = self.create_styled_entry(frame)
        username_entry.pack(pady=5)
        
        tk.Label(frame, text="Password:", bg="#f0f0f0").pack()
        password_entry = self.create_styled_entry(frame)
        password_entry.config(show="*")
        password_entry.pack(pady=5)
        
        tk.Label(frame, text="Phone Number:", bg="#f0f0f0").pack()
        phone_entry = self.create_styled_entry(frame)
        phone_entry.pack(pady=5)
        
        role_var = tk.StringVar(value="participant")
        tk.Radiobutton(frame, text="Admin", variable=role_var,
                      value="admin", bg="#f0f0f0").pack()
        tk.Radiobutton(frame, text="Participant", variable=role_var,
                      value="participant", bg="#f0f0f0").pack()
        
        self.create_styled_button(frame, "Register",
                                lambda: self.register(username_entry.get(),
                                                    password_entry.get(),
                                                    phone_entry.get(),
                                                    role_var.get())).pack(pady=10)
        
        self.create_styled_button(frame, "Back to Login",
                                self.show_login_page).pack(pady=5)

    def register(self, username, password, phone, role):
        if not username or not password or not phone:
            messagebox.showerror("Error", "All fields are required!")
            return
            
        if not re.match(r'^\d{10}$', phone):
            messagebox.showerror("Error", "Invalid phone number format!")
            return
            
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if self.cursor.fetchone():
            messagebox.showerror("Error", "Username already exists!")
            return
            
        self.cursor.execute("INSERT INTO users (username, password, role, phone) VALUES (?, ?, ?, ?)", 
                           (username, password, role, phone))
        self.conn.commit()
        messagebox.showinfo("Success", "Registration successful!")
        self.show_login_page()

    def login(self, username, password):
        # Query the database for the user with the given username and password
        self.cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = self.cursor.fetchone()

        if user:
            # If a user is found, set the current user and navigate based on role
            self.current_user = username  # Set the current user
            if user[2] == 'admin':  # Check if the user role is admin
                self.show_admin_dashboard(username)
            else:
                self.show_participant_dashboard(username)
        else:
            # If no matching user is found, show an error message
            messagebox.showerror("Error", "Invalid credentials!")


    def show_admin_dashboard(self, username):
        self.clear_window()
        self.current_user = username
        
        # Create main container
        container = tk.Frame(self.root, bg="#f0f0f0")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        tk.Label(container, text=f"Welcome Admin: {username}",
                font=("Arial", 16, "bold"),
                bg="#f0f0f0").pack(pady=10)
        
        # Buttons container
        button_frame = tk.Frame(container, bg="#f0f0f0")
        button_frame.pack(pady=20)
        
        self.create_styled_button(button_frame, "Add New Event",
                                self.show_add_event_page).pack(side=tk.LEFT, padx=10)
        self.create_styled_button(button_frame, "View Events",
                                self.show_admin_events_page).pack(side=tk.LEFT, padx=10)
        self.create_styled_button(button_frame, "Delete Event",
                                self.show_delete_event_page).pack(side=tk.LEFT, padx=10)
        self.create_styled_button(button_frame, "Logout",
                                self.show_login_page).pack(side=tk.LEFT, padx=10)
        

    def show_add_event_page(self):
        self.clear_window()
        
        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(frame, text="Add New Event",
                font=("Arial", 16, "bold"),
                bg="#f0f0f0").pack(pady=20)
        
        tk.Label(frame, text="Event Name:", bg="#f0f0f0").pack()
        name_entry = self.create_styled_entry(frame)
        name_entry.pack(pady=5)
        
        tk.Label(frame, text="Date:", bg="#f0f0f0").pack()
        date_entry = DateEntry(frame, width=12, background='darkblue',
                             foreground='white', borderwidth=2)
        date_entry.pack(pady=5)
        
        tk.Label(frame, text="Time (HH:MM):", bg="#f0f0f0").pack()
        time_entry = self.create_styled_entry(frame)
        time_entry.pack(pady=5)
        
        tk.Label(frame, text="Location:", bg="#f0f0f0").pack()
        location_entry = self.create_styled_entry(frame)
        location_entry.pack(pady=5)
        
        def add_event():
            name = name_entry.get()
            date = date_entry.get()
            time = time_entry.get()
            location = location_entry.get()
            
            if not all([name, date, time, location]):
                messagebox.showerror("Error", "All fields are required!")
                return
                
            self.cursor.execute("INSERT INTO events (name, date, location) VALUES (?, ?, ?)", 
                               (name, f"{date} {time}", location))
            self.conn.commit()
            messagebox.showinfo("Success", "Event added successfully!")
            self.show_admin_dashboard(self.current_user)
        
        self.create_styled_button(frame, "Add Event", add_event).pack(pady=10)
        self.create_styled_button(frame, "Back", lambda: self.show_admin_dashboard(self.current_user)).pack(pady=5)

    def show_delete_event_page(self):
        self.clear_window()
        
        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(frame, text="Delete Event",
                font=("Arial", 16, "bold"),
                bg="#f0f0f0").pack(pady=20)
        
        # Create treeview
        tree = ttk.Treeview(frame, columns=("Name", "Date", "Location"),
                           show="headings")
        
        tree.heading("Name", text="Event Name")
        tree.heading("Date", text="Date")
        tree.heading("Location", text="Location")
        
        self.cursor.execute("SELECT * FROM events")
        for event in self.cursor.fetchall():
            tree.insert("", tk.END, values=(
                event[1],
                event[2],
                event[3]
            ))
        
        tree.pack(pady=10, fill=tk.BOTH, expand=True)
        
        def delete_selected_event():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Please select an event to delete!")
                return
                
            event_values = tree.item(selected_item[0])['values']
            event_name = event_values[0]
            
            self.cursor.execute("SELECT event_id FROM events WHERE name = ?", (event_name,))
            event_id = self.cursor.fetchone()[0]
            
            # Delete participants associated with the event
            self.cursor.execute("DELETE FROM participants WHERE event_id = ?", (event_id,))
            # Delete the event
            self.cursor.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
            self.conn.commit()
            
            messagebox.showinfo("Success", "Event deleted successfully!")
            self.show_admin_dashboard(self.current_user)
        
        self.create_styled_button(frame, "Delete Event",
                                delete_selected_event).pack(pady=10)
        self.create_styled_button(frame, "Back",
                                lambda: self.show_admin_dashboard(self.current_user)).pack(pady=5)


    def show_admin_events_page(self):
        self.clear_window()
        
        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(frame, text="Events List",
                font=("Arial", 16, "bold"),
                bg="#f0f0f0").pack(pady=20)
        
        # Create treeview
        tree = ttk.Treeview(frame, columns=("Name", "Date", "Location", "Participants"),
                           show="headings")
        
        tree.heading("Name", text="Event Name")
        tree.heading("Date", text="Date")
        tree.heading("Location", text="Location")
        tree.heading("Participants", text="Participants")
        
        self.cursor.execute("SELECT * FROM events")
        for event in self.cursor.fetchall():
            self.cursor.execute("SELECT COUNT(*) FROM participants WHERE event_id = ?", (event[0],))
            participant_count = self.cursor.fetchone()[0]
            tree.insert("", tk.END, values=(
                event[1],
                event[2],
                event[3],
                participant_count
            ))
        
        tree.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.create_styled_button(frame, "Back",
                                lambda: self.show_admin_dashboard(self.current_user)).pack(pady=10)

    def show_participant_dashboard(self, username):
        self.clear_window()
        self.current_user = username
        
        frame = tk.Frame(self.root, bg="#f0f0f0")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(frame, text=f"Welcome {username}",
                font=("Arial", 16, "bold"),
                bg="#f0f0f0").pack(pady=20)
        
        # Create treeview for events
        tree = ttk.Treeview(frame, columns=("Name", "Date", "Location", "Status"),
                           show="headings")
        
        tree.heading("Name", text="Event Name")
        tree.heading("Date", text="Date")
        tree.heading("Location", text="Location")
        tree.heading("Status", text="Status")
        
        self.cursor.execute("SELECT e.name, e.date, e.location, (CASE WHEN p.username IS NULL THEN 'Not Registered' ELSE 'Registered' END) AS status "
                           "FROM events e "
                           "LEFT JOIN participants p ON e.event_id = p.event_id AND p.username = ?", (username,))
        for event in self.cursor.fetchall():
            tree.insert("", tk.END, values=event)
        
        tree.pack(pady=10, fill=tk.BOTH, expand=True)
        
        def register_for_selected():
            selected_item = tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Please select an event!")
                return
                
            event_values = tree.item(selected_item[0])['values']
            event_name = event_values[0]
            
            self.cursor.execute("SELECT event_id FROM events WHERE name = ?", (event_name,))
            event_id = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT * FROM participants WHERE event_id = ? AND username = ?", (event_id, username))
            if not self.cursor.fetchone():
                self.cursor.execute("INSERT INTO participants (event_id, username) VALUES (?, ?)", (event_id, username))
                self.conn.commit()
                messagebox.showinfo("Success", "Successfully registered for the event!")
                self.show_participant_dashboard(username)
        
        button_frame = tk.Frame(frame, bg="#f0f0f0")
        button_frame.pack(pady=10)
        
        self.create_styled_button(button_frame, "Register for Event",
                                register_for_selected).pack(side=tk.LEFT, padx=10)
        self.create_styled_button(button_frame, "Logout",
                                self.show_login_page).pack(side=tk.LEFT, padx=10)


    def send_sms_notification(self, phone_number, message):
        # Your Twilio account SID and Auth token
        account_sid = 'AC5be3d3a70db58c5a7c9a8f943abeb97e'
        auth_token = '[5e228f350ce014de929ad64d9b88a9e7]'

        # Create a Twilio client
        client = Client(account_sid, auth_token)

        # Send the SMS
        client.messages.create(
            body="Started",
            from_='+19712163920',  # Your Twilio phone number
            to='+917397125015',
        )

    def send_bulk_notification(self):
        current_time = datetime.now()
        
        # Query to get all upcoming events and participants
        self.cursor.execute('''
            SELECT e.name, e.date, e.location, u.phone
            FROM events e
            JOIN participants p ON e.event_id = p.event_id
            JOIN users u ON p.username = u.username
        ''')
        
        notifications_sent = 0
        for event_name, event_date, location, phone in self.cursor.fetchall():
            try:
                event_time = datetime.strptime(event_date, "%Y-%m-%d %H:%M")
                time_diff = (event_time - current_time).total_seconds() / 60
                
                if 0 < time_diff <= 1440:  # Notify if event is within the next 24 hours
                    message = f"Reminder: {event_name} at {location} on {event_date}."
                    self.send_sms_notification(phone, message)
                    notifications_sent += 1
            except ValueError:
                continue  # Skip if date parsing fails

        messagebox.showinfo("Notifications", f"Notifications sent to {notifications_sent} participants.")

    def check_notifications(self):
        while True:
            try:
                current_time = datetime.now()
                # Fetch upcoming events within the next 10 minutes and their participants
                self.cursor.execute('''
                    SELECT e.name, e.date, e.location, u.phone
                    FROM events e
                    JOIN participants p ON e.event_id = p.event_id
                    JOIN users u ON p.username = u.username
                    WHERE datetime(e.date) > datetime('now') 
                      AND datetime(e.date) <= datetime('now', '+10 minutes')
                ''')
                events_to_notify = self.cursor.fetchall()

                # Loop through fetched events and send notifications
                for event_name, event_date, location, phone in events_to_notify:
                    message = f"Reminder: {event_name} is starting soon at {event_date}. Location: {location}."
                    try:
                        self.send_sms_notification(phone, message)
                    except Exception as e:
                        print(f"Failed to send SMS to {phone}: {e}")

            except Exception as e:
                print(f"Error in notification process: {e}")

            # Check every minute
            time.sleep(60)
        
if __name__ == "__main__":
    root = tk.Tk()
    app = EventManagementApp(root)
    root.mainloop()
