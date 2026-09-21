
import sqlite3
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "campus.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

CATEGORIES = ["Electrical", "Furniture", "Plumbing", "IT", "Internet", "Cleaning", "AC/Cooling", "Other"]
PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Pending", "In Progress", "Resolved"]

st.set_page_config(
    page_title="CampusFix — Maintenance Tracker",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    .hero {
        padding: 1.2rem 1.4rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #1f2937 0%, #334155 100%);
        color: white;
        margin-bottom: 1.2rem;
    }
    .hero h1 {margin: 0 0 .3rem 0; font-size: 2.15rem;}
    .hero p {margin: 0; opacity: .9;}
    .small-note {color: #64748b; font-size: .9rem;}
    div[data-testid="stMetric"] {
        border: 1px solid rgba(100,116,139,.18);
        border-radius: 14px;
        padding: .65rem;
        background: rgba(248,250,252,.65);
    }
</style>
""", unsafe_allow_html=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE NOT NULL,
            student_name TEXT NOT NULL,
            department TEXT NOT NULL,
            building TEXT NOT NULL,
            room_no TEXT NOT NULL,
            category TEXT NOT NULL,
            problem TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            date TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            staff_name TEXT NOT NULL,
            repair_date TEXT NOT NULL,
            cost REAL NOT NULL,
            remarks TEXT,
            FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
        )
    """)
    conn.commit()
    conn.close()

def get_complaints():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM complaints ORDER BY id DESC", conn)
    conn.close()
    return df

def get_maintenance():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM maintenance ORDER BY id DESC", conn)
    conn.close()
    return df

def next_complaint_id():
    conn = get_conn()
    row = conn.execute("SELECT MAX(id) AS max_id FROM complaints").fetchone()
    conn.close()
    n = (row["max_id"] or 0) + 1
    return f"CMP{n:03d}"

def complaint_exists(cid):
    conn = get_conn()
    row = conn.execute("SELECT complaint_id FROM complaints WHERE complaint_id = ?", (cid,)).fetchone()
    conn.close()
    return row is not None

def add_complaint(student, dept, building, room, category, problem, priority):
    cid = next_complaint_id()
    conn = get_conn()
    conn.execute("""
        INSERT INTO complaints
        (complaint_id, student_name, department, building, room_no, category, problem, priority, status, date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?)
    """, (cid, student.strip(), dept.strip(), building.strip(), room.strip(), category, problem.strip(), priority, str(date.today())))
    conn.commit()
    conn.close()
    return cid

def update_status(cid, status):
    conn = get_conn()
    cur = conn.execute("UPDATE complaints SET status = ? WHERE complaint_id = ?", (status, cid))
    conn.commit()
    conn.close()
    return cur.rowcount > 0

def add_maintenance(cid, staff, repair_date, cost, remarks):
    conn = get_conn()
    conn.execute("""
        INSERT INTO maintenance (complaint_id, staff_name, repair_date, cost, remarks)
        VALUES (?, ?, ?, ?, ?)
    """, (cid, staff.strip(), str(repair_date), float(cost), remarks.strip()))
    conn.commit()
    conn.close()

def search_complaint(cid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM complaints WHERE complaint_id = ?", (cid,)).fetchone()
    conn.close()
    return dict(row) if row else None

init_db()

st.markdown("""
<div class="hero">
  <h1>🛠️ CampusFix</h1>
  <p>Campus Maintenance Complaint & Tracking System · Register, track, repair and analyze campus issues.</p>
</div>
""", unsafe_allow_html=True)

complaints = get_complaints()
maintenance = get_maintenance()

with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Go to",
        ["Dashboard", "Register Complaint", "View Complaints", "Search Complaint",
         "Update Status", "Add Maintenance", "Reports & Analysis"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Built with Streamlit • Python • SQLite • Pandas • Matplotlib")
    st.caption(f"Database: `{DB_PATH.name}`")

if page == "Dashboard":
    total = len(complaints)
    pending = int((complaints["status"] == "Pending").sum()) if total else 0
    progress = int((complaints["status"] == "In Progress").sum()) if total else 0
    resolved = int((complaints["status"] == "Resolved").sum()) if total else 0
    total_cost = float(maintenance["cost"].sum()) if not maintenance.empty else 0.0

    st.subheader("Dashboard")
    a, b, c, d, e = st.columns(5)
    a.metric("Total Complaints", total)
    b.metric("Pending", pending)
    c.metric("In Progress", progress)
    d.metric("Resolved", resolved)
    e.metric("Maintenance Cost", f"₹{total_cost:,.0f}")

    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown("### Complaint Status")
        if total:
            status_counts = complaints["status"].value_counts().reindex(STATUSES, fill_value=0)
            fig, ax = plt.subplots()
            ax.pie(status_counts.values, labels=status_counts.index, autopct="%1.0f%%")
            ax.set_title("Pending / In Progress / Resolved")
            st.pyplot(fig, width="stretch")
            plt.close(fig)
        else:
            st.info("No complaints yet.")
    with right:
        st.markdown("### Complaints by Category")
        if total:
            counts = complaints["category"].value_counts().sort_values()
            fig, ax = plt.subplots()
            counts.plot(kind="barh", ax=ax)
            ax.set_xlabel("Number of complaints")
            ax.set_ylabel("")
            st.pyplot(fig, width="stretch")
            plt.close(fig)
        else:
            st.info("No complaints yet.")

    if total:
        st.markdown("### Recent Complaints")
        st.dataframe(
            complaints[["complaint_id","student_name","category","building","priority","status","date"]].head(8),
            width="stretch",
            hide_index=True,
        )

elif page == "Register Complaint":
    st.subheader("Register Complaint")
    st.caption("Complaint IDs are generated automatically, e.g. CMP001.")
    with st.form("register_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        student = c1.text_input("Student Name *")
        dept = c2.text_input("Department *")
        building = c1.text_input("Building *", placeholder="Block A")
        room = c2.text_input("Room No. *", placeholder="204")
        category = c1.selectbox("Category *", CATEGORIES)
        priority = c2.selectbox("Priority *", PRIORITIES, index=1)
        problem = st.text_area("Problem Description *", placeholder="Describe the issue...")
        submitted = st.form_submit_button("Register Complaint", type="primary", width="stretch")

    if submitted:
        if not all([student.strip(), dept.strip(), building.strip(), room.strip(), problem.strip()]):
            st.error("Please fill all required fields.")
        else:
            try:
                cid = add_complaint(student, dept, building, room, category, problem, priority)
                st.success(f"Complaint Registered Successfully — **{cid}**")
                st.info("Status: Pending")
                st.rerun()
            except sqlite3.Error as exc:
                st.error(f"Database error: {exc}")

elif page == "View Complaints":
    st.subheader("View Complaints")
    if complaints.empty:
        st.info("No complaints have been registered yet.")
    else:
        f1, f2, f3 = st.columns(3)
        status_filter = f1.multiselect("Status", STATUSES, default=STATUSES)
        category_filter = f2.multiselect("Category", CATEGORIES, default=CATEGORIES)
        text_filter = f3.text_input("Search text", placeholder="ID, student, problem...")

        df = complaints[
            complaints["status"].isin(status_filter) &
            complaints["category"].isin(category_filter)
        ].copy()
        if text_filter.strip():
            q = text_filter.strip().lower()
            mask = (
                df["complaint_id"].str.lower().str.contains(q, na=False) |
                df["student_name"].str.lower().str.contains(q, na=False) |
                df["problem"].str.lower().str.contains(q, na=False)
            )
            df = df[mask]

        display_cols = ["complaint_id","student_name","department","building","room_no",
                        "category","problem","priority","status","date"]
        st.dataframe(df[display_cols], width="stretch", hide_index=True)
        st.caption(f"Showing {len(df)} complaint(s).")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export Current View to CSV", csv, "complaints_report.csv", "text/csv")

elif page == "Search Complaint":
    st.subheader("Search Complaint")
    cid = st.text_input("Complaint ID", placeholder="CMP001").strip().upper()
    if st.button("Search", type="primary"):
        if not cid:
            st.warning("Enter a Complaint ID.")
        else:
            row = search_complaint(cid)
            if not row:
                st.error("Complaint Not Found")
            else:
                st.success(f"Complaint {cid} found")
                c1, c2, c3 = st.columns(3)
                c1.metric("Status", row["status"])
                c2.metric("Priority", row["priority"])
                c3.metric("Category", row["category"])
                st.dataframe(pd.DataFrame([row]), width="stretch", hide_index=True)

                m = maintenance[maintenance["complaint_id"] == cid] if not maintenance.empty else pd.DataFrame()
                if not m.empty:
                    st.markdown("#### Maintenance Details")
                    st.dataframe(m, width="stretch", hide_index=True)
                else:
                    st.info("No maintenance record has been added for this complaint.")

elif page == "Update Status":
    st.subheader("Update Complaint Status")
    if complaints.empty:
        st.info("No complaints available.")
    else:
        cid = st.selectbox("Complaint ID", complaints["complaint_id"].tolist())
        row = search_complaint(cid)
        st.write(f"Current status: **{row['status']}**")
        new_status = st.selectbox("New Status", STATUSES, index=STATUSES.index(row["status"]))
        if st.button("Update Status", type="primary"):
            if update_status(cid, new_status):
                st.success(f"{cid}: status updated to **{new_status}**")
                st.rerun()
            else:
                st.error("Complaint ID not found.")

elif page == "Add Maintenance":
    st.subheader("Add Maintenance Details")
    if complaints.empty:
        st.info("Register a complaint first.")
    else:
        cid = st.selectbox("Complaint ID", complaints["complaint_id"].tolist())
        c1, c2 = st.columns(2)
        staff = c1.text_input("Maintenance Staff Name *")
        repair_date = c2.date_input("Repair Date", value=date.today())
        cost = c1.number_input("Repair Cost (₹) *", min_value=0.0, step=50.0)
        remarks = c2.text_area("Repair Remarks", placeholder="Fan capacitor replaced")
        if st.button("Save Maintenance Details", type="primary"):
            if not staff.strip():
                st.error("Maintenance staff name is required.")
            elif cost < 0:
                st.error("Repair cost cannot be negative.")
            else:
                add_maintenance(cid, staff, repair_date, cost, remarks)
                st.success(f"Maintenance details saved for **{cid}**.")
                st.rerun()

elif page == "Reports & Analysis":
    st.subheader("Reports & Analysis")
    if complaints.empty:
        st.info("No complaint data available for analysis.")
    else:
        total = len(complaints)
        pending = int((complaints["status"] == "Pending").sum())
        progress = int((complaints["status"] == "In Progress").sum())
        resolved = int((complaints["status"] == "Resolved").sum())
        total_cost = float(maintenance["cost"].sum()) if not maintenance.empty else 0.0
        avg_cost = float(maintenance["cost"].mean()) if not maintenance.empty else 0.0
        common_cat = complaints["category"].mode().iloc[0] if not complaints["category"].mode().empty else "N/A"
        common_building = complaints["building"].mode().iloc[0] if not complaints["building"].mode().empty else "N/A"

        a,b,c,d = st.columns(4)
        a.metric("Total Complaints", total)
        b.metric("Pending", pending)
        c.metric("In Progress", progress)
        d.metric("Resolved", resolved)
        a,b,c = st.columns(3)
        a.metric("Total Maintenance Cost", f"₹{total_cost:,.2f}")
        b.metric("Average Repair Cost", f"₹{avg_cost:,.2f}")
        c.metric("Most Common Category", common_cat)
        st.info(f"Most Reported Building: **{common_building}**")

        st.markdown("### Charts")
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**1. Complaints by Category**")
            counts = complaints["category"].value_counts().sort_values()
            fig, ax = plt.subplots()
            counts.plot(kind="barh", ax=ax)
            ax.set_xlabel("Complaints")
            ax.set_ylabel("")
            st.pyplot(fig, width="stretch")
            plt.close(fig)

        with c2:
            st.markdown("**2. Complaint Status Distribution**")
            status_counts = complaints["status"].value_counts().reindex(STATUSES, fill_value=0)
            fig, ax = plt.subplots()
            ax.pie(status_counts.values, labels=status_counts.index, autopct="%1.0f%%")
            st.pyplot(fig, width="stretch")
            plt.close(fig)

        c3, c4 = st.columns(2)
        with c3:
            st.markdown("**3. Complaints by Building**")
            counts = complaints["building"].value_counts().sort_values()
            fig, ax = plt.subplots()
            counts.plot(kind="barh", ax=ax)
            ax.set_xlabel("Complaints")
            ax.set_ylabel("")
            st.pyplot(fig, width="stretch")
            plt.close(fig)

        with c4:
            st.markdown("**4. Complaints Reported by Month**")
            tmp = complaints.copy()
            tmp["date"] = pd.to_datetime(tmp["date"], errors="coerce")
            monthly = tmp.dropna(subset=["date"]).groupby(tmp["date"].dt.to_period("M")).size()
            monthly.index = monthly.index.astype(str)
            fig, ax = plt.subplots()
            monthly.plot(kind="line", marker="o", ax=ax)
            ax.set_xlabel("Month")
            ax.set_ylabel("Complaints")
            ax.grid(alpha=.2)
            st.pyplot(fig, width="stretch")
            plt.close(fig)

        if not maintenance.empty:
            st.markdown("**5. Maintenance Cost by Category**")
            joined = maintenance.merge(complaints[["complaint_id","category"]], on="complaint_id", how="left")
            cost_by_cat = joined.groupby("category")["cost"].sum().sort_values()
            fig, ax = plt.subplots()
            cost_by_cat.plot(kind="barh", ax=ax)
            ax.set_xlabel("Total repair cost (₹)")
            ax.set_ylabel("")
            st.pyplot(fig, width="stretch")
            plt.close(fig)

        st.markdown("### Export")
        export_df = complaints.copy()
        csv = export_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Complaints CSV", csv, "complaints_report.csv", "text/csv")
        if not maintenance.empty:
            mcsv = maintenance.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download Maintenance CSV", mcsv, "maintenance_report.csv", "text/csv")

st.markdown("---")
st.markdown('<div class="small-note">CampusFix follows the project workflow: Enter Complaint → Save → View/Search → Update Status → Add Repair Details → Analyze Data.</div>', unsafe_allow_html=True)
