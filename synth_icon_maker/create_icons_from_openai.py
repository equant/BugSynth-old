from openai import OpenAI
import os
import requests

client = OpenAI(api_key='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')

model="dall-e-3"
presets_file_path = 'presets.txt'
output_directory = 'images'
pre_prompt = "A "
post_prompt = f" done in a child-like pixel art icon syle using only black and white color, with simple, clear, bold lines, minimal detail, and a focus on the key features that define the subject."

pre_prompt = "Black and white, minimal, stylized icon of a "
post_prompt = " using minimal clear, lines, minimal detail and a focus on key features.  On a black background."


def generate_image(prompt):
    response = client.images.generate(
                    model=model,
                    prompt=prompt,
                    n=1,  # Number of images to generate
                    size="1024x1024"
    )
    #breakpoint()
    return response.data[0].url

def download_image(image_url, filename):
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)

def process_presets(file_path, output_dir):
    with open(file_path, 'r') as file:
        for line in file:
            line = line.rstrip()
            if not line or line.startswith('#'):
                continue

            preset = line
            print(f"Generating image for: {preset}")
            #prompt = f'"{preset}" pixel art icon using black and white color scheme, simplicity, clear and bold lines, minimal detail, and a focus on the key features that define the subject and landscape orientation.'
            prompt = pre_prompt + preset + post_prompt
            image_url = generate_image(prompt)
            print(image_url)
            filename = os.path.join(output_dir, f'{preset}-{model}.png')  # Save as PNG
            print(f'Downloaded image for {preset}: {filename}')
            download_image(image_url, filename)

process_presets(presets_file_path, output_directory)
