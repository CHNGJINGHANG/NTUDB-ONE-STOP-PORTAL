🐉 Dragonboat Team Portal
This is a Streamlit application designed to be a centralized portal for a dragonboat team to manage members, share resources, track progress, and handle deadlines. It provides a secure, role-based system for team administrators and members.

Key Features
🔒 Secure Access:

A password-protected login system for different team roles (e.g., APH, Junior, Senior).

🛡️ APH Admin Dashboard:

Portal Management: Create and remove team-specific portals with unique passwords.

Member Management: Add, remove, and sync member lists using a bulk text input feature for quick updates.

Task Management: Add new resources and tasks with descriptions, URLs, priorities, and deadlines.

Deadline Management: Adjust and set custom deadlines for specific tasks.

Data Export: Export member lists as a CSV file and a complete system data backup as a JSON file.

📋 Team Member Portal:

Personalized Dashboard: After logging in and selecting their name, members see their own dashboard.

Task Tracking: View a list of assigned tasks with their priority and deadline.

Progress Updates: Easily mark tasks as "Completed" to track their progress.

Resource Access: Click links to open resources directly from the portal.

How to Run the App
Dependencies: Ensure you have Python installed. The app requires streamlit, pandas, and other standard libraries. You can install them using pip:

pip install streamlit pandas

Save the file: Save the provided App.py file to your local machine.

Run the app: Open your terminal or command prompt, navigate to the directory where you saved the file, and run the following command:

streamlit run App.py

Access the Portal: The app will automatically open in your web browser. Use the password "NTUDB#1314998" to log in to the "APH" admin portal and begin setting up your team's data.

Data Management
The application uses a local portal_data.json file to store all data, including passwords, member lists, resources, and progress. This file is automatically created and updated by the app.
