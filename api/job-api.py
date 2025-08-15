from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
from config import get_db_connection

app = FastAPI()

# Request models
class CountyRequest(BaseModel):
    state_id: int

class WebsiteRequest(BaseModel):
    state_id: int
    county_id: int

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
