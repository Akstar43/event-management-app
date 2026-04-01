import tkinter as tk 
from tkinter import ttk, messagebox,PhotoImage 
import sqlite3 
import hashlib 
import re 

class UserAuthentication: 
    def __init__(self, db_name='users.db'): 
        self.conn = sqlite3.connect(db_name) 
        self.create_table() 

    def create_table(self): 
        with self.conn: 
            self.conn.execute(''' 
                CREATE TABLE IF NOT EXISTS users ( 
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    username TEXT UNIQUE NOT NULL, 
                    password TEXT NOT NULL 
                ) 
            ''') 

    def hash_password(self, password): 
        return hashlib.sha256(password.encode()).hexdigest() 

    def is_username_taken(self, username): 
        cursor = self.conn.cursor() 
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,)) 
        return cursor.fetchone() is not None 

    def is_password_valid(self, password): 
        pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$') 
        return pattern.match(password) is not None 

    def register(self, username, password): 
        if self.is_username_taken(username): 
            return "Username already taken. Please use another one." 
        if not self.is_password_valid(password): 
            return "Password must have at least 8 characters, including a special character, lowercase, and uppercase letters." 
        
        hashed_password = self.hash_password(password) 
        with self.conn: 
            self.conn.execute('INSERT INTO users(username, password) VALUES (?, ?)', (username, hashed_password)) 
        return "User registered successfully." 

    def login(self, username, password): 
        hashed_password = self.hash_password(password) 
        cursor = self.conn.cursor() 
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_password)) 
        user = cursor.fetchone() 

        if username == 'admin' and hashed_password == self.hash_password('admin1234@A'): 
            return "Login admin successful" 
        if user:
            return "Login successful"

    def close_connection(self): 
        self.conn.close() 

class UserDashboard: 
    def __init__(self, root, username): 
        self.root = root 
        self.root.title("Event Dashboard") 
        self.root.geometry('800x500') 

        self.nav = tk.Frame(self.root, width=750, height=100, background='blue') 
        self.nav.pack(fill=tk.X) 
        self.logout = tk.Button(self.nav, text='Logout', background='white', command=self.logout_user) 
        self.logout.pack(side=tk.RIGHT, fill=tk.X, padx=5) 

        # Updated to match database schema
        self.table = ttk.Treeview(self.root, columns=('id', 'organizer', 'name', 'time', 'date'), show='headings') 
        self.table.heading('organizer', text='Event Organizer') 
        self.table.heading('name', text='Event Name') 
        self.table.heading('time', text='Event Time') 
        self.table.heading('date', text='Event Date') 
        self.table.column('id', width=0, stretch=tk.NO) 
        self.table.place(relx=0, rely=0.35)
        self.load_events()
    def load_events(self): 
        self.conn = sqlite3.connect('events.db')
        for row in self.table.get_children(): 
            self.table.delete(row) 
        cursor = self.conn.cursor() 
        cursor.execute("SELECT id, organizer, name, time, date FROM events") 
        for row in cursor.fetchall(): 
            self.table.insert('', 'end', values=row) 

    def logout_user(self): 
        self.root.destroy() 
        root = tk.Tk() 
        LoginPage(root) 
        root.mainloop() 

class AdminDashboard:
    def __init__(self, root, username):
        self.root = root
        self.root.title("Admin Dashboard")
        self.root.geometry('1000x500')

        self.conn = sqlite3.connect("events.db")
        self.create_events_table()

        # Navigation frame
        self.nav = tk.Frame(self.root, width=750, height=100, background='blue')
        self.nav.pack(fill=tk.X)

        
        # Create event button
        self.create_event = tk.Button(self.nav, background='white', text='Create event', command=self.open_create_event_window)
        self.create_event.pack(side=tk.RIGHT, fill=tk.X, padx=5)
        
        # Logout button
        self.logout = tk.Button(self.nav, text='Logout', background='white', command=self.logout_user)
        self.logout.pack(side=tk.RIGHT, fill=tk.X, padx=5)

        # Edit and delete buttons
        self.edit_button = tk.Button(self.root, text='Edit', command=self.edit_event)
        self.edit_button.place(relx=0.1, rely=0.2)
        self.delete_button = tk.Button(self.root, text='Delete', command=self.delete_event)
        self.delete_button.place(relx=0.2, rely=0.2)

        # Event table
        self.table = ttk.Treeview(self.root, columns=('id', 'organizer', 'name', 'time', 'date'), show='headings')
        self.table.heading('id', text='Event ID')
        self.table.heading('organizer', text='Event Organizer')
        self.table.heading('name', text='Event Name')
        self.table.heading('time', text='Event Time')
        self.table.heading('date', text='Event Date')
        self.table.place(relx=0, rely=0.35)

        # Load existing events
        self.load_events()

    def create_events_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organizer TEXT NOT NULL,
                    name TEXT NOT NULL,
                    time TEXT NOT NULL,
                    date TEXT NOT NULL
                )
            ''')

    def open_create_event_window(self):
        create_event_window = tk.Toplevel(self.root)
        AddEvent(create_event_window, self.load_events)

    def edit_event(self):
        selected_item = self.table.selection()
        if not selected_item:
            messagebox.showwarning("Select Event", "Please select an event to edit.")
            return

        item_values = self.table.item(selected_item)['values']
        edit_event_window = tk.Toplevel(self.root)
        EditEvent(edit_event_window, self.load_events, item_values, int(item_values[0]))  # Pass ID as integer

    def delete_event(self):
        selected_item = self.table.selection()
        if not selected_item:
            messagebox.showwarning("Select Event", "Please select an event to delete.")
            return

        event_id = int(self.table.item(selected_item)['values'][0])  # Ensure ID is treated as integer
        confirmation = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this event?")
        if confirmation:
            try:
                with self.conn:
                    self.conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
                messagebox.showinfo("Deleted", "Event deleted successfully.")
                self.load_events()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete event: {e}")

    def load_events(self):
        for row in self.table.get_children():
            self.table.delete(row)

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, organizer, name, time, date FROM events")
        for row in cursor.fetchall():
            self.table.insert('', 'end', values=row)

    def logout_user(self):
        self.root.destroy()
        root = tk.Tk()
        LoginPage(root)
        root.mainloop()
class AddEvent: 
    def __init__(self, root, refresh_callback): 
        self.root = root 
        self.refresh_callback = refresh_callback 
        self.root.title("Add New Event") 
        self.root.geometry("400x300") 

        self.org_label = tk.Label(self.root, text="Event Organizer:") 
        self.org_label.grid(row=0, column=0, padx=10, pady=10, sticky='w') 
        self.org_entry = tk.Entry(self.root, width=30) 
        self.org_entry.grid(row=0, column=1, padx=10, pady=10) 

        self.name_label = tk.Label(self.root, text="Event Name:") 
        self.name_label.grid(row=1, column=0, padx=10, pady=10, sticky='w') 
        self.name_entry = tk.Entry(self.root, width=30) 
        self.name_entry.grid(row=1, column=1, padx=10, pady=10) 

        self.time_label = tk.Label(self.root, text="Event Time:") 
        self.time_label.grid(row=2, column=0, padx=10, pady=10, sticky='w') 
        self.time_entry = tk.Entry(self.root, width=30) 
        self.time_entry.grid(row=2, column=1, padx=10, pady=10) 

        self.date_label = tk.Label(self.root, text="Event Date:") 
        self.date_label.grid(row=3, column=0, padx=10, pady=10, sticky='w') 
        self.date_entry = tk.Entry(self.root, width=30) 
        self.date_entry.grid(row=3, column=1, padx=10, pady=10) 

        self.add_button = tk.Button(self.root, text="Add Event", command=self.add_event) 
        self.add_button.grid(row=4, column=0, columnspan=2, pady=20) 

    def add_event(self): 
        organizer = self.org_entry.get() 
        name = self.name_entry.get() 
        time = self.time_entry.get() 
        date = self.date_entry.get() 

        try: 
            with sqlite3.connect("events.db") as conn: 
                conn.execute('INSERT INTO events (organizer, name, time, date) VALUES (?, ?, ?, ?)', 
                             (organizer, name, time, date)) 
            messagebox.showinfo("Success", "Event added successfully.") 
            self.refresh_callback() 
            self.root.destroy() 
        except Exception as e: 
            messagebox.showerror("Error", f"Failed to add event: {e}") 





class EditEvent:
    def __init__(self, root, refresh_callback, event_data, event_id):
        self.root = root
        self.refresh_callback = refresh_callback
        self.event_id = event_id  # Store as integer for consistency
        self.root.title("Edit Event")
        self.root.geometry("400x300")

        # Event Organizer
        self.org_label = tk.Label(self.root, text="Event Organizer:")
        self.org_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.org_entry = tk.Entry(self.root, width=30)
        self.org_entry.grid(row=0, column=1, padx=10, pady=10)
        self.org_entry.insert(0, event_data[1])

        # Event Name
        self.name_label = tk.Label(self.root, text="Event Name:")
        self.name_label.grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.name_entry = tk.Entry(self.root, width=30)
        self.name_entry.grid(row=1, column=1, padx=10, pady=10)
        self.name_entry.insert(0, event_data[2])

        # Event Time
        self.time_label = tk.Label(self.root, text="Event Time:")
        self.time_label.grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.time_entry = tk.Entry(self.root, width=30)
        self.time_entry.grid(row=2, column=1, padx=10, pady=10)
        self.time_entry.insert(0, event_data[3])

        # Event Date
        self.date_label = tk.Label(self.root, text="Event Date:")
        self.date_label.grid(row=3, column=0, padx=10, pady=10, sticky='w')
        self.date_entry = tk.Entry(self.root, width=30)
        self.date_entry.grid(row=3, column=1, padx=10, pady=10)
        self.date_entry.insert(0, event_data[4])

        # Edit Button
        self.edit_button = tk.Button(self.root, text="Edit Event", command=self.edit_event)
        self.edit_button.grid(row=4, column=0, columnspan=2, pady=20)

    def edit_event(self):
        organizer = self.org_entry.get()
        name = self.name_entry.get()
        time = self.time_entry.get()
        date = self.date_entry.get()

        try:
            print(f"Editing event with ID: {self.event_id}")

            with sqlite3.connect("events.db") as conn:
                conn.execute('''UPDATE events SET organizer=?, name=?, time=?, date=? WHERE id=?''',
                             (organizer, name, time, date, self.event_id))
                conn.commit()
            messagebox.showinfo("Success", "Event updated successfully.")
            self.refresh_callback()
            self.root.destroy()

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to update event with ID {self.event_id}: {e}")





class LoginPage: 
    def __init__(self, root): 
        self.root = root 
        self.root.title("Login Page") 
        self.root.geometry("300x250") 

        self.username_label = tk.Label(self.root, text="Username:") 
        self.username_label.pack(pady=10) 
        self.username_entry = tk.Entry(self.root) 
        self.username_entry.pack() 

        self.password_label = tk.Label(self.root, text="Password:") 
        self.password_label.pack(pady=10) 
        self.password_entry = tk.Entry(self.root, show='*') 
        self.password_entry.pack() 

        self.login_button = tk.Button(self.root, text="Login", command=self.login_user) 
        self.login_button.pack(pady=20) 

        self.register_button = tk.Button(self.root, text="Register", command=self.open_registration) 
        self.register_button.pack() 

        self.auth = UserAuthentication() 

    def login_user(self): 
        username = self.username_entry.get() 
        password = self.password_entry.get() 
        message = self.auth.login(username, password) 

        if message == "Login successful": 
            self.root.destroy() 
            root = tk.Tk() 
            UserDashboard(root, username) 
            root.mainloop() 
        if message == "Login admin successful": 
            self.root.destroy() 
            root = tk.Tk() 
            AdminDashboard(root, username) 
            root.mainloop() 

    def open_registration(self): 
        registration_window = tk.Toplevel(self.root) 
        RegistrationPage(registration_window, self.auth) 

class RegistrationPage: 
    def __init__(self, root, auth): 
        self.root = root 
        self.auth = auth 
        self.root.title("Registration Page") 
        self.root.geometry("300x300") 
        self.username_label = tk.Label(self.root, text="Username:") 
        self.username_label.pack(pady=10) 
        self.username_entry = tk.Entry(self.root) 
        self.username_entry.pack() 

        self.password_label = tk.Label(self.root, text="Password:") 
        self.password_label.pack(pady=10) 
        self.password_entry = tk.Entry(self.root, show='*') 
        self.password_entry.pack() 

        self.register_button = tk.Button(self.root, text="Register", command=self.register) 
        self.register_button.pack(pady=20) 

    def register(self): 
        username = self.username_entry.get() 
        password = self.password_entry.get() 
        message = self.auth.register(username, password) 
        messagebox.showinfo("Registration", message) 
        self.root.destroy() 

if __name__ == "__main__":  
    root = tk.Tk() 
    LoginPage(root) 
    root.mainloop() 
