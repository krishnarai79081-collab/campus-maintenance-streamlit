# CampusFix — Campus Maintenance Complaint & Tracking System

A Streamlit web version of the Campus Maintenance Complaint & Tracking System described in the supplied project guide.

## Features
- Register complaints with automatic `CMP001`-style IDs
- View, filter and search complaints
- Update status: Pending / In Progress / Resolved
- Add maintenance staff, repair date, cost and remarks
- Dashboard metrics
- Pandas + Matplotlib reports with 5 charts
- Export complaints and maintenance data to CSV
- SQLite database

## Tech stack
Python, Streamlit, SQLite, Pandas, Matplotlib.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Push this folder to a GitHub repository.
2. Open Streamlit Community Cloud.
3. Choose **Create app**.
4. Select the GitHub repository, branch and `app.py`.
5. Deploy.

### Important persistence note
This project intentionally follows the guide's SQLite design. On Streamlit Community Cloud, local SQLite storage should be treated as demo/test storage because a deployed app's local filesystem is not a reliable long-term multi-user database. For production use, move the database to a hosted PostgreSQL/Supabase-style database.
