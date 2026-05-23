from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import base64

app = FastAPI(
    title="BFHL API",
    description="API for processing data and files"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BFHLRequest(BaseModel):
    data: List[str]
    file_b64: Optional[str] = None


def is_prime(n: int) -> bool:

    if n <= 1:
        return False

    if n <= 3:
        return True

    if n % 2 == 0 or n % 3 == 0:
        return False

    i = 5

    while i * i <= n:

        if n % i == 0 or n % (i + 2) == 0:
            return False

        i += 6

    return True


def parse_base64_file(file_b64: Optional[str]):

    if not file_b64:
        return False, None, None

    try:

        mime_type = None
        base64_data = file_b64

        if file_b64.startswith("data:") and ";base64," in file_b64:

            header, base64_data = file_b64.split(";base64,", 1)

            mime_type = header.split(":", 1)[1]

        decoded_bytes = base64.b64decode(base64_data)

        file_size_kb = len(decoded_bytes) / 1024.0

        if not mime_type:

            if decoded_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
                mime_type = "image/png"

            elif decoded_bytes.startswith(b"\xff\xd8\xff"):
                mime_type = "image/jpeg"

            elif decoded_bytes.startswith(b"%PDF"):
                mime_type = "doc/pdf"

            elif decoded_bytes.startswith(b"GIF87a") or decoded_bytes.startswith(b"GIF89a"):
                mime_type = "image/gif"

            else:
                mime_type = "application/octet-stream"

        if mime_type == "application/pdf":
            mime_type = "doc/pdf"

        return True, mime_type, f"{file_size_kb:.0f}"

    except Exception:
        return False, None, None


@app.get("/")
def home():
    return {
        "message": "BFHL API Running Successfully"
    }


@app.get("/bfhl")
def get_operation_code():

    return {
        "operation_code": 1
    }


@app.post("/bfhl")
def process_bfhl_data(request: BFHLRequest):

    try:

        data = request.data
        file_b64 = request.file_b64

        numbers = []
        alphabets = []

        for item in data:

            item_str = str(item).strip()

            if not item_str:
                continue

            if item_str.isdigit():
                numbers.append(item_str)

            elif item_str.isalpha() and len(item_str) == 1:
                alphabets.append(item_str)

        is_prime_found = False

        for num_str in numbers:

            try:

                num_val = int(num_str)

                if is_prime(num_val):
                    is_prime_found = True
                    break

            except ValueError:
                pass

        lowercase_alphabets = [
            char for char in alphabets if char.islower()
        ]

        highest_lowercase_alphabet = []

        if lowercase_alphabets:
            highest_lowercase_alphabet = [max(lowercase_alphabets)]

        file_valid, mime_type, file_size_kb = parse_base64_file(file_b64)

        response = {
            "is_success": True,
            "user_id": "abhishek_pal_30092004",
            "email": "abc@gmail.com",
            "roll_number": "0827AL231009",
            "numbers": numbers,
            "alphabets": alphabets,
            "highest_lowercase_alphabet": highest_lowercase_alphabet,
            "is_prime_found": is_prime_found,
            "file_valid": file_valid
        }

        if file_valid:

            response["file_mime_type"] = mime_type
            response["file_size_kb"] = file_size_kb

        return response

    except Exception as e:

        return {
            "is_success": False,
            "error": str(e)
        }