from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import shutil

app = FastAPI()
IMAGE_DIR = "images"

# Create images folder if it doesn't exist
os.makedirs(IMAGE_DIR, exist_ok=True)

@app.post("/upload-image/")
async def upload_image(mobile: str, file: UploadFile = File(...)):
    # Check if uploaded file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Extract file extension (like .jpg, .png)
    file_ext = os.path.splitext(file.filename)[1]
    filename = f"{mobile}{file_ext}"
    file_path = os.path.join(IMAGE_DIR, filename)
    
    for existing_file in os.listdir(IMAGE_DIR):
        if existing_file.startswith(mobile):
            os.remove(os.path.join(IMAGE_DIR, existing_file))


    # Save uploaded image file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Return success message as JSON
    return {"message": f"Image saved for mobile {mobile}"}

@app.get("/get-image/{mobile}")
def get_image(mobile: str):
    # Look for any file starting with the mobile number
    for filename in os.listdir(IMAGE_DIR):
        if filename.startswith(mobile):
            # Return the image file with proper media type
            file_path = os.path.join(IMAGE_DIR, filename)
            return FileResponse(
                file_path, 
                media_type="image/*",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )

    # If no image found, return 404 error
    raise HTTPException(status_code=404, detail="Image not found")
