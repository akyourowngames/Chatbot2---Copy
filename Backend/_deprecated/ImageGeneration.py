import asyncio
from random import randint
from PIL import Image, UnidentifiedImageError
import requests
from dotenv import get_key
import os
from time import sleep


def open_images(prompt):
    folder_path = r"Data"
    prompt = prompt.replace(" ", "_")

    Files = [f"{prompt}{i}.jpg" for i in range(1, 5)]

    for jpg_file in Files:
        image_path = os.path.join(folder_path, jpg_file)

        try:
            with Image.open(image_path) as img:
                img.verify()  # Verify if the image is valid
                img = Image.open(image_path)  # Reopen for proper operation
                print(f"Opening image: {image_path}")
                img.show()
                sleep(1)
        except (IOError, UnidentifiedImageError):
            print(f"Unable to open {image_path} - File might be corrupted or not in proper format.")


API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}"}


async def query(payload):
    response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
    return response.content


async def generate_images(prompt: str):
    tasks = []

    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, seed= {randint(1, 1000000)}",
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    image_bytes_list = await asyncio.gather(*tasks)

    for i, image_bytes in enumerate(image_bytes_list):
        output_path = fr"Data\{prompt.replace(' ', '_')}{i + 1}.jpg"
        try:
            # Save the image content
            with open(output_path, "wb") as f:
                f.write(image_bytes)

            # Validate and re-save the image to ensure proper format
            with Image.open(output_path) as img:
                img.convert("RGB").save(output_path, "JPEG")
        except UnidentifiedImageError:
            print(f"Failed to process the image at {output_path}")


def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_images(prompt)


if __name__ == "__main__":
    while True:
        try:
            with open(r"Frontend/Files/ImageGeneration.data", "r") as f:
                Data: str = f.read()
                print(f"Read from file: {Data}")

            # Extract the prompt and status
            Prompt, Status = Data.split(", ")
            print(f"Extracted Prompt='{Prompt}', Status='{Status}'")

            if Status.strip() == "True":
                print("Generating Images ...")
                GenerateImages(prompt=Prompt.strip())

                # Reset the file after generating images
                with open(r"Frontend/Files/ImageGeneration.data", "w") as f:
                    f.write("False, False")
                print("Reset the file to 'False, False'")
                break

            else:
                print("Status is not 'True', sleeping for 1 second")
                sleep(1)

        except Exception as e:
            print(f"An error occurred: {e}")
            sleep(1)