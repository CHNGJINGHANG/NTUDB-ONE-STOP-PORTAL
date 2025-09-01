import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import io
import csv

# --- DATA MANAGER ---
class DataManager:
    def __init__(self, filename="portal_data.json"):
        self.filename = filename
        self.data = self.load_data()
    
    def load_data(self) -> Dict:
        """Load data from JSON file or create default structure"""
        if Path(self.filename).exists():
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    # Ensure all required keys exist
                    default_structure = {
                        "passwords": {"APH": "NTUDB#247365"},
                        "resources": {"APH": [], "Junior": [], "Senior": []},
                        "members": {"APH": ["admin"], "Junior": [], "Senior": []},
                        "user_progress": {"APH": {}, "Junior": {}, "Senior": {}},
                        "custom_deadlines": {}
                    }
                    for key, value in default_structure.items():
                        if key not in data:
                            data[key] = value
                    return data
            except (json.JSONDecodeError, IOError):
                pass
        
        # Default structure
        return {
            "passwords": {"APH": "NTUDB#1314998"},
            "resources": {"APH": [], "Junior": [], "Senior": []},
            "members": {"APH": ["admin"], "Junior": [], "Senior": []},
            "user_progress": {"APH": {}, "Junior": {}, "Senior": {}},
            "custom_deadlines": {}
        }
    
    def save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
        except IOError as e:
            st.error(f"Failed to save data: {e}")
    
    def add_portal(self, role: str, password: str):
        """Add a new portal/role"""
        self.data["passwords"][role] = password
        self.data["resources"][role] = []
        self.data["members"][role] = []
        self.data["user_progress"][role] = {}
        self.save_data()
    
    def remove_portal(self, role: str):
        """Remove a portal/role completely"""
        if role in self.data["passwords"] and role != "APH":
            del self.data["passwords"][role]
            if role in self.data["resources"]:
                del self.data["resources"][role]
            if role in self.data["members"]:
                del self.data["members"][role]
            if role in self.data["user_progress"]:
                del self.data["user_progress"][role]
            # Remove custom deadlines for this role
            keys_to_remove = [k for k in self.data["custom_deadlines"].keys() if k.startswith(f"{role}_")]
            for key in keys_to_remove:
                del self.data["custom_deadlines"][key]
            self.save_data()
    
    def add_member(self, role: str, name: str, save: bool = True):
        """Add a member to a role"""
        if name not in self.data["members"][role]:
            self.data["members"][role].append(name)
            self.data["user_progress"][role][name] = {}
            
            # Set all existing resources to "Pending" for this new member
            for resource in self.data["resources"][role]:
                self.data["user_progress"][role][name][resource["name"]] = "Pending"
            
            if save:
                self.save_data()
    
    def remove_member(self, role: str, name: str, save: bool = True):
        """Remove a member from a role"""
        if name in self.data["members"][role]:
            self.data["members"][role].remove(name)
            if name in self.data["user_progress"][role]:
                del self.data["user_progress"][role][name]
            
            if save:
                self.save_data()
    
    def add_resource(self, role: str, item_name: str, url: str, desc: str, priority: str, deadline: str):
        """Add a resource to a role"""
        resource = {
            "name": item_name,
            "url": url,
            "description": desc,
            "priority": priority.lower(),
            "deadline": deadline
        }
        
        self.data["resources"][role].append(resource)
        
        # Add this resource as "Pending" for all existing members in this role
        for member in self.data["members"][role]:
            self.data["user_progress"][role][member][item_name] = "Pending"
        
        self.save_data()
    
    def remove_resource(self, role: str, item_name: str):
        """Remove a resource from a role"""
        self.data["resources"][role] = [r for r in self.data["resources"][role] if r["name"] != item_name]
        
        # Remove from all members' progress
        for member in self.data["members"][role]:
            if item_name in self.data["user_progress"][role][member]:
                del self.data["user_progress"][role][member][item_name]
        
        self.save_data()
    
    def update_progress(self, role: str, name: str, item_name: str, new_status: str):
        """Update progress status for a user"""
        if role in self.data["user_progress"] and name in self.data["user_progress"][role]:
            self.data["user_progress"][role][name][item_name] = new_status
            self.save_data()
    
    def get_effective_deadline(self, role: str, item_name: str) -> Optional[str]:
        """Get effective deadline (custom or default)"""
        item_key = f"{role}_{item_name}"
        if item_key in self.data["custom_deadlines"]:
            return self.data["custom_deadlines"][item_key]
        
        for resource in self.data["resources"][role]:
            if resource["name"] == item_name:
                return resource["deadline"]
        return None
    
    def update_deadline(self, role: str, item_name: str, new_deadline: str):
        """Update deadline for a specific item"""
        item_key = f"{role}_{item_name}"
        self.data["custom_deadlines"][item_key] = new_deadline
        self.save_data()

# --- BULK TEXT INPUT FUNCTIONS ---
def parse_bulk_text_members(text_input: str, default_role: str = None) -> List[str]:
    """Parse bulk text input and extract member names"""
    if not text_input.strip():
        return []
    
    members = []
    lines = text_input.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line contains role specification (e.g., "Junior: Alice" or "Alice")
        if ':' in line and default_role is None:
            # Extract name after colon
            name = line.split(':', 1)[1].strip()
        else:
            # Use entire line as name
            name = line
        
        if name and name not in members:  # Avoid duplicates
            members.append(name)
    
    return members

def sync_members_from_text(data_manager: DataManager, role: str, new_members: List[str]):
    """Sync members from text input while preserving progress"""
    if role not in data_manager.data["members"]:
        return False
    
    old_members = set(data_manager.data["members"][role])
    new_members_set = set(new_members)
    
    # Add new members
    for member in new_members_set - old_members:
        data_manager.add_member(role, member, save=False)
    
    # Remove old members
    for member in old_members - new_members_set:
        data_manager.remove_member(role, member, save=False)
    
    # Update order to match input
    data_manager.data["members"][role] = new_members
    data_manager.save_data()
    
    return True

# --- AUTHENTICATION ---
def authenticate_user(password: str, data_manager: DataManager) -> Optional[str]:
    """Authenticate user and return role"""
    for role, pw in data_manager.data["passwords"].items():
        if password == pw:
            return role
    return None

def init_session_state():
    """Initialize session state variables"""
    if "role" not in st.session_state:
        st.session_state.role = None
    if "name" not in st.session_state:
        st.session_state.name = None
    if "data_manager" not in st.session_state:
        st.session_state.data_manager = DataManager()

# --- UI COMPONENTS ---
def render_login_page():
    """Render the login page"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>🐉 Dragonboat Team Portal</h1>
        <p style="font-size: 1.2rem; color: #666;">Secure team resource management system</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔒 Team Member Login")
        
        password = st.text_input(
            "Enter your team password", 
            type="password", 
            placeholder="Password"
        )
        
        if st.button("Login", type="primary", use_container_width=True):
            if password:
                role = authenticate_user(password, st.session_state.data_manager)
                if role:
                    st.session_state.role = role
                    st.success(f"✅ Welcome to the {role} Portal!")
                    st.rerun()
                else:
                    st.error("❌ Invalid password. Please try again.")
            else:
                st.warning("Please enter a password.")

def render_name_selection():
    """Render name selection for non-APH users"""
    data_manager = st.session_state.data_manager
    role = st.session_state.role
    members = data_manager.data["members"][role]
    
    if not members:
        st.warning(f"No members found for {role} team. Contact administrator.")
        return
    
    st.markdown(f"### Welcome to {role} Portal")
    st.write("Please select your name to continue:")
    
    selected_name = st.selectbox("Select your name:", members)
    
    if st.button("Continue", type="primary"):
        st.session_state.name = selected_name
        st.rerun()

def render_resource_card(resource: Dict, index: int):
    """Render an individual resource card"""
    data_manager = st.session_state.data_manager
    role = st.session_state.role
    name = st.session_state.name
    
    priority_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    priority_emoji = priority_colors.get(resource.get("priority", "low"), "⚪")
    
    st.markdown(f"#### {priority_emoji} {resource['name']}")
    st.write(resource.get("description", "No description available"))
    
    # Deadline warning
    deadline = data_manager.get_effective_deadline(role, resource["name"])
    if deadline:
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            days_left = (deadline_date - datetime.now()).days
            
            if days_left < 0:
                st.error(f"⚠️ OVERDUE by {abs(days_left)} days (Deadline: {deadline})")
            elif days_left <= 3:
                st.warning(f"⏰ Due in {days_left} days (Deadline: {deadline})")
            else:
                st.info(f"📅 Deadline: {deadline} ({days_left} days remaining)")
        except ValueError:
            st.info(f"📅 Deadline: {deadline}")
    
    # Resource link
    if resource.get("url"):
        st.markdown(f"[📂 Open {resource['name']} ↗]({resource['url']})")
    
    # Status and completion button
    current_status = data_manager.data["user_progress"][role][name].get(resource["name"], "Pending")
    
    if current_status == "Completed":
        st.success("✅ Completed")
    else:
        if st.button(f"Mark as Completed", key=f"complete_{index}", type="primary"):
            data_manager.update_progress(role, name, resource["name"], "Completed")
            st.success(f"✅ {resource['name']} marked as completed!")
            st.rerun()
    
    st.markdown("---")

def render_member_management_tab(data_manager: DataManager):
    """Render the updated member management tab with bulk text input"""
    st.markdown("### 👥 Member Management")
    st.write("Manage team members using bulk text input.")
    
    available_roles = [role for role in data_manager.data["passwords"].keys() if role != "APH"]
    
    if not available_roles:
        st.info("No team portals available. Create a portal first.")
        return
    
    # Bulk text input for each role
    st.markdown("#### ✏️ Bulk Member Update")
    st.write("Enter member names (one per line) for each team:")
    
    member_updates = {}
    
    for role in available_roles:
        st.markdown(f"**{role} Team**")
        
        # Show current members as placeholder text
        current_members = data_manager.data["members"][role]
        placeholder_text = "\n".join(current_members) if current_members else "Enter member names, one per line"
        
        # Text area for bulk input
        text_input = st.text_area(
            f"Members for {role}",
            value="\n".join(current_members),
            height=150,
            placeholder=placeholder_text,
            key=f"members_text_{role}",
            help="Enter one member name per line. Empty lines will be ignored."
        )
        
        # Parse and preview changes
        new_members = parse_bulk_text_members(text_input)
        member_updates[role] = new_members
        
        # Show preview of changes
        if new_members != current_members:
            current_set = set(current_members)
            new_set = set(new_members)
            
            col1, col2 = st.columns(2)
            
            with col1:
                added = new_set - current_set
                if added:
                    st.success(f"➕ Adding: {', '.join(sorted(added))}")
            
            with col2:
                removed = current_set - new_set
                if removed:
                    st.warning(f"➖ Removing: {', '.join(sorted(removed))}")
            
            if not added and not removed:
                st.info("✅ No changes (order may have changed)")
        
        st.write(f"Current: {len(current_members)} → New: {len(new_members)} members")
        st.markdown("---")
    
    # Update button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🔄 Update All Members", type="primary", use_container_width=True):
            updated_roles = []
            
            for role, new_members in member_updates.items():
                if sync_members_from_text(data_manager, role, new_members):
                    updated_roles.append(role)
            
            if updated_roles:
                st.success(f"🎉 Successfully updated members for: {', '.join(updated_roles)}")
                st.rerun()
            else:
                st.error("Failed to update members")
    
    # Current members overview
    st.markdown("#### 👥 Current Members Overview")
    
    for role in available_roles:
        members = data_manager.data["members"][role]
        if members:
            st.write(f"**{role}**: {', '.join(members)} ({len(members)} members)")
        else:
            st.write(f"**{role}**: No members")

def render_aph_dashboard():
    """Render the APH admin dashboard"""
    data_manager = st.session_state.data_manager
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #8b0000, #dc143c); 
                color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
        <h1>🛡️ APH Admin Portal</h1>
        <p>Administrative Portal Handler - Team Management Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Portal Management", "Member Management", "Task Management", "Deadline Management", "Data Export"])
    
    # Portal Management Tab
    with tab1:
        st.markdown("### 🚪 Portal Management")
        
        col1, col2 = st.columns(2)
        
        # Add Portal Form
        with col1:
            st.markdown("#### ➕ Add New Portal")
            with st.form("add_portal_form"):
                new_portal_name = st.text_input("Portal Name", placeholder="e.g., Advanced Team")
                new_password = st.text_input("Password", type="password", placeholder="Enter secure password")
                
                if st.form_submit_button("Add Portal", type="primary"):
                    if new_portal_name and new_password:
                        if new_portal_name not in data_manager.data["passwords"]:
                            data_manager.add_portal(new_portal_name, new_password)
                            st.success(f"✅ Portal '{new_portal_name}' created successfully!")
                            st.rerun()
                        else:
                            st.error("Portal name already exists!")
                    else:
                        st.error("Please fill in all fields.")
        
        # Remove Portal Form
        with col2:
            st.markdown("#### ➖ Remove Portal")
            available_portals = [role for role in data_manager.data["passwords"].keys() if role != "APH"]
            
            if available_portals:
                with st.form("remove_portal_form"):
                    portal_to_remove = st.selectbox("Select Portal to Remove", available_portals)
                    confirm_removal = st.checkbox("I confirm I want to remove this portal and ALL its data")
                    
                    if st.form_submit_button("Remove Portal", type="secondary"):
                        if confirm_removal:
                            data_manager.remove_portal(portal_to_remove)
                            st.success(f"✅ Portal '{portal_to_remove}' removed successfully!")
                            st.rerun()
                        else:
                            st.error("Please confirm the removal by checking the checkbox.")
            else:
                st.info("No portals available to remove.")
        
        # Show existing portals
        st.markdown("#### 📊 Existing Portals")
        for role in data_manager.data["passwords"].keys():
            if role != "APH":
                member_count = len(data_manager.data["members"][role])
                resource_count = len(data_manager.data["resources"][role])
                st.write(f"**{role}** - {member_count} members, {resource_count} tasks")
    
    # Member Management Tab (Bulk Text Input)
    with tab2:
        render_member_management_tab(data_manager)
    
    # Task Management Tab
    with tab3:
        st.markdown("### 📋 Task Management")
        
        available_roles = [role for role in data_manager.data["passwords"].keys() if role != "APH"]
        
        if available_roles:
            col1, col2 = st.columns(2)
            
            # Add Task Form
            with col1:
                st.markdown("#### ➕ Add Task")
                with st.form("add_task_form"):
                    role = st.selectbox("Portal", available_roles)
                    item_name = st.text_input("Task Name")
                    url = st.text_input("URL")
                    description = st.text_area("Description")
                    priority = st.selectbox("Priority", ["Low", "Medium", "High"])
                    deadline = st.date_input("Deadline", value=datetime.now().date())
                    
                    if st.form_submit_button("Add Task", type="primary"):
                        if item_name and url and description:
                            data_manager.add_resource(
                                role, item_name, url, description, 
                                priority, deadline.strftime("%Y-%m-%d")
                            )
                            st.success(f"✅ Task '{item_name}' added to {role}!")
                            st.rerun()
                        else:
                            st.error("Please fill in all required fields.")
            
            # Remove Task Form
            with col2:
                st.markdown("#### ➖ Remove Task")
                with st.form("remove_task_form"):
                    role_remove = st.selectbox("Portal", available_roles, key="remove_role")
                    
                    # Get resources for selected role
                    resources = data_manager.data["resources"][role_remove]
                    resource_names = [r["name"] for r in resources]
                    
                    if resource_names:
                        item_name_remove = st.selectbox("Task", resource_names)
                        
                        if st.form_submit_button("Remove Task", type="secondary"):
                            data_manager.remove_resource(role_remove, item_name_remove)
                            st.success(f"✅ Task '{item_name_remove}' removed!")
                            st.rerun()
                    else:
                        st.write("No tasks available for this portal.")
            
            # Show current tasks
            st.markdown("#### 📊 Current Tasks Overview")
            for role in available_roles:
                resources = data_manager.data["resources"][role]
                if resources:
                    st.write(f"**{role} Team ({len(resources)} tasks):**")
                    for resource in resources:
                        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(resource.get("priority", "low"), "⚪")
                        st.write(f"  {priority_emoji} {resource['name']} - Due: {resource['deadline']}")
                else:
                    st.write(f"**{role} Team**: No tasks assigned")
        else:
            st.info("No team portals available. Create a portal first.")
    
    # Deadline Management Tab
    with tab4:
        st.markdown("### ⏰ Deadline Management")
        st.write("Manage custom deadlines for tasks.")
        
        for role in [r for r in data_manager.data["passwords"].keys() if r != "APH"]:
            resources = data_manager.data["resources"][role]
            if resources:
                st.markdown(f"#### {role} Team")
                for resource in resources:
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(resource.get("priority", "low"), "⚪")
                        st.write(f"{priority_emoji} **{resource['name']}**")
                    
                    with col2:
                        current_deadline = data_manager.get_effective_deadline(role, resource["name"])
                        default_date = datetime.strptime(current_deadline, "%Y-%m-%d").date() if current_deadline else datetime.now().date()
                        
                        new_date = st.date_input(
                            "Deadline",
                            value=default_date,
                            key=f"deadline_{role}_{resource['name']}",
                            label_visibility="collapsed"
                        )
                    
                    with col3:
                        if st.button("Set", key=f"set_deadline_{role}_{resource['name']}"):
                            data_manager.update_deadline(role, resource["name"], new_date.strftime("%Y-%m-%d"))
                            st.success("Updated!")
                            st.rerun()
    
    # Data Export Tab
    with tab5:
        st.markdown("### 📊 Data Export")
        st.write("Export current member lists and system data.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📥 Export Member Lists")
            if st.button("📄 Generate Current Members CSV"):
                # Create CSV with current members
                current_members = {}
                for role in data_manager.data["members"]:
                    if role != "APH" and data_manager.data["members"][role]:
                        current_members[role] = data_manager.data["members"][role]
                
                if current_members:
                    # Create CSV
                    output = io.StringIO()
                    
                    # Find max length for padding
                    max_len = max(len(members) for members in current_members.values())
                    
                    # Pad all lists to same length
                    for role in current_members:
                        while len(current_members[role]) < max_len:
                            current_members[role].append('')
                    
                    # Write CSV
                    writer = csv.writer(output)
                    writer.writerow(current_members.keys())  # Headers
                    for i in range(max_len):
                        row = [current_members[role][i] for role in current_members.keys()]
                        writer.writerow(row)
                    
                    st.download_button(
                        label="📥 Download Current Members CSV",
                        data=output.getvalue(),
                        file_name=f"current_members_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No members to export.")
        
        with col2:
            st.markdown("#### 🗃️ Export System Data")
            if st.button("📊 Generate JSON Backup"):
                json_str = json.dumps(data_manager.data, indent=2, default=str)
                st.download_button(
                    label="📥 Download JSON Backup",
                    data=json_str,
                    file_name=f"portal_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )

def render_team_dashboard():
    """Render team member dashboard"""
    data_manager = st.session_state.data_manager
    role = st.session_state.role
    name = st.session_state.name
    
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1f4e79, #2e86de); 
                color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
        <h1>🐉 {role} Portal</h1>
        <p>Welcome, {name}!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get user's progress
    user_progress = data_manager.data["user_progress"][role].get(name, {})
    resources = data_manager.data["resources"][role]
    
    # Calculate stats
    completed_count = len([status for status in user_progress.values() if status == "Completed"])
    total_count = len(resources)
    pending_count = total_count - completed_count
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Tasks", total_count)
    with col2:
        st.metric("✅ Completed", completed_count)
    with col3:
        st.metric("⏳ Pending", pending_count)
    
    if not resources:
        st.info("No tasks available yet. Contact your administrator.")
        return
    
    # Resource tabs
    pending_resources = [r for r in resources if user_progress.get(r["name"], "Pending") == "Pending"]
    completed_resources = [r for r in resources if user_progress.get(r["name"], "Pending") == "Completed"]
    
    tab1, tab2 = st.tabs([f"Pending ({len(pending_resources)})", f"Completed ({len(completed_resources)})"])
    
    with tab1:
        if pending_resources:
            for i, resource in enumerate(pending_resources):
                render_resource_card(resource, i)
        else:
            st.success("🎉 All tasks completed!")
    
    with tab2:
        if completed_resources:
            for resource in completed_resources:
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(resource.get("priority", "low"), "⚪")
                st.markdown(f"### ✅ {priority_emoji} {resource['name']}")
                st.write(resource.get("description", ""))
                if resource.get("url"):
                    st.markdown(f"[📂 Open {resource['name']} ↗]({resource['url']})")
                st.markdown("---")
        else:
            st.info("No completed tasks yet.")

def render_dashboard():
    """Render the appropriate dashboard"""
    role = st.session_state.role
    
    if role == "APH":
        render_aph_dashboard()
    else:
        if st.session_state.name is None:
            render_name_selection()
        else:
            render_team_dashboard()

# --- MAIN APPLICATION ---
def main():
    st.set_page_config(
        page_title="Dragonboat Team Portal",
        page_icon="🐉",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .stApp > header {visibility: hidden;}
    .stDeployButton {display: none;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    init_session_state()
    
    if st.session_state.role is None:
        render_login_page()
    else:
        render_dashboard()
    
    # Footer
    if st.session_state.role is not None:
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("<small>🐉 Dragonboat Team Portal v4.0 - Bulk Text Input Edition</small>", unsafe_allow_html=True)
        
        with col2:
            if st.button("🔓 Logout"):
                st.session_state.clear()
                st.rerun()

if __name__ == "__main__":
    main()

