import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
import aiofiles
import asyncio
from pdf2image import convert_from_path
import requests
import shutil

app = FastAPI()

@app.post("/convert-pdf")
async def convert_pdf(
    file: UploadFile = File(...),
    file_name: str = Form(...),
    organization_id: str = Form(...),
    document_id: str = Form(...)
):
    # Save the uploaded PDF file
    pdf_path = f"temp_{file_name}"
    async with aiofiles.open(pdf_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    # Convert the first page of the PDF to PNG
    images = convert_from_path(pdf_path, first_page=1, last_page=1)
    png_path = f"temp_{file_name}.png"
    images[0].save(png_path, 'PNG')

    # Send the PNG file via webhook
    webhook_url = os.getenv("WEBHOOK_URL")
    with open(png_path, "rb") as png_file:
        files = {"file": (f"{file_name}.png", png_file, "image/png")}
        data = {
            "file_name": file_name,
            "organization_id": organization_id,
            "document_id": document_id
        }
        response = requests.post(webhook_url, files=files, data=data)

    # Clean up temporary files
    os.remove(pdf_path)
    os.remove(png_path)

    if response.status_code == 200:
        return JSONResponse(content={"message": "Conversion and webhook successful"}, status_code=200)
    else:
        return JSONResponse(content={"message": "Webhook failed"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)