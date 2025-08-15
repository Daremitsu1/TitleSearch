from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import hashlib
from config import get_db_connection
import mysql.connector

app = FastAPI()

# Request schemas
class SignOnRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

def hash_password(password: str) -> str:
    """Hash password using SHA256 before sending to MySQL."""
    return hashlib.sha256(password.encode()).hexdigest()

@app.post("/user-signon", description="User sign on to the application", tags=["User Authentication"])
def sign_on(data: SignOnRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        hashed_pwd = hash_password(data.password)
        cursor.callproc("sp_user_sign_on", (data.username, data.email, hashed_pwd))
        conn.commit()

        result = []
        for res in cursor.stored_results():
            result.extend(res.fetchall())

        cursor.close()
        conn.close()
        return {"result": result}

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"MySQL Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/user-login", description="User login to the application", tags=["User Authentication"])
def login(data: LoginRequest, request: Request):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get IP address from request
        client_host = request.client.host

        hashed_pwd = hash_password(data.password)
        cursor.callproc("sp_user_login", (data.username, hashed_pwd, client_host))

        result = []
        for res in cursor.stored_results():
            result.extend(res.fetchall())

        cursor.close()
        conn.close()

        if not result or "FAILED" in str(result).upper():
            raise HTTPException(status_code=401, detail="Invalid username or password")

        return {"result": result}

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"MySQL Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
