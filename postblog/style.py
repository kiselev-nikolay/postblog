import colorsys


def unhex(rgbhex):
    rgbhex = rgbhex.strip('#').strip()
    rgb = [int(rgbhex[i:i + 2], 16) / 255 for i in range(0, 5, 2)]
    return colorsys.rgb_to_hls(*rgb)


def color_gen(rgbhex, source_lightness, source_saturation, alpha):
    hue, lightness, saturation = unhex(rgbhex)
    hsl_channels = colorsys.hls_to_rgb(
        hue,
        lightness,
        saturation
    )
    rgb = [round(c * 255) for c in hsl_channels]
    return 'rgba({}, {}, {}, {})'.format(*rgb, alpha)