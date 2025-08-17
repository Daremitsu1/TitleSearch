from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import mysql.connector
from api.config import get_db_connection, get_mongo_connection
from scraper.FL.Broward.broward_scraper import broward_appraiser, broward_revenue

app = FastAPI()

# Request models
class CountyRequest(BaseModel):
    state_id: int

class WebsiteRequest(BaseModel):
    state_id: int
    county_id: int

# Request model for create-job
class CreateJobRequest(BaseModel):
    state_id: int
    county_id: int
    website_id: int
    search_value: str  # This will contain Name/Folio/Address

# Utility to format SQL results into list of dicts
def fetch_all_as_dict(cursor):
    cols = [desc[0] for desc in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

# 1. GET all states
@app.get("/states", tags=["Filter Criteria"])
def get_states():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.callproc("sp_get_states")
        for result in cursor.stored_results():
            data = fetch_all_as_dict(result)
        return {"states": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 2. POST - get counties by state
@app.post("/counties", tags=["Filter Criteria"])
def get_counties(req: CountyRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Pass as tuple, not dict
        cursor.callproc("sp_get_counties_by_state", (req.state_id,))
        for result in cursor.stored_results():
            data = fetch_all_as_dict(result)
        return {"counties": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 3. POST - get websites by state & county
@app.post("/websites", tags=["Filter Criteria"])
def get_websites(req: WebsiteRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.callproc("sp_get_websites_by_state_county", (req.state_id, req.county_id))
        for result in cursor.stored_results():
            data = fetch_all_as_dict(result)
        return {"websites": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# POST API to create job
@app.post("/create-job", tags=["Job"])
def create_job(req: CreateJobRequest):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch state_code
        cursor.execute("SELECT state_code FROM state_list WHERE state_id = %s", (req.state_id,))
        state = cursor.fetchone()
        if not state:
            raise HTTPException(status_code=404, detail="State not found")
        state_code = state["state_code"]

        # Fetch county_code
        cursor.execute("SELECT fips_code FROM county_list WHERE county_id = %s", (req.county_id,))
        county = cursor.fetchone()
        if not county:
            raise HTTPException(status_code=404, detail="County not found")
        county_code = county["fips_code"]

        # Fetch serial_code & website_name
        cursor.execute("SELECT serial_code, website_name FROM website_list WHERE website_id = %s", (req.website_id,))
        website = cursor.fetchone()
        if not website:
            raise HTTPException(status_code=404, detail="Website not found")
        serial_code = website["serial_code"]
        website_name = website["website_name"]

        # Generate job name
        current_date = datetime.now().strftime("%Y%m%d")
        job_name = f"{state_code}{county_code}{serial_code}{current_date}"

        # Function to get status_id by status_name
        def get_status_id(status_name: str):
            cursor.callproc("sp_get_status_id", (status_name,))
            status_id = None
            for result in cursor.stored_results():
                row = result.fetchone()
                if row:
                    status_id = row["status_id"]
                    break
            if not status_id:
                raise HTTPException(status_code=500, detail=f"{status_name} status not found in status_db")
            return status_id

        # 🔹 Scraper mapping using website_name
        scraper_map = {
            "Broward Property Appraiser": broward_appraiser,
            "Broward Revenue Collection": broward_revenue,
        }
        scraper_func = scraper_map.get(website_name)
        if not scraper_func:
            raise HTTPException(status_code=400, detail=f"No scraper found for website: {website_name}")

        # Insert job as Pending first
        pending_status_id = get_status_id("Pending")
        cursor.callproc("sp_insert_job", (3, req.state_id, req.county_id, req.website_id, job_name, pending_status_id))
        cursor.execute("SELECT LAST_INSERT_ID() AS job_id")
        job_id = cursor.fetchone()["job_id"]
        conn.commit()

        # Update job status to Initiated before scraper
        initiated_status_id = get_status_id("Initiated")
        cursor.execute("UPDATE job_list SET status_id=%s WHERE job_id=%s", (initiated_status_id, job_id))
        conn.commit()

        # Run scraper
        scraper_success = scraper_func(
            job_name=job_name,
            search_value=req.search_value,
            website_type=website_name
        )
        if not scraper_success:
            raise HTTPException(status_code=500, detail="Scraper failed")

        # Update job status to In Progress while inserting documents
        in_progress_status_id = get_status_id("In Progress")
        cursor.execute("UPDATE job_list SET status_id=%s WHERE job_id=%s", (in_progress_status_id, job_id))
        conn.commit()

        # --- Fetch docs from Mongo and insert
        mongo_collection = get_mongo_connection()
        docs = list(mongo_collection.find({"Job_Name": job_name}, {"Doc_Name": 1, "_id": 0}))
        if not docs:
            raise HTTPException(status_code=500, detail="No documents found in Mongo for this job")

        doc_ids = []
        for d in docs:
            doc_name = d["Doc_Name"]
            cursor.callproc("sp_insert_document", (job_id, doc_name))
            for result in cursor.stored_results():
                row = result.fetchone()
                if row:
                    doc_ids.append({"doc_id": row["doc_id"], "doc_name": doc_name})
        conn.commit()

        # Update job status to Completed
        completed_status_id = get_status_id("Completed")
        cursor.execute("UPDATE job_list SET status_id=%s WHERE job_id=%s", (completed_status_id, job_id))
        conn.commit()

        return {
            "job_id": job_id,
            "job_name": job_name,
            "documents": doc_ids
        }

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()