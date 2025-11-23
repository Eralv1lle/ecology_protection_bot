import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')

async def create_report(user_id, username, first_name, photo_path, latitude, longitude, address, description, waste_type, danger_level, rating_points=10):
    async with aiohttp.ClientSession() as session:
        data = {
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'photo_path': photo_path,
            'latitude': latitude,
            'longitude': longitude,
            'address': address,
            'description': description,
            'waste_type': waste_type,
            'danger_level': danger_level,
            'rating_points': rating_points
        }
        
        async with session.post(f'{BACKEND_URL}/api/reports', json=data) as response:
            return await response.json()

async def get_user_stats(telegram_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{BACKEND_URL}/api/user/{telegram_id}/stats') as response:
            if response.status == 200:
                return await response.json()
            return None

async def get_reports(status=None, waste_type=None, danger_level=None):
    async with aiohttp.ClientSession() as session:
        params = {}
        if status:
            params['status'] = status
        if waste_type:
            params['waste_type'] = waste_type
        if danger_level:
            params['danger_level'] = danger_level
        
        async with session.get(f'{BACKEND_URL}/api/reports', params=params) as response:
            return await response.json()

async def update_report_status(report_id, status, changed_by, comment=None):
    async with aiohttp.ClientSession() as session:
        data = {
            'status': status,
            'changed_by': changed_by,
            'comment': comment
        }
        
        async with session.put(f'{BACKEND_URL}/api/reports/{report_id}', json=data) as response:
            return await response.json()

async def delete_report(report_id):
    async with aiohttp.ClientSession() as session:
        async with session.delete(f'{BACKEND_URL}/api/reports/{report_id}') as response:
            return await response.json()

async def get_coordinates_from_address(address):
    import os
    api_key = os.getenv('YANDEX_MAP_API_KEY')
    
    if not api_key:
        return None
    
    geocode_url = 'https://geocode-maps.yandex.ru/1.x/'
    
    params = {
        'apikey': api_key,
        'geocode': address,
        'format': 'json'
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(geocode_url, params=params) as response:
            if response.status != 200:
                return None
            
            data = await response.json()
            
            try:
                geo_object = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
                pos = geo_object['Point']['pos'].split()
                
                return {
                    'latitude': float(pos[1]),
                    'longitude': float(pos[0])
                }
            except:
                return None
