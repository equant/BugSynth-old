from PIL import Image, ImageChops
import os

def trim_old(im):
    bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)


def trim(im, aspect_ratio=None):
    """
    Trims the border from the image and adds padding to maintain the aspect ratio.

    Usage:
    trimmed_and_padded_im = trim_and_pad(im)  # Preserves original aspect ratio
    trimmed_and_padded_im = trim_and_pad(im, aspect_ratio=16/9)  # Preserves a 16:9 aspect ratio
    """

    border_color = im.getpixel((0, 0))

    bg = Image.new(im.mode, im.size, border_color)
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()

    if bbox:
        # Crop to the inner box
        cropped_im = im.crop(bbox)

        # Calculate aspect ratio to be preserved
        aspect_ratio = aspect_ratio or (im.width / im.height)

        # Calculate new dimensions based on aspect ratio
        new_width = max(cropped_im.width, int(cropped_im.height * aspect_ratio))
        new_height = max(cropped_im.height, int(cropped_im.width / aspect_ratio))

        # Create a new image with the desired aspect ratio
        new_im = Image.new(im.mode, (new_width, new_height), border_color)
        
        # Calculate position to paste the cropped image onto the new image
        x = (new_width - cropped_im.width) // 2
        y = (new_height - cropped_im.height) // 2

        new_im.paste(cropped_im, (x, y))

        return new_im
    else:
        return im


def crop_and_resize(image_path, output_path, target_size=(128, 128), background_color=(255, 255, 255)):
    # Open the image
    with Image.open(image_path) as img:
        # Convert to RGB if not
        if img.mode != 'RGB':
            img = img.convert('RGB')

        img_cropped = trim(img)

        threshold=128
        #img_cropped = img_cropped.convert('L')
        #img_cropped = img_cropped.convert('1', dither=image.resampling.nearest)
        img_cropped = img_cropped.convert('1', dither=Image.NONE)
        img_cropped.point(lambda x: 255 if x > threshold else 0, '1')

        # Determine the best fit (normal or rotated)
        #if img_cropped.height > img_cropped.width:
            # Rotate if wider than tall
            #img_cropped = img_cropped.rotate(90, expand=True)

        # Resize the image
        #img_resized = img_cropped.resize(target_size, Image.ANTIALIAS)
        img_resized = img_cropped.resize(target_size, Image.Resampling.NEAREST)

        # Save the processed image
        img_resized.save(output_path, format='BMP')

def process_images_in_directory(directory):
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(directory, filename)
            output_path = os.path.join(directory, "processed", f"{filename.upper().split('-')[0]}.bmp")
            crop_and_resize(image_path, output_path)

# Specify your directory here
directory = '.'
process_images_in_directory(directory)

