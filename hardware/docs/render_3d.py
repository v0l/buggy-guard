import sys

import f3d
from PIL import Image, ImageChops


def render(step, out, width, azimuth, elevation):
    f3d.Engine.autoload_plugins()
    engine = f3d.Engine.create(True)
    engine.options.update({
        "render.background.color": [1.0, 1.0, 1.0],
        "render.effect.antialiasing.enable": True,
        "render.effect.tone_mapping": True,
        "render.effect.ambient_occlusion": True,
        "render.grid.enable": False,
        "ui.axis": False,
        "ui.filename": False,
        "scene.up_direction": "+Z",
    })
    engine.window.size = (2400, 1600)
    engine.scene.add(step)
    camera = engine.window.camera
    camera.reset_to_bounds()
    camera.azimuth(azimuth)
    camera.elevation(elevation)
    camera.reset_to_bounds()
    engine.window.render_to_image().save(out)

    image = Image.open(out).convert("RGB")
    white = Image.new("RGB", image.size, (255, 255, 255))
    left, top, right, bottom = ImageChops.difference(image, white).point(lambda v: 255 if v > 8 else 0).getbbox()
    pad = 30
    image = image.crop((max(left - pad, 0), max(top - pad, 0), min(right + pad, image.width), min(bottom + pad, image.height)))
    image = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
    image.save(out, optimize=True)


if __name__ == "__main__":
    step, out, width, azimuth, elevation = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
    render(step, out, width, azimuth, elevation)
