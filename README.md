# 🐉 Dragonboat Team Portal

This is a **Streamlit application** designed as a centralized portal for a dragonboat team to manage members, share resources, track progress, and handle deadlines. It provides a secure, role-based system for team administrators and members.

---

## Key Features

### 🔒 Secure Access
- Password-protected login system for different team roles (e.g., **APH**, **Junior**, **Senior**).

### 🛡️ APH Admin Dashboard
- **Portal Management**: Create and remove team-specific portals with unique passwords.  
- **Member Management**: Add, remove, and sync member lists using a **bulk text input** feature for quick updates.  
- **Task Management**: Add new resources and tasks with descriptions, URLs, priorities, and deadlines.  
- **Deadline Management**: Adjust and set custom deadlines for specific tasks.  
- **Data Export**: Export member lists as a **CSV file** and a complete system **JSON backup**.

### 📋 Team Member Portal
- **Personalized Dashboard**: Members see a dashboard specific to their name after login.  
- **Task Tracking**: View a list of assigned tasks with priority and deadline.  
- **Progress Updates**: Easily mark tasks as **Completed** to track progress.  
- **Resource Access**: Click links to open resources directly from the portal.

---

## How to Run the App

### Dependencies
Ensure you have Python installed. The app requires **Streamlit**, **pandas**, and other standard libraries. Install them with:

```bash
pip install streamlit pandas
