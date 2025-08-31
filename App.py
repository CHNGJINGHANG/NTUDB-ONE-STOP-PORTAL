import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import os
from typing import Dict, List, Optional

# --- CONFIGURATION ---
class Config:
    # Use environment variables for production
    PASSWORDS = {
        "Junior": os.getenv("JUNIOR_PASSWORD", "dragon_junior_2526"),
        "Senior": os.getenv("SENIOR_PASSWORD", "NTUDB_believer_2526"), 
        "Pull Up Warrior": os.getenv("PULLUP_PASSWORD", "pullup_masterclass25/26"),
        "APH": os.getenv("APH_PASSWORD", "NTUDB#1314998")
    }
    
    SESSION_TIMEOUT = 3600  # 1 hour in seconds
    DATA_FILE = "portal_data.json"
    
    RESOURCES = {
        "Junior": {
            "Junior Water Availability": {
                "url": "https://docs.google.com/spreadsheets/d/1zZ3ZFu_jzM5n0GzNYCtQid8xzoIpIjYhy8dsZ1Qxv_M/edit?usp=sharing",
                "description": "Submit your water training availability for scheduling",
                "priority": "high",
                "deadline": "2024-09-15"
            },
            "Junior Land Availability": {
                "url": "https://docs.google.com/spreadsheets/d/1ichMMo5emFZpHk5dtkLkT6SrXTLrnFbso0i0OB3_BUA/edit?usp=sharing",
                "description": "Submit your land training availability",
                "priority": "high", 
                "deadline": "2024-09-15"
            },
            "Team Bio Data": {
                "url": "https://forms.gle/cEEvVZuoNfjDZwxv5",
                "description": "Complete your team member profile information",
                "priority": "medium",
                "deadline": "2024-09-20"
            },
            "Junior Gym Tracker": {
                "url": "https://docs.google.com/spreadsheets/d/1lSZupGRaA5BjV-15w6HZ5rkLZ1D5VdxlnGA6aWvvJjo/edit?usp=sharing",
                "description": "Track your gym sessions and fitness progress",
                "priority": "medium",
                "deadline": "2024-10-15"
            }
        },
        "Senior": {
            "Senior Land Availability": {
                "url": "https://docs.google.com/spreadsheets/d/1TZSOfJ1KNI71bI5JUI1H_jQsYSIo_E5Gd9Yycf0PeDo/edit?usp=sharing",
                "description": "Submit your land training schedule preferences",
                "priority": "high",
                "deadline": "2024-09-07"
            },
            "Senior Water Availability": {
                "url": "https://docs.google.com/spreadsheets/d/1TVQdxysR-DgHbsEYqEuScdU3HBUJmdjMOyZ7ZpzQz34/edit?usp=sharing", 
                "description": "Submit your water training availability",
                "priority": "high",
                "deadline": "2024-09-07"

            },
            "Senior Gym Tracker": {
                "url": "https://docs.google.com/spreadsheets/d/1FmFI5icuGGF6PISteEWNwTlwumZBtCMpPn9KDCFS2sg/edit?usp=sharing",
                "description": "Track your gym sessions and fitness progress",
                "priority": "medium",
                "deadline": "2024-11-07"
            }
        },
        "Pull Up Warrior": {
            "Pull Up Warrior Tracker": {
                "url": "https://docs.google.com/spreadsheets/d/1NThoRu4GesHcMjlNhe6ND339Oq3Xn4ISZrYZ-k3TzBE/edit?usp=sharing",
                "description": "Track your pull-up progress and goals",
                "priority": "medium",
                "deadline": "2024-11-07"
            }
        }
    }

# --- DATA PERSISTENCE ---
class DataManager:
    @staticmethod
    def load_data() -> Dict:
        """Load persistent data from file"""
        if Path(Config.DATA_FILE).exists():
            try:
                with open(Config.DATA_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"submissions": [], "user_progress": {}}
        return {"submissions": [], "user_progress": {}}
    
    @staticmethod
    def save_data(data: Dict):
        """Save data to file"""
        try:
            with open(Config.DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except IOError as e:
            st.error(f"Failed to save data: {e}")

    @staticmethod
    def log_submission(name: str, role: str, item: str, status: str, notes: str = ""):
        """Log a submission with validation"""
        data = DataManager.load_data()
        
        submission = {
            "timestamp": datetime.now().isoformat(),
            "name": name.strip(),
            "role": role,
            "item": item,
            "status": status,
            "notes": notes.strip(),
            "session_id": st.session_state.get("session_id", "unknown")
        }
        
        data["submissions"].append(submission)
        
        # Update user progress
        user_key = f"{role}_{name}"
        if user_key not in data["user_progress"]:
            data["user_progress"][user_key] = {}
        data["user_progress"][user_key][item] = {
            "status": status,
            "last_updated": datetime.now().isoformat()
        }
        
        DataManager.save_data(data)
        return submission
    
    @staticmethod
    def update_deadline(role: str, item: str, new_deadline: str):
        """Update deadline for a specific item"""
        data = DataManager.load_data()
        
        # Initialize deadlines section if it doesn't exist
        if "custom_deadlines" not in data:
            data["custom_deadlines"] = {}
        
        # Store the custom deadline
        item_key = f"{role}_{item}"
        data["custom_deadlines"][item_key] = new_deadline
        
        DataManager.save_data(data)
        
        # Log the deadline change
        DataManager.log_submission(
            "APH Admin", "APH", f"Deadline Update: {role} - {item}", 
            "Updated", f"New deadline: {new_deadline}"
        )
    
    @staticmethod
    def get_effective_deadline(role: str, item: str) -> Optional[str]:
        """Get the effective deadline (custom if set, otherwise default)"""
        data = DataManager.load_data()
        
        # Check for custom deadline first
        if "custom_deadlines" in data:
            item_key = f"{role}_{item}"
            if item_key in data["custom_deadlines"]:
                return data["custom_deadlines"][item_key]
        
        # Fall back to default deadline
        if role in Config.RESOURCES and item in Config.RESOURCES[role]:
            return Config.RESOURCES[role][item].get("deadline")
        
        return None
    
    @staticmethod
    def get_completion_stats() -> Dict:
        """Get completion statistics for all teams"""
        data = DataManager.load_data()
        stats = {
            "total_submissions": len(data["submissions"]),
            "by_role": {},
            "by_status": {},
            "recent_activity": data["submissions"][-20:] if data["submissions"] else [],
            "user_progress": data["user_progress"]
        }
        
        # Count by role
        for submission in data["submissions"]:
            role = submission["role"]
            if role not in stats["by_role"]:
                stats["by_role"][role] = {"total": 0, "completed": 0, "in_progress": 0}
            stats["by_role"][role]["total"] += 1
            if submission["status"] == "Completed":
                stats["by_role"][role]["completed"] += 1
            elif submission["status"] == "In Progress":
                stats["by_role"][role]["in_progress"] += 1
        
        # Count by status
        for submission in data["submissions"]:
            status = submission["status"]
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
        return stats
    
    @staticmethod
    def get_user_summary() -> Dict:
        """Get summary of all users and their completion status"""
        data = DataManager.load_data()
        user_summary = {}
        
        # Get all possible items for each role
        all_items = {}
        for role, resources in Config.RESOURCES.items():
            if role != "APH":  # Skip APH role
                all_items[role] = list(resources.keys())
        
        # Track user progress
        for user_key, progress in data["user_progress"].items():
            if "_" in user_key:
                role, name = user_key.split("_", 1)
                if role not in user_summary:
                    user_summary[role] = {}
                if name not in user_summary[role]:
                    user_summary[role][name] = {
                        "completed": [],
                        "in_progress": [],
                        "pending": [],
                        "last_activity": None
                    }
                
                for item, item_data in progress.items():
                    if item_data["status"] == "Completed":
                        user_summary[role][name]["completed"].append(item)
                    elif item_data["status"] == "In Progress":
                        user_summary[role][name]["in_progress"].append(item)
                    
                    # Track last activity
                    last_updated = datetime.fromisoformat(item_data["last_updated"])
                    if (user_summary[role][name]["last_activity"] is None or 
                        last_updated > user_summary[role][name]["last_activity"]):
                        user_summary[role][name]["last_activity"] = last_updated
        
        # Add pending items
        for role, users in user_summary.items():
            if role in all_items:
                for name, user_data in users.items():
                    completed = set(user_data["completed"])
                    in_progress = set(user_data["in_progress"])
                    all_role_items = set(all_items[role])
                    user_data["pending"] = list(all_role_items - completed - in_progress)
        
        return user_summary

# --- AUTHENTICATION ---
def authenticate_user(password: str) -> Optional[str]:
    """Authenticate user and return role"""
    for role, pw in Config.PASSWORDS.items():
        if password == pw:
            return role
    return None

def check_session_timeout():
    """Check if session has timed out"""
    if "login_time" in st.session_state:
        elapsed = datetime.now() - st.session_state.login_time
        if elapsed.total_seconds() > Config.SESSION_TIMEOUT:
            st.session_state.clear()
            st.warning("Session expired. Please login again.")
            st.rerun()

def init_session_state():
    """Initialize session state variables"""
    if "role" not in st.session_state:
        st.session_state.role = None
    if "session_id" not in st.session_state:
        st.session_state.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]

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
        with st.container():
            st.markdown("### 🔐 Team Member Login")
            
            password = st.text_input(
                "Enter your team password", 
                type="password", 
                placeholder="Password",
                help="Contact your team coordinator if you've forgotten your password"
            )
            
            login_col1, login_col2 = st.columns([1, 1])
            
            with login_col1:
                if st.button("Login", type="primary", use_container_width=True):
                    if password:
                        role = authenticate_user(password)
                        if role:
                            st.session_state.role = role
                            st.session_state.login_time = datetime.now()
                            st.success(f"✅ Welcome to the {role} Portal!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid password. Please try again.")
                    else:
                        st.warning("Please enter a password.")
            
            with login_col2:
                if st.button("Help", use_container_width=True):
                    st.info("📧 Contact your team coordinator for login assistance")
                    
        # Show available portals
        with st.expander("ℹ️ Available Portals"):
            st.write("**Team Portals:**")
            st.write("• 🐲 Junior Team Portal")
            st.write("• 🐉 Senior Team Portal") 
            st.write("• 💪 Pull Up Warrior Portal")
            st.write("• 🛡️ APH Admin Portal (Administrative access)")
            st.write("")
            st.write("Each portal requires a specific password. Contact your team coordinator for access.")

def render_resource_card(title: str, resource: Dict, index: int):
    """Render an individual resource card"""
    priority_colors = {
        "high": "🔴",
        "medium": "🟡", 
        "low": "🟢"
    }
    
    priority_emoji = priority_colors.get(resource.get("priority", "low"), "⚪")
    
    with st.container():
        st.markdown(f"#### {priority_emoji} {title}")
        st.write(resource.get("description", "No description available"))
        
        # Deadline warning
        deadline = resource.get("deadline")
        # Check for custom deadline override
        effective_deadline = DataManager.get_effective_deadline(st.session_state.role, title)
        if effective_deadline:
            deadline = effective_deadline
            
        if deadline:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            days_left = (deadline_date - datetime.now()).days
            
            if days_left < 0:
                st.error(f"⚠️ OVERDUE by {abs(days_left)} days (Deadline: {deadline})")
            elif days_left <= 3:
                st.warning(f"⏰ Due in {days_left} days (Deadline: {deadline})")
            else:
                st.info(f"📅 Deadline: {deadline} ({days_left} days remaining)")
        
        # Resource link
        if resource.get("url"):
            st.markdown(f"[📂 Open {title} →]({resource['url']})", unsafe_allow_html=True)
        else:
            st.write("📝 " + resource.get("description", "Contact coordinator for details"))
        
        st.markdown("---")
        
        # Submission form
        st.write("**📋 Update Your Status:**")
        
        name = st.text_input(
            "Your Name", 
            key=f"name_{index}",
            placeholder="Enter your full name"
        )
        
        notes = st.text_area(
            "Additional Notes (Optional)", 
            key=f"notes_{index}",
            placeholder="Any comments or questions..."
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(f"✅ Completed", key=f"complete_{index}", type="primary"):
                if name.strip():
                    submission = DataManager.log_submission(
                        name, st.session_state.role, title, "Completed", notes
                    )
                    st.success(f"✅ {title} marked as completed by {name}")
                    st.balloons()
                else:
                    st.error("Please enter your name")
        
        with col2:
            if st.button(f"⏳ In Progress", key=f"progress_{index}"):
                if name.strip():
                    submission = DataManager.log_submission(
                        name, st.session_state.role, title, "In Progress", notes
                    )
                    st.info(f"⏳ {title} marked as in progress by {name}")
                else:
                    st.error("Please enter your name")

def render_aph_dashboard():
    """Render the APH admin dashboard"""
    st.markdown("""
    <div style="background: linear-gradient(90deg, #8b0000, #dc143c); 
                color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
        <h1>🛡️ APH Admin Portal</h1>
        <p>Administrative Portal Handler - Team Oversight Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get statistics
    stats = DataManager.get_completion_stats()
    user_summary = DataManager.get_user_summary()
    
    # Overview metrics
    st.markdown("### 📊 Overview Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔢 Total Submissions", stats["total_submissions"])
    with col2:
        completed = stats["by_status"].get("Completed", 0)
        st.metric("✅ Completed", completed)
    with col3:
        in_progress = stats["by_status"].get("In Progress", 0)
        st.metric("⏳ In Progress", in_progress)
    with col4:
        total_users = sum(len(users) for users in user_summary.values())
        st.metric("👥 Active Users", total_users)
    
    st.markdown("---")
    
    # Team-wise breakdown - FIXED VERSION
    st.markdown("### 🏆 Team Performance")
    
    # Filter out APH role from stats
    team_roles = [role for role in stats["by_role"].keys() if role != "APH"]
    
    if team_roles:  # Only create columns if there are team roles
        team_cols = st.columns(len(team_roles))
        
        for i, role in enumerate(team_roles):
            role_stats = stats["by_role"][role]
            with team_cols[i]:
                completion_rate = (role_stats["completed"] / max(role_stats["total"], 1)) * 100
                st.metric(
                    f"🐉 {role}",
                    f"{completion_rate:.1f}%",
                    f"{role_stats['completed']}/{role_stats['total']} completed"
                )
    else:
        st.info("No team activity data available yet.")
    
    st.markdown("---")
    
    # Detailed user tracking
    st.markdown("### 👥 Individual User Progress")
    
    # Filter options
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        selected_role = st.selectbox(
            "Filter by Team",
            ["All Teams"] + [role for role in user_summary.keys()],
            key="aph_role_filter"
        )
    with filter_col2:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All Status", "Has Pending", "All Complete", "Has In Progress"],
            key="aph_status_filter"
        )
    
    # User progress table
    user_data = []
    for role, users in user_summary.items():
        if selected_role != "All Teams" and role != selected_role:
            continue
            
        for name, progress in users.items():
            completed_count = len(progress["completed"])
            in_progress_count = len(progress["in_progress"])
            pending_count = len(progress["pending"])
            total_items = completed_count + in_progress_count + pending_count
            
            completion_percentage = (completed_count / max(total_items, 1)) * 100
            
            # Apply status filter
            if status_filter == "Has Pending" and pending_count == 0:
                continue
            elif status_filter == "All Complete" and pending_count > 0:
                continue
            elif status_filter == "Has In Progress" and in_progress_count == 0:
                continue
            
            user_data.append({
                "Team": role,
                "Name": name,
                "Completed": completed_count,
                "In Progress": in_progress_count,
                "Pending": pending_count,
                "Completion %": f"{completion_percentage:.1f}%",
                "Last Activity": progress["last_activity"].strftime("%Y-%m-%d %H:%M") if progress["last_activity"] else "Never"
            })
    
    if user_data:
        df = pd.DataFrame(user_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Export functionality
        if st.button("📥 Download Progress Report"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"team_progress_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No users match the selected filters.")
    
    st.markdown("---")
    
    # Detailed item tracking
    st.markdown("### 📋 Item Completion Tracking")
    
    # Show completion rates per item
    item_stats = {}
    data = DataManager.load_data()
    
    for role, resources in Config.RESOURCES.items():
        if role != "APH":
            for item_name in resources.keys():
                item_stats[f"{role} - {item_name}"] = {
                    "completed": 0,
                    "in_progress": 0,
                    "total_users": 0
                }
    
    # Count completions per item
    for user_key, progress in data["user_progress"].items():
        if "_" in user_key:
            role, name = user_key.split("_", 1)
            if role != "APH":
                for item, item_data in progress.items():
                    item_key = f"{role} - {item}"
                    if item_key in item_stats:
                        if item_data["status"] == "Completed":
                            item_stats[item_key]["completed"] += 1
                        elif item_data["status"] == "In Progress":
                            item_stats[item_key]["in_progress"] += 1
    
    # Calculate total users per role for percentage
    role_user_counts = {}
    for role in user_summary.keys():
        role_user_counts[role] = len(user_summary[role])
    
    item_data = []
    for item_key, stats_data in item_stats.items():
        role = item_key.split(" - ")[0]
        item_name = item_key.split(" - ", 1)[1]
        total_users = role_user_counts.get(role, 1)
        
        completion_rate = (stats_data["completed"] / max(total_users, 1)) * 100
        
        item_data.append({
            "Team": role,
            "Item": item_name,
            "Completed": stats_data["completed"],
            "In Progress": stats_data["in_progress"],
            "Total Users": total_users,
            "Completion Rate": f"{completion_rate:.1f}%"
        })
    
    if item_data:
        df_items = pd.DataFrame(item_data)
        st.dataframe(df_items, use_container_width=True, hide_index=True)
    
    # Recent activity feed
    st.markdown("### 📈 Recent Activity Feed")
    if stats["recent_activity"]:
        activity_data = []
        for activity in stats["recent_activity"]:
            activity_data.append({
                "Time": datetime.fromisoformat(activity["timestamp"]).strftime("%Y-%m-%d %H:%M"),
                "Team": activity["role"],
                "Name": activity["name"],
                "Item": activity["item"],
                "Status": activity["status"],
                "Notes": activity.get("notes", "")[:50] + ("..." if len(activity.get("notes", "")) > 50 else "")
            })
        
        df_activity = pd.DataFrame(activity_data)
        st.dataframe(df_activity, use_container_width=True, hide_index=True)
    else:
        st.info("No recent activity to display.")
    
    # Data management section
    st.markdown("---")
    st.markdown("### 🔧 Data Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Data", type="secondary"):
            st.rerun()
    
    with col2:
        if st.button("📊 Export All Data", type="secondary"):
            all_data = DataManager.load_data()
            json_str = json.dumps(all_data, indent=2, default=str)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"portal_data_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json"
            )
    
    with col3:
        # Show data file info
        if Path(Config.DATA_FILE).exists():
            file_size = Path(Config.DATA_FILE).stat().st_size
            st.metric("📁 Data File", f"{file_size} bytes")
    
    # Deadline management section
    st.markdown("---")
    st.markdown("### ⏰ Deadline Management")
    st.write("Set custom deadlines for team resources. Leave blank to use default deadlines.")
    
    # Create deadline management interface
    deadline_cols = st.columns(2)
    
    with deadline_cols[0]:
        st.markdown("#### 🐲 Junior Team Deadlines")
        for item_name in Config.RESOURCES["Junior"].keys():
            current_deadline = DataManager.get_effective_deadline("Junior", item_name)
            
            col_label, col_input, col_button = st.columns([3, 2, 1])
            with col_label:
                st.write(f"**{item_name}**")
            with col_input:
                new_date = st.date_input(
                    f"Deadline",
                    value=datetime.strptime(current_deadline, "%Y-%m-%d").date() if current_deadline else datetime.now().date(),
                    key=f"junior_{item_name}_date",
                    label_visibility="collapsed"
                )
            with col_button:
                if st.button("Set", key=f"junior_{item_name}_set"):
                    DataManager.update_deadline("Junior", item_name, new_date.strftime("%Y-%m-%d"))
                    st.success("Updated!")
                    st.rerun()
        
        st.markdown("#### 💪 Pull Up Warrior Deadlines")
        for item_name in Config.RESOURCES["Pull Up Warrior"].keys():
            current_deadline = DataManager.get_effective_deadline("Pull Up Warrior", item_name)
            
            col_label, col_input, col_button = st.columns([3, 2, 1])
            with col_label:
                st.write(f"**{item_name}**")
            with col_input:
                new_date = st.date_input(
                    f"Deadline",
                    value=datetime.strptime(current_deadline, "%Y-%m-%d").date() if current_deadline else datetime.now().date(),
                    key=f"pullup_{item_name}_date",
                    label_visibility="collapsed"
                )
            with col_button:
                if st.button("Set", key=f"pullup_{item_name}_set"):
                    DataManager.update_deadline("Pull Up Warrior", item_name, new_date.strftime("%Y-%m-%d"))
                    st.success("Updated!")
                    st.rerun()
    
    with deadline_cols[1]:
        st.markdown("#### 🐉 Senior Team Deadlines")
        for item_name in Config.RESOURCES["Senior"].keys():
            current_deadline = DataManager.get_effective_deadline("Senior", item_name)
            
            col_label, col_input, col_button = st.columns([3, 2, 1])
            with col_label:
                st.write(f"**{item_name}**")
            with col_input:
                new_date = st.date_input(
                    f"Deadline",
                    value=datetime.strptime(current_deadline, "%Y-%m-%d").date() if current_deadline else datetime.now().date(),
                    key=f"senior_{item_name}_date",
                    label_visibility="collapsed"
                )
            with col_button:
                if st.button("Set", key=f"senior_{item_name}_set"):
                    DataManager.update_deadline("Senior", item_name, new_date.strftime("%Y-%m-%d"))
                    st.success("Updated!")
                    st.rerun()
    
    # Bulk deadline setting
    st.markdown("#### 🗓️ Bulk Deadline Actions")
    bulk_cols = st.columns(4)
    
    with bulk_cols[0]:
        if st.button("📅 Set All to Month End", type="secondary"):
            next_month_end = (datetime.now().replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            for role in ["Junior", "Senior", "Pull Up Warrior"]:
                for item in Config.RESOURCES[role].keys():
                    DataManager.update_deadline(role, item, next_month_end.strftime("%Y-%m-%d"))
            st.success("All deadlines set to end of current month!")
            st.rerun()
    
    with bulk_cols[1]:
        if st.button("📅 Set All to Week End", type="secondary"):
            next_sunday = datetime.now() + timedelta(days=(6 - datetime.now().weekday()))
            for role in ["Junior", "Senior", "Pull Up Warrior"]:
                for item in Config.RESOURCES[role].keys():
                    DataManager.update_deadline(role, item, next_sunday.strftime("%Y-%m-%d"))
            st.success("All deadlines set to end of current week!")
            st.rerun()
    
    with bulk_cols[2]:
        custom_bulk_date = st.date_input("Custom Date", key="bulk_custom_date")
    
    with bulk_cols[3]:
        if st.button("📅 Set All to Custom", type="secondary"):
            for role in ["Junior", "Senior", "Pull Up Warrior"]:
                for item in Config.RESOURCES[role].keys():
                    DataManager.update_deadline(role, item, custom_bulk_date.strftime("%Y-%m-%d"))
            st.success(f"All deadlines set to {custom_bulk_date}!")
            st.rerun()
    
    # Show current deadline overview
    st.markdown("#### 📊 Current Deadlines Overview")
    deadline_overview = []
    for role in ["Junior", "Senior", "Pull Up Warrior"]:
        for item in Config.RESOURCES[role].keys():
            effective_deadline = DataManager.get_effective_deadline(role, item)
            if effective_deadline:
                days_left = (datetime.strptime(effective_deadline, "%Y-%m-%d") - datetime.now()).days
                status = "🔴 Overdue" if days_left < 0 else "🟡 Due Soon" if days_left <= 3 else "🟢 On Track"
                
                deadline_overview.append({
                    "Team": role,
                    "Item": item,
                    "Deadline": effective_deadline,
                    "Days Left": days_left,
                    "Status": status
                })
    
    if deadline_overview:
        df_deadlines = pd.DataFrame(deadline_overview)
        df_deadlines = df_deadlines.sort_values("Days Left")
        st.dataframe(df_deadlines, use_container_width=True, hide_index=True)

def render_dashboard():
    """Render the main dashboard"""
    role = st.session_state.role
    
    if role == "APH":
        render_aph_dashboard()
        return
    
    resources = Config.RESOURCES[role]
    
    # Header
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1f4e79, #2e86de); 
                color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
        <h1>🐉 {role} Portal</h1>
        <p>Team Resource Management Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick stats
    data = DataManager.load_data()
    user_submissions = [s for s in data["submissions"] if s["role"] == role]
    completed_count = len([s for s in user_submissions if s["status"] == "Completed"])
    total_items = len(resources)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Items", total_items)
    with col2:
        st.metric("✅ Team Completions", completed_count)
    with col3:
        completion_rate = (completed_count / max(total_items, 1)) * 100
        st.metric("📈 Completion Rate", f"{completion_rate:.1f}%")
    
    st.markdown("---")
    
    # Resource tabs
    if resources:
        tabs = st.tabs(list(resources.keys()))
        
        for i, (title, resource) in enumerate(resources.items()):
            with tabs[i]:
                render_resource_card(title, resource, i)
    
    # Recent activity
    st.markdown("### 📊 Recent Team Activity")
    if user_submissions:
        df = pd.DataFrame(user_submissions[-10:])  # Last 10 submissions
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(
            df[["timestamp", "name", "item", "status", "notes"]].rename(columns={
                "timestamp": "Time",
                "name": "Name", 
                "item": "Item",
                "status": "Status",
                "notes": "Notes"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No recent activity to display.")

def render_footer():
    """Render footer with logout and info"""
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        <small style="color: #666;">
        🐉 Dragonboat Team Portal v2.0 | 
        Session ID: """ + st.session_state.get("session_id", "unknown") + """
        </small>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🔓 Logout"):
            st.session_state.clear()
            st.rerun()

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
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    init_session_state()
    
    if st.session_state.role is None:
        render_login_page()
    else:
        check_session_timeout()
        render_dashboard()
        render_footer()

if __name__ == "__main__":
    main()