from botzen.automation.io import IOPixel

pixel = IOPixel()
pixel.manually_pick()
print(pixel.is_active())
