import cv2
import os
import numpy as np
import pickle
import datetime
import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk

class SmartVotingSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Online Voting System")
        self.root.geometry("800x600")
        
        # Initialize database
        self.init_database()
        
        # Initialize face detection and recognition
        self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        # Load face recognition model if exists
        if os.path.exists('face_model.yml'):
            self.face_recognizer.read('face_model.yml')
            with open('face_labels.pkl', 'rb') as f:
                self.face_labels = pickle.load(f)
        else:
            self.face_labels = {}
        
        # Current user
        self.current_user = None
        
        # Create UI
        self.create_ui()
    
    def init_database(self):
        # Connect to database
        self.conn = sqlite3.connect('voting_system.db')
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            voter_id TEXT UNIQUE NOT NULL
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            position TEXT NOT NULL
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY,
            voter_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            position TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (voter_id) REFERENCES users (id),
            FOREIGN KEY (candidate_id) REFERENCES candidates (id),
            UNIQUE(voter_id, position)
        )
        ''')
        
        # Insert sample candidates if none exist
        self.cursor.execute("SELECT COUNT(*) FROM candidates")
        if self.cursor.fetchone()[0] == 0:
            sample_candidates = [
                ("John Doe", "President"),
                ("Jane Smith", "President"),
                ("Mike Johnson", "Vice President"),
                ("Sarah Williams", "Vice President")
            ]
            self.cursor.executemany("INSERT INTO candidates (name, position) VALUES (?, ?)", 
                                   sample_candidates)
        
        self.conn.commit()
    
    def create_ui(self):
        # Main frame
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(self.main_frame, text="Smart Online Voting System", 
                              font=("Arial", 24, "bold"), bg="#f0f0f0")
        title_label.pack(pady=20)
        
        # Buttons frame
        button_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        button_frame.pack(pady=30)
        
        # Register button
        register_btn = tk.Button(button_frame, text="Register Voter", font=("Arial", 14),
                               command=self.register_voter, width=15, bg="#4CAF50", fg="white")
        register_btn.grid(row=0, column=0, padx=10, pady=10)
        
        # Login button
        login_btn = tk.Button(button_frame, text="Voter Login", font=("Arial", 14),
                            command=self.voter_login, width=15, bg="#2196F3", fg="white")
        login_btn.grid(row=0, column=1, padx=10, pady=10)
        
        # Admin button
        admin_btn = tk.Button(button_frame, text="Admin Panel", font=("Arial", 14),
                            command=self.admin_panel, width=15, bg="#FF9800", fg="white")
        admin_btn.grid(row=1, column=0, padx=10, pady=10)
        
        # Exit button
        exit_btn = tk.Button(button_frame, text="Exit", font=("Arial", 14),
                           command=self.root.quit, width=15, bg="#f44336", fg="white")
        exit_btn.grid(row=1, column=1, padx=10, pady=10)
        
        # Status label
        self.status_label = tk.Label(self.main_frame, text="Welcome to Smart Voting System", 
                                   font=("Arial", 12), bg="#f0f0f0")
        self.status_label.pack(pady=20)
        
        # Camera feed frame (initially hidden)
        self.camera_frame = tk.Label(self.main_frame)
        self.camera_frame.pack_forget()
        
        # Voting frame (initially hidden)
        self.voting_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.voting_frame.pack_forget()
    
    def register_voter(self):
        # Ask for voter details
        voter_name = simpledialog.askstring("Register Voter", "Enter your full name:")
        if not voter_name:
            return
        
        voter_id = simpledialog.askstring("Register Voter", "Enter your voter ID number:")
        if not voter_id:
            return
        
        # Check if voter ID already exists
        self.cursor.execute("SELECT * FROM users WHERE voter_id = ?", (voter_id,))
        if self.cursor.fetchone():
            messagebox.showerror("Error", "Voter ID already registered!")
            return
        
        # Start camera to capture face
        self.register_mode = True
        self.temp_voter_name = voter_name
        self.temp_voter_id = voter_id
        self.captured_faces = []
        
        self.status_label.config(text="Please look at the camera. Capturing face samples...")
        
        # Open camera
        self.open_camera()
    
    def voter_login(self):
        # Start camera for face recognition
        self.register_mode = False
        self.status_label.config(text="Looking for your face... Please look at the camera")
        
        # Open camera
        self.open_camera()
    
    def admin_panel(self):
        # Simple admin authentication
        password = simpledialog.askstring("Admin Login", "Enter admin password:", show='*')
        if password != "admin123":  # Simple password for demo purposes
            messagebox.showerror("Error", "Invalid admin password!")
            return
        
        # Create admin window
        admin_window = tk.Toplevel(self.root)
        admin_window.title("Admin Panel")
        admin_window.geometry("600x500")
        
        # Add candidates frame
        add_frame = tk.LabelFrame(admin_window, text="Add Candidate", font=("Arial", 12))
        add_frame.pack(padx=10, pady=10, fill="x")
        
        tk.Label(add_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        name_entry = tk.Entry(add_frame, width=30)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(add_frame, text="Position:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        position_entry = tk.Entry(add_frame, width=30)
        position_entry.grid(row=1, column=1, padx=5, pady=5)
        
        def add_candidate():
            name = name_entry.get().strip()
            position = position_entry.get().strip()
            if name and position:
                self.cursor.execute("INSERT INTO candidates (name, position) VALUES (?, ?)", 
                                   (name, position))
                self.conn.commit()
                messagebox.showinfo("Success", "Candidate added successfully!")
                name_entry.delete(0, tk.END)
                position_entry.delete(0, tk.END)
                refresh_results()
            else:
                messagebox.showerror("Error", "Please fill all fields!")
        
        add_button = tk.Button(add_frame, text="Add Candidate", command=add_candidate)
        add_button.grid(row=2, column=1, pady=10)
        
        # Results frame
        results_frame = tk.LabelFrame(admin_window, text="Election Results", font=("Arial", 12))
        results_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Treeview for results
        results_tree = tk.ttk.Treeview(results_frame)
        results_tree["columns"] = ("Position", "Candidate", "Votes")
        results_tree.column("#0", width=0, stretch=tk.NO)
        results_tree.column("Position", anchor=tk.W, width=120)
        results_tree.column("Candidate", anchor=tk.W, width=200)
        results_tree.column("Votes", anchor=tk.CENTER, width=80)
        
        results_tree.heading("#0", text="")
        results_tree.heading("Position", text="Position")
        results_tree.heading("Candidate", text="Candidate")
        results_tree.heading("Votes", text="Votes")
        
        results_tree.pack(padx=10, pady=10, fill="both", expand=True)
        
        def refresh_results():
            # Clear tree
            for item in results_tree.get_children():
                results_tree.delete(item)
            
            # Get results
            self.cursor.execute("""
            SELECT c.position, c.name, COUNT(v.id) as vote_count
            FROM candidates c
            LEFT JOIN votes v ON c.id = v.candidate_id
            GROUP BY c.id
            ORDER BY c.position, vote_count DESC
            """)
            
            results = self.cursor.fetchall()
            for i, (position, name, votes) in enumerate(results):
                results_tree.insert("", i, values=(position, name, votes))
        
        refresh_button = tk.Button(results_frame, text="Refresh Results", command=refresh_results)
        refresh_button.pack(pady=10)
        
        # Load initial results
        refresh_results()
    
    def open_camera(self):
        # Hide main UI elements
        for widget in self.main_frame.winfo_children():
            widget.pack_forget()
        
        # Show camera frame
        self.camera_frame.pack(padx=10, pady=10)
        self.status_label.pack(pady=10)
        
        # Start camera capture
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open camera!")
            self.show_main_ui()
            return
        
        self.frame_count = 0
        self.update_camera()
    
    def update_camera(self):
        ret, frame = self.cap.read()
        if not ret:
            self.show_main_ui()
            return
        
        # Convert frame to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_detector.detectMultiScale(gray, 1.3, 5)
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            face_roi = gray[y:y+h, x:x+w]
            
            if self.register_mode:
                # In registration mode, capture multiple face samples
                if self.frame_count % 10 == 0 and len(self.captured_faces) < 5:
                    self.captured_faces.append(face_roi.copy())
                    self.status_label.config(text=f"Captured {len(self.captured_faces)}/5 face samples")
                
                # If we have enough samples, register the user
                if len(self.captured_faces) >= 5:
                    self.cap.release()
                    self.register_face_samples()
                    return
            else:
                # In login mode, try to recognize the face
                if self.frame_count % 30 == 0:  # Check every 30 frames
                    self.recognize_face(face_roi)
                    return
        
        # Convert to PIL format for tkinter
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.camera_frame.imgtk = imgtk
        self.camera_frame.configure(image=imgtk)
        
        self.frame_count += 1
        self.camera_frame.after(10, self.update_camera)
    
    def register_face_samples(self):
        # Insert user into database
        self.cursor.execute("INSERT INTO users (name, voter_id) VALUES (?, ?)", 
                           (self.temp_voter_name, self.temp_voter_id))
        self.conn.commit()
        
        # Get user ID for face label
        self.cursor.execute("SELECT id FROM users WHERE voter_id = ?", (self.temp_voter_id,))
        user_id = self.cursor.fetchone()[0]
        
        # Add user to face labels
        self.face_labels[user_id] = self.temp_voter_name
        
        # Train face recognizer with new samples
        faces = []
        labels = []
        
        # Add existing face data if available
        if os.path.exists('face_data.npz'):
            data = np.load('face_data.npz')
            existing_faces = data['faces']
            existing_labels = data['labels']
            faces = list(existing_faces)
            labels = list(existing_labels)
        
        # Add new face samples
        for face in self.captured_faces:
            faces.append(face)
            labels.append(user_id)
        
        # Train recognizer
        self.face_recognizer.train(faces, np.array(labels))
        
        # Save model and labels
        self.face_recognizer.write('face_model.yml')
        with open('face_labels.pkl', 'wb') as f:
            pickle.dump(self.face_labels, f)
        
        # Save face data for future training
        np.savez('face_data.npz', faces=np.array(faces), labels=np.array(labels))
        
        messagebox.showinfo("Success", "Registration successful!")
        self.show_main_ui()
    
    def recognize_face(self, face):
        try:
            label, confidence = self.face_recognizer.predict(face)
            
            # Lower confidence means better match
            if confidence < 80:  # Threshold for recognition
                self.cursor.execute("SELECT * FROM users WHERE id = ?", (label,))
                user = self.cursor.fetchone()
                
                if user:
                    self.current_user = user
                    self.cap.release()
                    messagebox.showinfo("Success", f"Welcome {user[1]}!")
                    self.show_voting_ui()
                    return
        except:
            pass
        
        # If we get here, face wasn't recognized successfully
        self.status_label.config(text="Face not recognized. Please try again...")
        self.camera_frame.after(10, self.update_camera)
    
    def show_main_ui(self):
        # Stop camera if running
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        
        # Clear frames
        for widget in self.main_frame.winfo_children():
            widget.pack_forget()
        
        # Create UI again
        self.create_ui()
    
    def show_voting_ui(self):
        # Clear frames
        for widget in self.main_frame.winfo_children():
            widget.pack_forget()
        
        # Show voting frame
        self.voting_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.voting_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Add welcome message
        welcome_label = tk.Label(self.voting_frame, 
                                text=f"Welcome, {self.current_user[1]}", 
                                font=("Arial", 18, "bold"), bg="#f0f0f0")
        welcome_label.pack(pady=10)
        
        # Get available positions
        self.cursor.execute("SELECT DISTINCT position FROM candidates")
        positions = [row[0] for row in self.cursor.fetchall()]
        
        # Check if user has already voted for any position
        self.cursor.execute("SELECT position FROM votes WHERE voter_id = ?", (self.current_user[0],))
        voted_positions = [row[0] for row in self.cursor.fetchall()]
        
        # Create a frame for each position
        for position in positions:
            position_frame = tk.LabelFrame(self.voting_frame, text=position, font=("Arial", 14))
            position_frame.pack(fill="x", padx=10, pady=10)
            
            # Check if already voted
            if position in voted_positions:
                # Show message that user already voted
                tk.Label(position_frame, text="You have already voted for this position",
                      font=("Arial", 12), fg="blue").pack(pady=10)
                continue
            
            # Get candidates for this position
            self.cursor.execute("SELECT id, name FROM candidates WHERE position = ?", (position,))
            candidates = self.cursor.fetchall()
            
            # Create radio buttons for candidates
            var = tk.IntVar()
            for i, (candidate_id, name) in enumerate(candidates):
                tk.Radiobutton(position_frame, text=name, variable=var, value=candidate_id,
                            font=("Arial", 12)).pack(anchor="w", padx=20, pady=5)
            
            # Add vote button
            def make_vote_func(pos, var):
                return lambda: self.cast_vote(pos, var)
                
            vote_btn = tk.Button(position_frame, text="Cast Vote", 
                              command=make_vote_func(position, var),
                              bg="#4CAF50", fg="white", font=("Arial", 12))
            vote_btn.pack(pady=10)
        
        # Add logout button
        logout_btn = tk.Button(self.voting_frame, text="Logout", 
                            command=self.show_main_ui,
                            bg="#f44336", fg="white", font=("Arial", 12))
        logout_btn.pack(pady=20)
    
    def cast_vote(self, position, var):
        candidate_id = var.get()
        if candidate_id == 0:
            messagebox.showerror("Error", "Please select a candidate")
            return
        
        # Record the vote
        try:
            self.cursor.execute("INSERT INTO votes (voter_id, candidate_id, position) VALUES (?, ?, ?)",
                              (self.current_user[0], candidate_id, position))
            self.conn.commit()
            messagebox.showinfo("Success", "Vote cast successfully!")
            
            # Refresh voting UI to reflect the vote
            self.show_voting_ui()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "You have already voted for this position")
    
    def _del_(self):
        # Close database connection when object is destroyed
        if hasattr(self, 'conn'):
            self.conn.close()
        
        # Release camera if open
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()

if __name__ == "__main__":
    # Create main application window
    root = tk.Tk()
    app = SmartVotingSystem(root)
    root.mainloop()
    
