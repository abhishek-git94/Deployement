import os
import io
import json

import openai
import PyPDF2

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="NexusAI Resume Parser API",
    description="AI Powered Resume Parser Backend"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# ENV VARIABLES
# =========================

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")

if not API_KEY:
    raise ValueError("API_KEY environment variable not found")

if not BASE_URL:
    raise ValueError("BASE_URL environment variable not found")


# =========================
# OPENAI CLIENT
# =========================

client = openai.OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)


# =========================
# ROOT ROUTE
# =========================

@app.get("/")
def home():

    return {
        "message": "NexusAI Resume Parser Backend is Running"
    }


# =========================
# RESUME PARSER API
# =========================

@app.post("/api/parse")
async def parse_resume(resume: UploadFile = File(...)):

    try:

        content = await resume.read()

        text = ""

        # =========================
        # PDF EXTRACTION
        # =========================

        if resume.filename.lower().endswith(".pdf"):

            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))

            for page in pdf_reader.pages:

                extracted = page.extract_text()

                if extracted:
                    text += extracted + "\n"

        else:

            try:
                text = content.decode("utf-8")

            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Only PDF files are supported."
                )

        if not text.strip():

            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF."
            )

        # =========================
        # SYSTEM PROMPT
        # =========================

        system_prompt = """
You are an expert AI resume parser.

Extract information from the resume and return ONLY valid JSON.

Do not include markdown.
Do not include explanations.
Return raw JSON only.

JSON format:

{
  "personalInfo": {
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedIn": ""
  },
  "summary": "",
  "skills": [],
  "experience": [
    {
      "title": "",
      "company": "",
      "duration": "",
      "description": ""
    }
  ],
  "education": [
    {
      "degree": "",
      "institution": "",
      "year": ""
    }
  ]
}
"""

        # =========================
        # LLM REQUEST
        # =========================

        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0
        )

        result_text = response.choices[0].message.content.strip()

        # =========================
        # CLEAN MARKDOWN
        # =========================

        if result_text.startswith("```json"):
            result_text = result_text[7:]

        if result_text.endswith("```"):
            result_text = result_text[:-3]

        parsed_data = json.loads(result_text.strip())

        return {
            "success": True,
            "data": parsed_data
        }

    except json.JSONDecodeError:

        return {
            "success": False,
            "error": "Invalid JSON returned by model."
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    import uvicorn

    port = int(os.environ.get("PORT", 10000))

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port
    )