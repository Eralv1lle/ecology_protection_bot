from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import os

class ImageProcessor:
    @staticmethod
    def extract_geolocation(image_path):
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
            
            lat = ImageProcessor._convert_to_degrees(gps_info.get('GPSLatitude'))
            lon = ImageProcessor._convert_to_degrees(gps_info.get('GPSLongitude'))
            
            if gps_info.get('GPSLatitudeRef') == 'S':
                lat = -lat
            if gps_info.get('GPSLongitudeRef') == 'W':
                lon = -lon
            
            return {'latitude': lat, 'longitude': lon}
        except:
            return None
    
    @staticmethod
    def _convert_to_degrees(value):
        if not value:
            return None
        d, m, s = value
        return float(d) + float(m) / 60.0 + float(s) / 3600.0
    
    @staticmethod
    def save_image(file_data, filename):
        upload_dir = 'uploads'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        filepath = os.path.join(upload_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(file_data)
        
        return filepath

image_processor = ImageProcessor()
