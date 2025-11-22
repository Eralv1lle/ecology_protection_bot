from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def extract_gps_from_image(image_path):
    try:
        image = Image.open(image_path)
        exif_data = image.getexif()
        
        if not exif_data:
            return None
        
        gps_info = {}
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == 'GPSInfo':
                for gps_tag in value:
                    gps_tag_name = GPSTAGS.get(gps_tag, gps_tag)
                    gps_info[gps_tag_name] = value[gps_tag]
        
        if not gps_info:
            return None
        
        lat = convert_to_degrees(gps_info.get('GPSLatitude'))
        lon = convert_to_degrees(gps_info.get('GPSLongitude'))
        
        if gps_info.get('GPSLatitudeRef') == 'S':
            lat = -lat
        if gps_info.get('GPSLongitudeRef') == 'W':
            lon = -lon
        
        return {'latitude': lat, 'longitude': lon}
    except Exception as e:
        return None

def convert_to_degrees(value):
    if not value:
        return None
    d, m, s = value
    return float(d) + float(m) / 60.0 + float(s) / 3600.0
